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
- Compiler adaptation and runtime verification are in progress; this configuration result is not
  a claim that the SDK or consuming application has passed its test suites.
