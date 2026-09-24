# Contributing to Sharekey Realm Kotlin

Start with the [maintainer guide](docs/maintainers/README.md) and [AGENTS.md](AGENTS.md).
This fork maintains the local-database SDK from upstream `community`; the current release is
[`3.0.0-sharekey.1`](https://github.com/sharekey/realm-kotlin/releases/tag/v3.0.0-sharekey.1).
The mobile app installs its Maven repository from the GitHub Release tarball with Yarn. See
[publishing](docs/maintainers/publishing.md) for local staging and release commands.

## Contribution policy

The upstream MongoDB CLA form and `help@realm.io` address are not a contribution process established
for this Sharekey fork. Follow the contribution requirements agreed with Sharekey maintainers.
Preserve upstream copyright and license notices when adapting existing code.

## Obtaining the source

```sh
git clone --branch community --recurse-submodules https://github.com/sharekey/realm-kotlin.git
cd realm-kotlin
```

For an existing checkout, initialize Core at the committed revision:

```sh
git submodule update --init --recursive
```

Preserve tracked symlinks, including shared `buildSrc` directories and Android/common test sources.
Do not use `git submodule update --remote` for a normal build.

## Branch strategy

Base maintenance work on `community`. The `main` branch retains Atlas Sync code and is not the
baseline for this local-only SDK. Review individual upstream fixes before backporting them; do not
merge `main` wholesale into `community`. Keep changes focused and retain their source provenance.
See [fork maintenance](docs/maintainers/fork-maintenance.md) for publication and adoption gates.

## Building and testing

The SDK Gradle root is `packages/`. Read [build and test](docs/maintainers/build-and-test.md) for the
required JDK, Android SDK/NDK, SWIG, CMake, ccache and platform tools before running Gradle. The
[Kotlin 2.2.10 migration record](docs/maintainers/kotlin-2.2.10-migration.md) records the combinations
actually tested, including local Apple-host constraints. Select the same supported JDK in your IDE.

Run the narrowest relevant check from `packages/`, for example:

```sh
cd packages
./gradlew :plugin-compiler:test
./gradlew :test-base:jvmTest
./gradlew :test-base:connectedDebugAndroidTest
```

JVM tests require a native host library; Android tests require native binaries and a connected
device/emulator. macOS/iOS tests need a compatible Apple host and tools. Consult the build guide
for the Windows and Linux source-build limitations instead of assuming every task runs on every host.
Report exactly which commands, targets and devices passed, and record failures or exclusions.

## Testing published artifacts

Source tests normally substitute included SDK projects for their Maven dependencies. Published-artifact
checks instead consume packages from `packages/build/m2-buildrepo`. Follow the
[packaged-consumer reproduction commands](docs/maintainers/kotlin-2.2.10-migration.md#reproduce-the-packaged-consumer-checks)
for the current JVM/Android scope, including the local publication exclusions.

The current integration fixture is `integration-tests/gradle/current`. After publishing the required
artifacts, run from the repository root:

```sh
./gradlew -p integration-tests/gradle/current \
  :multi-platform:jvmTest :single-platform:connectedDebugAndroidTest
```

The minimal Android sample also checks generated models and consumer ProGuard rules in an
installable minified release APK. Historical fixtures, KMM examples and benchmarks need separate
compatibility work; their older wrappers do not establish support for the migrated SDK.

Release publication uses the Sharekey workflow and an immutable version tag. Inspect
publishing destinations before invoking release tasks; the inherited scripts target upstream services.

## Code style and dependency versions

Follow the surrounding Kotlin style, explicit public API declarations and existing ktlint/detekt rules.
Avoid wildcard imports. From `packages/`, run the relevant module checks, for example:

```sh
./gradlew :plugin-compiler:ktlintCheck :plugin-compiler:detekt
```

Repository-root `ktlintCheck`, `ktlintFormat` and `detekt` cover SDK packages. Explicit tasks for
legacy examples/benchmarks remain available, but are outside the default gates until migrated.
See the [build guide](docs/maintainers/build-and-test.md) for exact coverage and CI limitations.

Shared dependency versions live in [Config.kt](buildSrc/src/main/kotlin/Config.kt). Update the owning
build scripts and maintainer documentation together when changing a supported combination.

## Source and test layout

See the [repository map](docs/maintainers/repository-map.md) for the full source hierarchy. In
`library-base`, `commonMain` holds shared behavior; the intermediate `jvm` source set feeds Android
and desktop JVM, while `nativeDarwin` feeds the macOS and iOS targets.

| Path | Tests |
| --- | --- |
| `packages/test-base/src/commonTest` | Shared runtime behavior, migrations and notifications |
| `packages/test-base/src/jvmTest` | Compiler validation and JVM-specific behavior |
| `packages/test-base/src/androidInstrumentedTest` | Android cases and the symlink to shared tests |
| `packages/test-base/src/nativeDarwinTest` | Darwin-specific behavior |
| `packages/plugin-compiler/src/test` | Compiler generation and reviewed IR fixtures |

Keep common tests platform-independent and preserve the Android/common symlink. Shared test dependencies
currently need to be mirrored into `androidInstrumentedTest`; the test-base build script documents
that wiring. Edit maintained sources and expected fixtures, not generated outputs.
