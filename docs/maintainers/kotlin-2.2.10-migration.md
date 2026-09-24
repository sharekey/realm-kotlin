# Kotlin 2.2.10 migration

Work item: [M-3153](https://yt.sharekey.com/issue/M-3153).
Baseline: upstream community `28182c37`, Realm 3.0.0. Development artifact version:
`3.0.0-sharekey.1-SNAPSHOT`. Maven/API namespace remains `io.realm.kotlin`; no remote publication
is part of this migration.

## Toolchain

- Kotlin/compiler plugin: 2.2.10, matching the Sharekey mobile application's current Kotlin version.
- Gradle: 8.14.3, distribution SHA-256 pinned in the updated wrappers.
- JDK and JVM bytecode: 17; AGP 8.10.0; R8 8.10.21.
- Android: minimum API 21, compile/target API 35, Build Tools 35.0.0, NDK 27.0.12077973.
- Kotlin libraries: atomicfu 0.29.0, coroutines 1.10.2, serialization 1.9.0; test datetime 0.6.1
  and compile-testing 0.8.0. Dokka 2.0.0 retains its V1 task layout; Shadow 8.1.1 supports Gradle 8.

The [Kotlin compatibility table](https://kotlinlang.org/docs/gradle-configure-project.html)
covers the selected Gradle/AGP generation. [Android's Kotlin/R8 table](https://developer.android.com/build/kotlin-support)
requires R8 8.10.21 for Kotlin 2.2 metadata. Build-script Kotlin is kept separate from SDK Kotlin.
Android API 16–20 and JVM 8 consumers are outside this development version's support matrix.

Core remains **20.0.1**, gitlink `d8a68400288245c01be3dcb0ca3bcd4922fee680`.
No file-format or storage-engine migration is included.

## Initial migration validation

Host: macOS arm64, JDK 17. Commands run from `packages/` unless stated otherwise.

- Toolchain configuration: `./gradlew help` passed with all SDK and test projects included.
- `:plugin-compiler:test`: **5 passed**, with `-Xverify-ir=error`. IR fixtures were reviewed for
  the Kotlin 2.2 dump format: schema constants, fields and property declarations are preserved.
- `:test-base:jvmTest`: **988 tests, 0 failures/errors, 44 existing skips**. The shared models and
  dynamic compiler tests also enable `-Xverify-ir=error`. This includes the added named-companion
  regression: managed reads/writes and reopening an encrypted file with `Factory`/`CREATOR`.
- `:gradle-plugin:validatePlugins`, compiler `ktlintCheck`/`detekt`, and test-base `ktlintCheck` passed.
  The aggregate test-base `detekt` task reports `NO-SOURCE`; it is not additional test coverage.
- `:test-base:connectedDebugAndroidTest -Pandroid.injected.build.abi=arm64-v8a`: **941 test cases,
  0 failures/errors, 44 skips** in the XML report. Pixel 10 Pro emulator, Android 16/API 36,
  arm64, `getconf PAGE_SIZE` = **16384**. The console's final count includes skips again; the
  checked XML contains 941 `<testcase>` elements.
- Local `publishCIPackages` passed for JVM, Android, compiler plugins and the Gradle plugin,
  including multiplatform metadata and five Darwin cinterops. Generated version sources are included
  in the Android, JVM and common source JARs; all source-archive tasks explicitly depend on generation.
- Published-artifact CRUD checks in `integration-tests/gradle/current`: **1 JVM + 1 Android test
  passed**, no failures or skips. Gradle stored the configuration cache successfully.
- The Android AAR contains all four ABIs (`arm64-v8a`, `armeabi-v7a`, `x86`, `x86_64`). Every ELF
  `LOAD` segment in each `librealmc.so` has alignment **16384**. Runtime execution was on arm64 only.
- The minimal sample's debug APK, R8 release APK and shared JVM JAR build successfully. The final
  R8 APK passed its startup CRUD assertions on the same 16 KB emulator, displayed
  `Hello, Android 36!` and retained a live process with no crash. `zipalign -c -P 16 4` also passed.
- The same isolated sample passed a release build and startup CRUD check with the mobile app's
  consumer toolchain: **Gradle 9.4.1, AGP 9.2.1, R8 9.2.14, Kotlin 2.2.10**, using
  `android.builtInKotlin=false` and `android.newDsl=false`. APK 16 KB zip alignment passed too.
  This verifies SDK/plugin compatibility in a small consumer, not the full React Native app.
- Root `help` passed. Wrapper scripts and JARs were regenerated with Gradle 8.14.3 for the root,
  SDK, current integration fixture and minimal Android sample.

## Follow-up review (2026-09-24)

The FIR/IR changes and expected dumps were independently compared again: model field/property
counts, schema constants and managed/unmanaged accessor behavior remain consistent. No additional
compiler change was needed. The review made four focused improvements:

- Backport upstream `9cdc4556` to convert the pre-26 Android clock's milliseconds into epoch seconds
  and nanoseconds. Add an Android wall-clock regression. The app does not currently use
  `RealmInstant`; this repairs SDK behavior within its supported Android range.
- Remove unused JAXB (and its activation dependency), the Android compile dependency, SnakeYAML,
  Core-version generation and the unused Gradle-plugin logger. `PLUGIN_VERSION` and compiler
  artifact selection remain unchanged; Core is still needed for native builds.
- Scope default root lint gates to SDK packages. Legacy example/benchmark tasks remain explicitly
  available but unsupported. Pin JDK 17/CMake 3.22.1 in the corresponding static-analysis workflow.
- Add a synthetic encrypted Channel/User graph with embedded/linked objects, nullable binary and
  list fields, a participant query, managed updates and close/reopen. This covers patterns used by
  Sharekey, not Realm JS or concurrent shared-file access.

Checks on the reviewed changes (separate from the initial full-suite counts above):

- `:test-base:jvmTest` filtered to `SharekeyCompatibilityTests`, `NamedCompanionTests` and
  `RealmInstantTests`: **11 tests, 0 failures/errors/skips**.
- `:test-base:connectedDebugAndroidTest` filtered to `PlatformInfoTest`,
  `SharekeyCompatibilityTests` and `NamedCompanionTests`: **4 tests, 0 failures/errors/skips**,
  on the same API 36 arm64 / 16 KB emulator.
- The original clock bug reproduced with the pre-fix Android AAR in an isolated host-JVM probe.
  The rebuilt AAR passed with a stubbed `SDK_INT` of 21, 24, 25, 26 and 36. This exercises both
  clock branches but **does not constitute API 24/25 device coverage**; that device gate remains.
- Root `ktlintCheck detekt`, `:gradle-plugin:validatePlugins`, Android AAR assembly and local plugin
  publication passed. Multiplatform `detekt` tasks still report `NO-SOURCE`; only the JVM plugins
  receive detekt analysis in the inherited setup. The static-analysis workflow was not run on GitHub.
- Republished the fixed Android AAR and cleaned Gradle plugin to the local Maven repository, then
  ran `:multi-platform:jvmTest :single-platform:connectedDebugAndroidTest --refresh-dependencies`
  in `integration-tests/gradle/current`: **1 JVM + 1 Android test passed**, no failures/errors/skips.
  Both consumers recompiled, and Gradle stored the configuration cache. The plugin POM contains
  Kotlin stdlib only; no JAXB dependency remains.
- Local documentation links/anchors, workflow YAML syntax and `git diff --check` passed.

See [Sharekey integration](sharekey-integration.md) for the inspected mobile contract, retained SDK
components and the remaining app adoption checks. Core and the mobile dependency were not changed.

## Compiler adaptation

The FIR/IR API adaptation was compared with Infomaniak source
`6d2bf1582a23f2673933e33e09f8111bf8f4f8ab`, not its misleading `3.2.9` tag.
Kotlin 2.2 unifies receiver and regular argument slots. The changes update argument indices,
receiver parameters, constructor builders, FIR `coneType` and compiler opt-ins.
Fake overrides copy only value/context parameters before adding the receiver; a receiver must not
be copied as an extra regular argument. Persisted names retain strict string handling.
The original companion lookup and frozen-reference runtime behavior are preserved.

## Named companions under R8

The first minified sample launch failed with `NoSuchFieldException: Factory`. The inherited keep
rule matched only a field literally named `Companion` of type `**$Companion`. R8 renamed the named
companion field while Kotlin reflection still looked it up by its original name. The consumer rule
now keeps static nested-class fields on Realm models, covering `Companion`, `Factory`, `CREATOR`
and other names without changing runtime reflection or generated model APIs. The `Factory` sample
reproduced the failure before this change and passed after republishing the AAR and refreshing the
consumer dependency.

## Reproduce the packaged-consumer checks

After the source JVM/Android checks above have built the host JNI library, run from the repository
root with the prerequisites in [build and test](build-and-test.md):

```sh
./gradlew -p packages publishCIPackages \
  -Prealm.kotlin.targets=jvm,android,compilerPlugin,gradlePlugin \
  -Prealm.kotlin.buildRealmCore=false \
  -x :library-base:dokkaHtmlPartial
./gradlew -p integration-tests/gradle/current \
  :multi-platform:jvmTest :single-platform:connectedDebugAndroidTest
./gradlew -p examples/min-android-sample \
  :app:assembleDebug :app:assembleRelease :shared:jvmJar
```

This writes only to `packages/build/m2-buildrepo`. `buildRealmCore=false` reuses the already built
host JNI library; it does not fetch native binaries. The Android AAR's four native ABIs were built
from the pinned Core source. The local JVM JAR contains this host's macOS native library, not a
complete Windows/Linux release bundle. Skipping `dokkaHtmlPartial` avoids its dependencies on every
Apple platform binary; the resulting documentation JAR is not release-ready. This exclusion is
for local consumer verification, not a release command.

After republishing the same SNAPSHOT, add `--refresh-dependencies` to the consumer command. To run
R8 checks, use the **release** APK on the test emulator:

```sh
adb -e install -r examples/min-android-sample/app/build/outputs/apk/release/app-release.apk
adb -e shell am start -W -S -n io.realm.example.minandroidsample.android/.MainActivity
```

For the mobile toolchain check, run the same sample with a separately installed **Gradle 9.4.1**
(or the mobile repository's 9.4.1 wrapper), keeping the SDK build on its own 8.14.3 wrapper:

```sh
gradle -p examples/min-android-sample \
  -PandroidGradlePluginVersion=9.2.1 \
  -Pandroid.builtInKotlin=false -Pandroid.newDsl=false \
  :app:assembleRelease
```

Check `gradle --version` first for this command. The sample's default AGP remains 8.10.0. The
legacy AGP opt-outs match Sharekey's current setup; this is not AGP 10 support. The shared library
uses Kotlin's standard `androidMain` layout and leaves `targetSdk` to the application.

The sample uses a debug signing key solely to make its minified release APK installable. Its screen
initialization checks unmanaged/managed accessors, querying a committed object and deletion using
a named `Factory` companion. Seeing the greeting and a live activity after startup confirms those
checks finished. A successful `assembleRelease` alone does not check reflective companion lookup.

## Scope and remaining release gates

The migrated and validated scope is the SDK/compiler plus current Android/JVM consumers. This is
not a Kotlin 2.3 migration, an app dependency switch, or a remote SDK release. Apple C interop and
metadata compiled, but Apple executables/tests and Windows/Linux JNI were not validated here.
The historical versioned Gradle fixtures, Compose/KMM examples and benchmarks still have their
older wrappers and scripts while sharing the upgraded `buildSrc` dependencies. They are not a
working compatibility matrix and are excluded from default root lint gates. The inherited upstream
CI and publishing destinations require a separate Sharekey setup before a release.

Application adoption still needs shared encrypted-file tests with Realm JS, lifecycle/migration
checks against Sharekey data and the CI/release gates in [fork maintenance](fork-maintenance.md).

## Local Apple host constraints

The verification host runs macOS 27/Xcode 27 (AppleClang 21). Unchanged Core 20.0.1/S2 cannot build
against that SDK's C++ library. The local JVM JNI build used the installed macOS 26.5 SDK plus
compatibility flags, without changing the Core submodule or committing host paths:

```sh
cmake -S packages/cinterop/src/jvm -B packages/cinterop/build/realmMacOsBuild \
  -DCMAKE_OSX_SYSROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk \
  '-DCMAKE_CXX_FLAGS=-Wno-invalid-specialization -include cstdlib'
```

Run that command from the repository root after initial JVM CMake configuration on such a host.
The flags address S2's old `std::is_pod` specializations and Core's missing direct `<cstdlib>` include.
SWIG 4.3.1 and ccache 4.10.2 were built locally from official source archives because the installed
Homebrew did not recognize macOS 27. CMake 3.22.1 and NDK 27.0.12077973 came from the Android SDK.
The SDK 27 failure is not evidence of Kotlin compiler incompatibility; this does not claim general
support for Xcode 27 or verify iOS execution.
