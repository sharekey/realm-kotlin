#!/usr/bin/env bash
# Exercise only the Maven files from one archive, then restore the staging repository.
set -euo pipefail
cd "$(dirname "$0")/.."
archive="${1:?Usage: test-mobile-package.sh PATH_TO_ARCHIVE.tgz}"
staging="$PWD/packages/build/m2-buildrepo"
if [[ ! -d "$staging" || -L "$staging" ]]; then
  echo "Expected a real staging repository directory: $staging" >&2
  exit 1
fi
mkdir -p build/mobile-package
workspace="$(mktemp -d "$PWD/build/mobile-package/consumer-check.XXXXXX")"
backup="$workspace/staged-maven"
packaged="$workspace/package/maven"
restore_repository() {
  result=$?
  trap - EXIT
  if [[ -d "$backup" ]]; then
    if [[ -L "$staging" && "$(readlink "$staging")" == "$packaged" ]]; then
      rm "$staging" || exit 1
    fi
    if [[ -e "$staging" || -L "$staging" ]]; then
      echo "Cannot restore staging over an unexpected path; backup retained at $backup" >&2
      exit 1
    fi
    mv "$backup" "$staging" || exit 1
  fi
  rm -rf "$workspace"
  exit "$result"
}
trap restore_repository EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

tar -xzf "$archive" -C "$workspace"
(cd "$workspace/package" && shasum -a 256 -c SHA256SUMS)
[[ -d "$packaged" ]]
mv "$staging" "$backup"
ln -s "$packaged" "$staging"
./gradlew -p integration-tests/gradle/current \
  :multi-platform:jvmTest :single-platform:assembleDebug :single-platform:assembleDebugAndroidTest \
  --no-daemon --stacktrace
