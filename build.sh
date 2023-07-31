#!/bin/bash
set -x
set -o errexit
set -o nounset
set -o pipefail

rm -rf out/
mkdir -p out/data/

echo "Cloning results-analysis.git/"
git clone --bare https://github.com/web-platform-tests/results-analysis.git

python3 scores.py --branch gh-pages --out-path out/data/ results-analysis.git
