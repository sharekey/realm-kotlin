# Building and testing the SDK

The SDK Gradle root is `packages/`. See [migration validation](kotlin-2.2.10-migration.md)
for executed checks; command examples elsewhere in this guide are not proof that a target passed.

## Prerequisites and the correct Gradle root

Use [Config.kt](../../buildSrc/src/main/kotlin/Config.kt) and the wrappers as the version authority.
The development build uses Kotlin 2.2.10, Gradle 8.14.3, JDK/JVM target 17, AGP 8.10.0,
R8 8.10.21, compile/target SDK 35, Build Tools 35.0.0 and NDK 27.0.12077973. Android minimum
SDK is 21. SWIG 4.2.0+, CMake 3.18.1+ and ccache must be on `PATH`; set `JAVA_HOME`,
`ANDROID_HOME` and `NDK_HOME`. Apple targets additionally need compatible Xcode/platform tools.
`buildSrc` uses Gradle's embedded Kotlin compiler; SDK/compiler-plugin sources use `Versions.kotlin`.

From the repository root, prepare the **pinned** Core revision:

```sh
git submodule status
git submodule update --init --recursive
```

Do not use `--remote`: `.gitmodules` contains a historical branch hint, but the committed gitlink is
the build input. SWIG and native compilation need Core's headers and build files. The Gradle plugin
no longer reads `dependencies.yml` during configuration; its only generated version constant is
`PLUGIN_VERSION`. This does not remove Core as a native build prerequisite.

Then enter the SDK build:

```sh
cd packages
./gradlew projects
./gradlew tasks --all
```

All following `./gradlew` commands assume `packages/` unless another directory is stated.
The task path is `:test-base:jvmTest`, **not** `:packages:test-base:jvmTest`. The root build handles
cross-project lint/release orchestration; it is not the Infomaniak root-build layout.

## Targeted tests

| Concern | Command from `packages/` | Notes |
| --- | --- | --- |
| Compiler generation and IR fixtures | `./gradlew :plugin-compiler:test` | Compilation and dependencies may still require native setup |
| SDK JVM behavior and model validation | `./gradlew :test-base:jvmTest` | Requires the host's native Realm library |
| One compiler regression group | `./gradlew :test-base:jvmTest --tests 'io.realm.kotlin.test.compiler.ModelDefinitionTests'` | Use the actual test class for the change |
| Android device/emulator behavior | `./gradlew :test-base:connectedAndroidTest` | Requires a suitable connected device and Android native binaries |
| macOS / iOS simulator tests | `./gradlew :test-base:macosTest :test-base:iosTest` | Host-specific aliases are configured on macOS |
| SDK Kotlin style and static analysis | `./gradlew ktlintCheck detekt` | Root-level equivalents cover SDK packages |

The module tests are intentionally separate from the SDK modules. Source locations:

- `test-base/src/commonTest`: shared behavior, migrations and notification tests;
- `test-base/src/jvmTest`: compiler validation and JVM-specific cases;
- `test-base/src/androidInstrumentedTest`: Android cases and a symlink to common tests;
- `test-base/src/nativeDarwinTest`: Darwin-specific tests;
- `cinterop/src/androidInstrumentedTest` and `nativeDarwinTest`: direct interop checks.

Preserve the Android/common symlink. Shared test dependencies must currently be mirrored into
`androidInstrumentedTest` as documented in [test-base's build script](../../packages/test-base/build.gradle.kts).

## Source tests versus published-artifact tests

By default, `includeSdkModules=true` and `includeTestModules=true`. `test-base` declares Maven
coordinates and substitutes included SDK projects, allowing source development.

To test the packaged SDK, first publish to the local **Test** repository, then exclude SDK projects:

```sh
./gradlew publishAllPublicationsToTestRepository
./gradlew -PincludeSdkModules=false :test-base:jvmTest :test-base:connectedAndroidTest
```

This can build many targets; use a host with the required native prerequisites. The default repository
is `packages/build/m2-buildrepo/`, configured by `testRepository` in
[`packages/gradle.properties`](../../packages/gradle.properties). Use unique development versions and
check resolved dependencies so Maven Central or a stale local publication cannot mask a bad build.

There is an additional trap: Android **unit** test runtime configurations substitute the JVM
artifacts and require those artifacts to have been published. Do not assume they see the latest
source changes; the build script explicitly warns about this. Device instrumentation tests exercise
a different native path.

## Native build and publication controls

| Property/task | Actual purpose |
| --- | --- |
| `realm.kotlin.buildRealmCore=false` | Suppresses selected native Core build work; does not provide missing headers/binaries |
| `realm.kotlin.copyNativeJvmLibs` | Copies prebuilt JVM libraries into the package; inputs must be built and traceable |
| `includeSdkModules` / `includeTestModules` | Controls SDK/test project inclusion |
| `publishCIPackages` + `realm.kotlin.targets` | Selects publication tasks, not a universal switch disabling target configuration |
| `realm.kotlin.mainHost` | Controls publication of multiplatform metadata in that workflow |
| `generatePluginArtifactMarker` | Enables marker publication for Gradle's `plugins {}` resolution |

Read the accepted target names in [packages/build.gradle.kts](../../packages/build.gradle.kts), rather
than relying only on stale property comments. Core builds can be expensive.

The default Gradle JVM-native builder supports macOS and Windows; its Linux branch throws. The
inherited GitHub workflow builds the Linux JNI library through separate CMake steps. Consequently,
Linux runtime support is not proof that the default local Linux Gradle source build works.

## Root static-analysis gates

From the repository root, `./gradlew ktlintCheck detekt` checks the SDK builds under `packages/`.
The KMM sample and benchmarks retain explicit `ktlintCheckExamplesKmmSample`,
`ktlintCheckBenchmarks`, `detektExamplesKmmSample` and `detektBenchmarks` tasks outside the default
SDK gate. The benchmark build has been migrated to Gradle 8.14.3/JVM 17; its assembly checks do not
establish clean benchmark lint results. The old KMM sample still needs migration.

Detekt 1.23.6 reports `NO-SOURCE` for the multiplatform SDK/test projects in the inherited setup.
The aggregate currently analyzes the JVM Gradle/compiler plugins only; ktlint scans SDK Kotlin
sources. A successful `detekt` aggregate must not be described as full runtime static analysis.

## Consumer integration and CI

`integration-tests/gradle/current` and the Gradle 8.3/8.5 fixtures are separate builds. They consume
published packages and verify plugin/application wiring. After local publication, enter the chosen
fixture and inspect/run its `assemble` task with its own wrapper and configured repository path.
Examples and benchmarks are consumers too; they are not included by SDK `test-base` tasks.
The Gradle 7.2/7.5 fixtures are retained as historical sources and removed from the CI matrix: Kotlin
2.2.10 requires Gradle 7.6.3 or newer. The active Gradle consumers use Sharekey coordinates and JDK 17. The Gradle 8.3/8.5 fixtures
retain AGP 8.1 and explicitly upgrade D8/R8 to 8.10.21 for Kotlin 2.2 bytecode.
The Realm Java interoperability example uses the current wrapper, AGP namespace configuration and
Realm Java 10.19.0 (the old 10.11.0 transformer does not support AGP 8). This example checks a separate
SDK interoperability contract; the mobile app does not acquire a Realm Java dependency.

The [benchmark build](../../benchmarks/README.md) also uses Gradle 8.14.3/JVM 17 and the staged SDK.
Its reusable CI job explicitly assembles the Android instrumentation APK and JMH JAR, in addition
to `assemble`; compiling benchmark artifacts does not measure performance.

The additional [Sharekey workflow](../../.github/workflows/sharekey.yml) runs static-analysis and
Gradle plugin validation for `community` pushes and pull requests. It reuses the workflow below and
does not replace the inherited matrix. These checks do not provide native-runtime or release coverage.

The inherited entry point is [`.github/workflows/pr.yml`](../../.github/workflows/pr.yml), with reusable
static-analysis/integration workflows. Its intended flow builds per-platform artifacts, assembles a
local Maven repository and runs tests against those artifacts. The migrated static-analysis jobs
explicitly select Temurin JDK 17 and CMake 3.22.1; the SDK-scoped root gates have passed in the
Sharekey workflows on GitHub. This does not establish that every inherited native job is configured.

The inherited PR matrix now pins Temurin 17, Ninja 1.12.1, SWIG 4.3.1 and NDK 27.0.12077973
in the repository. JNI/Android builds use CMake 3.22.1; Apple Kotlin/Native builds use CMake 3.31.6
for the current Xcode generator. Apple builds select Xcode 16.4 on macOS 15, and Windows JNI selects
Visual Studio 17 2022 on `windows-2022`. It does not require upstream `VERSION_*` repository variables.
The SWIG installer is shared with the mobile release workflow and verifies the source archive's
SHA-256. Intel macOS lanes use `macos-15-intel`; Android emulator consumers select API 35
`google_apis` explicitly. Android setup requests `platform-tools` explicitly because the action's
legacy default also requests the removed `tools` package. Package cache keys include the workflows
and SWIG installer so toolchain changes cannot reuse artifacts built with the previous configuration.

The inherited matrix is not the Sharekey release pipeline. Its broader native consumer coverage
must be verified by a successful run; selecting tool versions is not proof that those targets pass.
The mobile workflow separately tests API 25 clock compatibility, API 35 instrumentation and R8.
The API 25 clock/device check and the 16 KB arm64 check serve different purposes. Inspect credentials,
artifact paths and publish conditions before changing release behavior.
Markdown-only pull requests are ignored by its PR trigger; documentation checks need a separate path.

The commented `debugMinified` setup in `test-base` is not enabled by simply passing a property.
A normal release build is not proof that R8/obfuscation works. The minimal Android sample now has an
installable minified release variant that runs Realm assertions during startup; use the commands
and publication exclusions in the [migration record](kotlin-2.2.10-migration.md).

## Recording a result

Record SDK commit, Core SHA, toolchain versions, exact command, host/device and whether tests used
source substitutions or published artifacts. Preserve failures and exclusions. For new releases,
add mobile JS/Kotlin file interoperability, encryption, lifecycle and 16 KB validation described in
[fork maintenance](fork-maintenance.md).

For documentation-only changes, check links and run `git diff --check` from the repository root.
