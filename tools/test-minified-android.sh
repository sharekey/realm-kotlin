#!/usr/bin/env bash
# Run the named-companion CRUD assertions from a genuinely minified APK.
set -euo pipefail
cd "$(dirname "$0")/.."
./gradlew -p examples/min-android-sample :app:assembleRelease --no-daemon --stacktrace

app=io.realm.example.minandroidsample.android
apk=examples/min-android-sample/app/build/outputs/apk/release/app-release.apk
# An assembly that silently bypassed R8 is not an adequate regression check.
test -s examples/min-android-sample/app/build/outputs/mapping/release/mapping.txt
adb install -r "$apk"
adb shell am start -W -S -n "$app/.MainActivity"
api="$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
mkdir -p build/mobile-package
hierarchy="$(mktemp "$PWD/build/mobile-package/minified-ui.XXXXXX")"
trap 'rm -f "$hierarchy"' EXIT

# Greeting is assigned only after Platform's managed CRUD assertions complete.
# Check the rendered result as am start alone may report success before a crash.
for attempt in {1..15}; do
  if adb shell uiautomator dump /sdcard/realm-minified-check.xml >/dev/null 2>&1 &&
     adb exec-out cat /sdcard/realm-minified-check.xml > "$hierarchy" &&
     python3 - "$hierarchy" "$app" "$api" <<'PY'
import sys
import xml.etree.ElementTree as ET
try:
    nodes = ET.parse(sys.argv[1]).iter("node")
    passed = any(
        node.get("resource-id") == sys.argv[2] + ":id/text"
        and node.get("text") == "Hello, Android " + sys.argv[3] + "!"
        for node in nodes
    )
except (OSError, ET.ParseError):
    passed = False
sys.exit(0 if passed else 1)
PY
  then
    echo "Minified named-companion CRUD passed on API $api"
    exit 0
  fi
  sleep 1
done
adb logcat -d -s AndroidRuntime >&2
echo "The minified sample did not complete its Realm CRUD assertions" >&2
exit 1
