# pyright: strict
import argparse
import json
import urllib.request
from pathlib import Path
from typing import List, TypedDict

from terminaltables import SingleTable  # type: ignore

cache = Path(__file__).parent / "cache"


class License(TypedDict):
    name: str
    licenseId: str
    url: str
    osiApproved: bool
    detailsUrl: str


def get(url: str):
    return urllib.request.urlopen(url).read().decode("utf-8")


def getch_licenses() -> List[License]:
    licenses_path = Path(__file__).parent / "licenses.json"
    if licenses_path.exists():
        with licenses_path.open() as f:
            return json.load(f)["licenses"]

    print("Downloading license list")
    data = json.loads(
        get(
            "https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json"
        )
    )
    with licenses_path.open("w") as f:
        json.dump(data, f)
    return data["licenses"]


def getch_license(license: License, force: bool) -> str:
    if not cache.exists():
        cache.mkdir()
    if (cache / license["licenseId"]).exists() and not force:
        with (cache / license["licenseId"]).open() as f:
            print(f"Using cached license for {license['name']}")
            return f.read()

    print(f"Downloading license for {license['name']}")

    data = json.loads(get(license["detailsUrl"]))
    with (cache / license["licenseId"]).open("w") as f:
        f.write(data["licenseText"])
    return data["licenseText"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--spdx", action="store_true", help="Use SPDX license identifiers"
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Do not use cached licenses"
    )
    parser.add_argument("name", help="Name of the license")
    args = parser.parse_args()

    licenses = getch_licenses()
    results: List[License] = []
    if args.spdx:
        results = [l for l in licenses if args.name.lower() in l["licenseId"].lower()]
    else:
        results = [l for l in licenses if args.name.lower() in l["name"].lower()]

    table = [["Id", "Name", "SPDX-Identifier"]]
    for idx, result in enumerate(results):
        idx += 1
        if args.spdx:
            ident = (
                result["licenseId"]
                .replace(args.name, f"\033[31m{args.name}\033[0m")
                .replace(args.name.lower(), f"\033[31m{args.name.lower()}\033[0m")
            )
            table.append([str(idx), result["name"], ident])
        else:
            name = (
                result["name"]
                .replace(args.name, f"\033[31m{args.name}\033[0m")
                .replace(args.name.lower(), f"\033[31m{args.name.lower()}\033[0m")
            )
            table.append([str(idx), name, result["licenseId"]])
    print(SingleTable(table).table)  # type: ignore

    which = input("Which license do you want to use? ")
    assert which.isdigit(), "Please enter a number"
    assert int(which) <= len(results) and int(which) > 0, "Please enter a valid number"

    text = getch_license(results[int(which) - 1], args.no_cache)

    with open("LICENSE", "w") as f:
        f.write(text)


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f'\033[31m{" ".join(e.args)}\033[0m')
