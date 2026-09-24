#!/usr/bin/env bash
# Keep required Android gates in one fail-fast shell, independent of the action's line parser.
set -euo pipefail
cd "$(dirname "$0")/.."

gradle_arguments=(
  -p packages :test-base:connectedAndroidTest
  -PincludeSdkModules=false -Prealm.kotlin.buildRealmCore=false
  --no-daemon --stacktrace
)
case "${1:-}" in
  25) gradle_arguments+=(-Pandroid.testInstrumentationRunnerArguments.class=io.realm.kotlin.test.android.PlatformInfoTest) ;;
  35) ;;
  *) echo "Expected emulator API 25 or 35" >&2; exit 2 ;;
esac

./gradlew "${gradle_arguments[@]}"

if [[ "$1" == 35 ]]; then
  bash tools/test-minified-android.sh
fi
