# ubuntu-core-kernel-versions

Find the version and architecture of all revisions of the Ubuntu Core kernel snap.

## Rationale

Unfortunately it's not possible to easily switch between kernel versions on Ubuntu Core and the information provided by `snap info pc-kernel` is not enough to match all versions to a revision of the snap. This is limiting our ability to test software against various kernel versions. This script solves this problem by downloading each revision of the snap and extracting the snap metadata to determine the version and architecture of the kernel.

## Usage

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./process.py [--workers N] [--snap SNAP_NAME] [--output OUTPUT_FILE] [--verbose]
```

All parameters are optional.

- `N` is the number of workers to use. Defaults to the number of cores on the machine.
- `SNAP_NAME` is the name of the snap to download and inspect. Defaults to `pc-kernel`.
- `OUTPUT_FILE` is the file to save the results to. Defaults to `results.csv`.
- `VERBOSE` is a flag to enable verbose logging.

## Results

The results are saved to `results.csv`. You can find the artifacts of the weekly workflow runs in the [Releases](https://github.com/pkulik0/ubuntu-core-kernel-versions/releases) section.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
