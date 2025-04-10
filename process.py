#! /usr/bin/env python3
import subprocess
import re
import csv
import os
import argparse
import tempfile
import concurrent.futures
from typing import Tuple
import yaml

REVISION_REGEX = r"\d{4}-\d{2}-\d{2}\s+\((\d+)\)"
SNAP_NAME = "pc-kernel"


def get_current_revision() -> int:
    """
    Get the current revision of the kernel snap.
    """
    result = subprocess.run(
        ["snap", "info", SNAP_NAME], capture_output=True, text=True, check=True
    )

    revisions = []
    for line in result.stdout.split("\n"):
        match = re.search(REVISION_REGEX, line)
        if match:
            revisions.append(int(match.group(1)))
    return max(revisions)


def process_revision(revision: int) -> Tuple[str, str]:
    """
    Downloads the given revision of the snap and returns its kernel version.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Getting revision {revision}")
        subprocess.run(
            ["snap", "download", SNAP_NAME, "--revision", str(revision)],
            cwd=temp_dir,
            stdout=subprocess.DEVNULL,
            check=True,
        )

        subprocess.run(
            [
                "unsquashfs",
                f"{SNAP_NAME}_{revision}.snap",
                "meta/snap.yaml",
            ],
            cwd=temp_dir,
            stdout=subprocess.DEVNULL,
            check=True,
        )

        with open(
            os.path.join(temp_dir, "squashfs-root", "meta", "snap.yaml"), "r"
        ) as f:
            snap_yaml = yaml.safe_load(f)

    version = snap_yaml["version"]
    architecture = snap_yaml["architecture"][0]  # Each kernel has only one architecture
    print(f"Revision {revision} is version {version} for {architecture}")
    return version, architecture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=os.cpu_count())
    args = parser.parse_args()

    current_revision = get_current_revision()
    print(f"Current revision: {current_revision}")

    revisions = list(range(current_revision, 0, -1))
    print(f"Processing {len(revisions)} revisions with {args.workers} workers")

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_revision, rev): rev for rev in revisions}
        for future in concurrent.futures.as_completed(futures):
            try:
                version, architecture = future.result()
                rev = futures[future]
                results[rev] = (version, architecture)
            except Exception as e:
                print(f"Error processing revision {rev}: {e}")

    with open("results.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["revision", "version", "architecture"])
        for rev, (version, architecture) in sorted(results.items()):
            writer.writerow([rev, version, architecture])

    print("Done! Results saved to results.csv")


if __name__ == "__main__":
    main()
