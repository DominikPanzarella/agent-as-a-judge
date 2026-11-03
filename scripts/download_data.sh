#!/usr/bin/env bash
# Download the raw data used by the project into data/raw/ (not tracked by git).
#  - ClassEval (Du et al., 2023): FudanSELab/ClassEval, CC BY-NC 4.0
#  - benchmarks+ (Examining Benchmark Quality in Code Generation): Zenodo 10.5281/zenodo.21031875, CC BY 4.0
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p data/raw/classeval data/raw/benchmarks_plus

curl -fsSL -o data/raw/classeval/ClassEval_data.json \
  "https://raw.githubusercontent.com/FudanSELab/ClassEval/master/data/ClassEval_data.json"

curl -fsSL -o data/raw/benchmarks_plus/benchmarks+.zip \
  "https://zenodo.org/records/21031875/files/benchmarks+.zip?download=1"
unzip -oq data/raw/benchmarks_plus/benchmarks+.zip -d data/raw/benchmarks_plus
find data/raw -type l -delete

ls -la data/raw/classeval data/raw/benchmarks_plus/benchmarks+
