# Realm Kotlin benchmarks

This build contains Android microbenchmarks and JVM JMH benchmarks for the SDK. iOS and macOS
Kotlin/Native benchmarks are not implemented. The JVM benchmarks can run on a host whose native
Realm JNI library is present in the consumed SDK; the Sharekey mobile package provides macOS JNI.

## Build prerequisites and artifact checks

Use JDK 17, the checked-in Gradle 8.14.3 wrapper and Android SDK 35. The shared configuration selects
Kotlin 2.2.10 and AGP 8.10.0. Java and Kotlin sources target JVM 17.

By default, the build includes `../packages` as a source composite. To test published artifacts,
first stage the SDK in `packages/build/m2-buildrepo` using the
[maintainer publication commands](../docs/maintainers/publishing.md#local-candidate-validation).
Then, from this directory, run:

```sh
CI=true ./gradlew assemble :androidApp:assembleReleaseAndroidTest :jvmApp:jmhJar
```

Setting `CI` selects the staged Maven repository and disables source substitution. The reusable
integration workflow runs the same tasks. These checks compile the Android instrumentation APK
and JMH executable JAR; they do not execute benchmarks or establish performance results. Benchmark
lint tasks remain separate from the repository's default SDK static-analysis gates.

## Android

Android uses [Jetpack Microbenchmark](https://developer.android.com/topic/performance/benchmarking/microbenchmark-overview).
The benchmark test APK requires API 32 or newer. Use a physical device for useful performance
comparisons; the configuration permits emulators and unlocked devices for development, but their
measurements are not a stable performance baseline.

From this directory, with the staged SDK and a connected device:

```sh
CI=true ./gradlew :androidApp:connectedReleaseAndroidTest
```

The benchmark Gradle plugin pulls device results into `androidApp/build/outputs/`. Inspect the
connected-test additional-output directory for the benchmark JSON. See the Android documentation
for [benchmark results](https://developer.android.com/topic/performance/benchmarking/microbenchmark-write#benchmark-results)
and [profiling](https://developer.android.com/topic/performance/benchmarking/microbenchmark-profile).
Profiling is disabled in `androidApp/build.gradle.kts`; change the instrumentation runner arguments
when collecting traces deliberately.

## JVM

JVM benchmarks use [JMH](https://github.com/openjdk/jmh) and the
[JMH Gradle plugin](https://github.com/melix/jmh-gradle-plugin). Run from this directory:

```sh
CI=true ./gradlew :jvmApp:clean :jvmApp:jmh
```

To select benchmark classes, pass a regular expression:

```sh
CI=true ./gradlew :jvmApp:clean :jvmApp:jmh -Pjmh.include=".*BulkWrite.*"
```

Results are written to `jvmApp/build/reports/benchmarks.json`. The commands clean previous outputs
so Gradle cannot reuse an earlier result. For an incremental build, use `--rerun-tasks` when a new
measurement is required.

## Interpreting results

The example files under `benchmark-data/` are historical experimental runs. They are not a
performance baseline for the migrated SDK. Keep device, OS, JVM, thermal conditions and benchmark
parameters comparable, use repeated measurements and investigate regressions with profiles before
drawing conclusions. Building the benchmark artifacts is not evidence of unchanged performance.
