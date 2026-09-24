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

## Validation log

Host: macOS arm64, JDK 17. Commands run from `packages/` unless stated otherwise.

- Toolchain configuration: `./gradlew help` passed with all SDK and test projects included.
- `:plugin-compiler:test`: **5 passed**, with `-Xverify-ir=error`. IR fixtures were reviewed for
  the Kotlin 2.2 dump format: schema constants, fields and property declarations are preserved.
- `:test-base:jvmTest`: **988 tests, 0 failures/errors, 44 existing skips**. The shared models and
  dynamic compiler tests also enable `-Xverify-ir=error`. This includes the added named-companion
  regression: managed reads/writes and reopening an encrypted file with `Factory`/`CREATOR`.
- `:gradle-plugin:validatePlugins`, compiler `ktlintCheck`/`detekt`, and test-base `ktlintCheck` passed.
  The aggregate test-base `detekt` task reports `NO-SOURCE`; it is not additional test coverage.
- Android and packaged-consumer verification are in progress.

## Compiler adaptation

The FIR/IR API adaptation was compared with Infomaniak source
`6d2bf1582a23f2673933e33e09f8111bf8f4f8ab`, not its misleading `3.2.9` tag.
Kotlin 2.2 unifies receiver and regular argument slots. The changes update argument indices,
receiver parameters, constructor builders, FIR `coneType` and compiler opt-ins.
Fake overrides copy only value/context parameters before adding the receiver; a receiver must not
be copied as an extra regular argument. Persisted names retain strict string handling.
The original companion lookup and frozen-reference runtime behavior are preserved.

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
