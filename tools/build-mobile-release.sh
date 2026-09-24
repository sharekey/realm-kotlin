#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
: "${JAVA_HOME:?Set JAVA_HOME to JDK 17}"
: "${ANDROID_HOME:?Set ANDROID_HOME to the Android SDK}"
export NDK_HOME="$ANDROID_HOME/ndk/27.0.12077973"
export PATH="$ANDROID_HOME/cmake/3.22.1/bin:$PATH"

# Generate the same SWIG Java/JNI stubs for both Android and the JVM library.
./gradlew -p packages :jni-swig-stub:assemble :gradle-plugin:validatePlugins \
  :gradle-plugin:publishAllPublicationsToTestRepository \
  -PincludeTestModules=false -Prealm.kotlin.buildRealmCore=false --no-daemon --stacktrace

# Pin the minimum OS: otherwise CMake inherits the runner's SDK/OS version.
cmake -S packages/cinterop/src/jvm -B packages/cinterop/build/realmMacOsBuild \
  -DCMAKE_BUILD_TYPE=Release -DREALM_NO_TESTS=1 -DREALM_BUILD_LIB_ONLY=true \
  -DREALM_CORE_SUBMODULE_BUILD=true -DCMAKE_CXX_VISIBILITY_PRESET=hidden \
  -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
  '-DCMAKE_OSX_ARCHITECTURES=x86_64;arm64' -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 \
  '-DCMAKE_CXX_FLAGS=-include cstdlib'
cmake --build packages/cinterop/build/realmMacOsBuild --parallel 3
lipo -archs packages/cinterop/build/realmMacOsBuild/librealmc.dylib | \
  python3 -c 'import sys; assert set(sys.stdin.read().split()) == {"x86_64", "arm64"}'

# Android's externalNativeBuild still builds all four ABIs. buildRealmCore=false
# skips unrelated Apple native SDK builds and reuses the JVM library built above.
./gradlew -p packages publishCIPackages \
  -PincludeTestModules=false -Prealm.kotlin.targets=jvm,android,compilerPlugin,gradlePlugin \
  -Prealm.kotlin.buildRealmCore=false -Prealm.kotlin.copyNativeJvmLibs=macos \
  -x :library-base:dokkaHtmlPartial --no-daemon --stacktrace
./gradlew -p packages :plugin-compiler:test :test-base:jvmTest \
  -Prealm.kotlin.buildRealmCore=false --no-daemon --stacktrace
python3 tools/pack-mobile.py

# Make the independent consumers resolve the contents of the final archive.
# Only generated staging directories are moved; published bytes are not edited.
mkdir -p build/mobile-package/unpacked
tar -xzf "build/mobile-package/sharekey-realm-kotlin-$(python3 tools/pack-mobile.py --version).tgz" \
  -C build/mobile-package/unpacked
(cd build/mobile-package/unpacked/package && shasum -a 256 -c SHA256SUMS)
mv packages/build/m2-buildrepo packages/build/m2-before-package-check
ln -s "$PWD/build/mobile-package/unpacked/package/maven" packages/build/m2-buildrepo
./gradlew -p integration-tests/gradle/current \
  :multi-platform:jvmTest :single-platform:assembleDebug :single-platform:assembleDebugAndroidTest \
  --no-daemon --stacktrace
