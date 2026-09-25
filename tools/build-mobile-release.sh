#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
: "${JAVA_HOME:?Set JAVA_HOME to JDK 17}"
: "${ANDROID_HOME:?Set ANDROID_HOME to the Android SDK}"
export NDK_HOME="$ANDROID_HOME/ndk/27.0.12077973"
export PATH="$ANDROID_HOME/cmake/3.22.1/bin:$PATH"

python3 tools/pack-mobile.py --check-source

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

# Test the final archive without retaining a temporary repository in the checkout.
bash tools/test-mobile-package.sh "build/mobile-package/sharekey-realm-kotlin-$(python3 tools/pack-mobile.py --version).tgz"
