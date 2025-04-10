#! /usr/bin/env python3
import argparse
import concurrent.futures
import csv
import logging
import os
import re
import subprocess
import tempfile
from typing import Tuple

import yaml

REVISION_REGEX = r"\d{4}-\d{2}-\d{2}\s+\((\d+)\)"


def get_current_revision(snap_name: str) -> int:
    """
    Get the current revision of the kernel snap.
    """
    result = subprocess.run(
        ["snap", "info", snap_name], capture_output=True, text=True, check=True
    )

    revisions = []
    for line in result.stdout.split("\n"):
        match = re.search(REVISION_REGEX, line)
        if match:
            revisions.append(int(match.group(1)))
    return max(revisions)


def process_revision(snap_name: str, revision: int) -> Tuple[str, str]:
    """
    Downloads the given revision of the snap and returns its kernel version and architecture.
    """
    logging.info(f"Processing revision {revision}")
    with tempfile.TemporaryDirectory() as temp_dir:
        logging.debug(f"Getting revision {revision}")
        subprocess.run(
            ["snap", "download", snap_name, "--revision", str(revision)],
            cwd=temp_dir,
            stdout=subprocess.DEVNULL,
            check=True,
        )

        logging.debug(f"Extracting meta/snap.yaml from {snap_name}_{revision}.snap")
        subprocess.run(
            [
                "unsquashfs",
                f"{snap_name}_{revision}.snap",
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
    # Each revision supports only one architecture
    architecture = snap_yaml["architectures"][0]
    logging.debug(f"Revision {revision} is version {version} for {architecture}")
    return version, architecture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=os.cpu_count())
    parser.add_argument("--snap", type=str, default="pc-kernel")
    parser.add_argument("--output", type=str, default="results.csv")
    parser.add_argument("--verbose", type=bool, default=False)
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    current_revision = get_current_revision(args.snap)
    logging.info(f"Current revision: {current_revision}")

    revisions = list(range(current_revision, 0, -1))
    logging.info(f"Processing {len(revisions)} revisions with {args.workers} workers")

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_revision, args.snap, rev): rev for rev in revisions
        }
        for future in concurrent.futures.as_completed(futures):
            rev = futures[future]
            try:
                version, architecture = future.result()
                results[rev] = (version, architecture)
            except Exception as e:
                logging.error(f"Error processing revision {rev}: {e}")

    with open(args.output, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["revision", "version", "architecture"])
        for rev, (version, architecture) in sorted(results.items()):
            writer.writerow([rev, version, architecture])
    logging.info(f"Done! Results saved to {args.output}")


if __name__ == "__main__":
    main()
