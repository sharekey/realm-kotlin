#!/usr/bin/env bash
set -euo pipefail

: "${RUNNER_TEMP:?GitHub Actions temporary directory is required}"
: "${GITHUB_PATH:?GitHub Actions path file is required}"

curl --fail --location --retry 3 \
  https://downloads.sourceforge.net/project/swig/swig/swig-4.3.1/swig-4.3.1.tar.gz \
  -o "$RUNNER_TEMP/swig.tar.gz"
echo "44fc829f70f1e17d635a2b4d69acab38896699ecc24aa023e516e0eabbec61b8  $RUNNER_TEMP/swig.tar.gz" | shasum -a 256 -c -
tar -xzf "$RUNNER_TEMP/swig.tar.gz" -C "$RUNNER_TEMP"
cd "$RUNNER_TEMP/swig-4.3.1"
./configure --prefix="$RUNNER_TEMP/realm-tools" --without-pcre --without-alllang
make -j3
make install
echo "$RUNNER_TEMP/realm-tools/bin" >> "$GITHUB_PATH"
