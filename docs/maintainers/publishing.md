# Publishing Sharekey Realm Kotlin

Tracking: [M-3153](https://yt.sharekey.com/issue/M-3153).

## Current status

The selected distribution is a GitHub Release tarball consumed by Yarn in the mobile app.
[`3.0.0-sharekey.1`](https://github.com/sharekey/realm-kotlin/releases/tag/v3.0.0-sharekey.1) is published;
its tagged build, Android tests and automatic upload all passed on 2026-09-24.
No Maven Central, GitHub Packages or npm registry account is required. The release job uses the
repository-scoped `GITHUB_TOKEN`; consumers download the public Release asset without credentials.
The maintainer accepted the preceding local snapshot and authorized adoption on 2026-09-24.

| Contract | Value |
| --- | --- |
| Maven group | `com.sharekey.realm.kotlin` |
| Gradle plugin ID | `com.sharekey.realm.kotlin` |
| Release version | `3.0.0-sharekey.1` |
| Public Kotlin packages / Android namespaces | `io.realm.kotlin` (unchanged) |
| Kotlin compiler | 2.2.10 |
| Core | 20.0.1 / `d8a68400288245c01be3dcb0ca3bcd4922fee680` |

Plugin/runtime coordinates, compiler artifact selection, Android unit-test JVM substitutions and
current consumer fixtures use the same group. `PLUGIN_GROUP` and `PLUGIN_VERSION` are generated
from Config.kt. The internal compiler plugin ID stays `io.realm.kotlin`; it is not a Maven coordinate.
AndroidX Startup 1.2.0 is declared by the SDK, matching the app's existing resolved version.

## Local candidate validation

Use the prerequisites in [build and test](build-and-test.md). With the host JNI build already present:

```sh
./gradlew -p packages :gradle-plugin:validatePlugins publishCIPackages \
  -Prealm.kotlin.targets=jvm,android,compilerPlugin,gradlePlugin -Prealm.kotlin.mainHost=true \
  -Prealm.kotlin.buildRealmCore=false \
  -x :library-base:dokkaHtmlPartial
./gradlew -p integration-tests/gradle/current \
  :multi-platform:jvmTest :single-platform:assembleDebug
```

The committed `packages/gradle.properties` sets `realm.kotlin.mainHost=true`; this adds the root
`cinterop`/`library-base` KMP metadata publications to `publishCIPackages`. The command repeats the
flag explicitly so a developer's Gradle user properties cannot disable the roots. The release
workflow uses that committed project setting on a clean runner; its successful tagged build logs
include both `publishKotlinMultiplatformPublicationToTestRepository` tasks.

Artifacts are staged under `packages/build/m2-buildrepo/com/sharekey/realm/kotlin/`.
The Gradle publisher configures only the local Test repository. It does not upload to Maven Central,
GitHub Packages, the Gradle Plugin Portal or upstream Realm infrastructure.

**This command is a local validation set, not a complete cross-platform release.** The current host
JVM JAR contains macOS JNI only; Linux/Windows native libraries and Kotlin Apple runtime publications
have not been validated. The Android compiler plugin classpath also resolves `cinterop-jvm` and the JNI stub, so
JVM artifacts cannot simply be omitted from an Android publication. KMP root metadata advertises
all configured targets, so an Android-first release must
explicitly settle its publication scope before upload. Do not upload this entire staging directory
and call it a complete KMP release. The excluded Dokka task also means the documentation artifact is
not release-ready. See the [migration evidence](kotlin-2.2.10-migration.md).

## Candidate checks (2026-09-24)

- `:gradle-plugin:validatePlugins` and local publication of ten modules passed, including
  `plugin-compiler-shaded`. The mobile tarball contains nine modules: the native-only shaded
  compiler publication is deliberately excluded.
- Every staged POM/module file uses Sharekey coordinates for SDK dependencies; no original Realm or
  Infomaniak SDK dependency remains. The Gradle plugin JAR contains the new plugin descriptor.
- The independent current fixture passed its JVM CRUD test (1 test, no failures/errors/skips), Android
  library assembly and instrumented-test APK assembly. Device execution was not repeated for this
  coordinate-only candidate; preceding snapshot device evidence is in the migration record.
- Minimal sample `:app:assembleRelease :shared:jvmJar` passed, including R8. This candidate APK was
  built, not installed or launched as part of this check.
- Root `ktlintCheck detekt` passed. KMP detekt tasks still report `NO-SOURCE` as documented.
- All four Android JNI ABIs are present. ARM64 `librealmc.so` SHA-256 is
  `86524a16def2467e7027872d46b5cf8e30064c70a178289bc6c9361b47950d13`, unchanged from the tested snapshot.
- The mobile app passed ARM64 debug APK assembly and releaseDev Kotlin compilation with
  Gradle 9.4.1/AGP 9.2.1. Its 32 runtime dependency graphs resolve the Sharekey candidate, preserving
  all other runtime lock entries. APK signatures and 16 KB ZIP alignment passed; its version string,
  single initializer and native-library hash match this candidate. No packaged app release or new
  device test is claimed for this step. Mobile details: `docs/realm-kotlin-local-testing.md`.
- Relative documentation file links, workflow YAML parsing and `git diff --check` passed.
  These were local candidate checks; the tagged release validation is recorded below.

## GitHub Release distribution

[Sharekey mobile release](../../.github/workflows/sharekey-release.yml) validates the migration branch
and releases tags matching `v*-sharekey.*`. Manual runs validate/package; publication requires a tag
whose value is exactly `v` plus `Realm.version`. Build/test jobs have read-only repository access;
only the release job has `contents: write`. The inherited build/test workflows remain in place; their Gradle 7.2/7.5 consumer lanes are
retired because Kotlin 2.2.10 requires Gradle 7.6.3 or newer.

The workflow uses macOS 15/Xcode 16.4, Temurin 17, Node 22.17.0, SWIG 4.3.1 (checksum pinned),
CMake 3.22.1 and Android NDK 27.0.12077973. It builds the macOS JNI library with a minimum deployment
target of 11.0 and both arm64/x86_64 slices; otherwise CMake can inherit the builder's much newer OS.
It compiles all four Android ABIs, runs compiler/JVM tests, packs the Maven repository and tests
independent consumers against the extracted tarball. Linux jobs run the published Android SDK's instrumentation tests on API 35 x86_64 and a focused
`PlatformInfoTest` on API 25, covering the pre-API-26 clock fallback. The API 35 job also builds the
minified Android sample against the extracted package, installs it, and checks the rendered greeting
that follows successful named-companion CRUD assertions. Static analysis must pass before publishing.

[build-mobile-release.sh](../../tools/build-mobile-release.sh) is the macOS build entry point.
[pack-mobile.py](../../tools/pack-mobile.py) verifies POM coordinates, SDK dependency closure,
Gradle metadata hashes, all four Android native libraries and 16 KB ELF segment alignment. Each
Android library must match its advertised ABI by ELF machine type and 32/64-bit class. Mislabeled
libraries and malformed or truncated ELF headers are rejected. The archive includes nine modules,
source JARs, original POM/module metadata, licenses, checksums and source/Core provenance.
Both the pre-build and packaging checks reject modified or untracked SDK/Core sources. Ignored
build output is allowed; CI keeps its compiler cache under `build/`.
[`test-mobile-package.sh`](../../tools/test-mobile-package.sh) extracts into a new temporary directory
and restores the staging repository on success, failure or interruption. Its failure/repeat-run
regressions run with `python3 -B -m unittest discover -s tools/tests -v`.
[`test-minified-android.sh`](../../tools/test-minified-android.sh) requires a connected emulator and the
packaged Maven repository at `packages/build/m2-buildrepo`; it fails if R8 mapping output or the
successful CRUD screen is absent. The emulator action executes inline commands with `sh`; keep
its conditionals POSIX-compatible and invoke the Bash helper explicitly. Each UI dump replaces its
previous output so a failed dump cannot reuse a successful screen from an earlier launch.
The npm package is `@sharekey/realm-kotlin`, marked private to prevent accidental registry publishing.
It contains no JavaScript entry point or installation scripts. npm is used only to make a tarball.

### Gradle plugin resolution

The archive contains the plugin implementation, not the optional Gradle Plugin Portal marker POM.
Load the implementation on the buildscript classpath, then apply its ID without a version. This is
how the mobile app and `integration-tests/gradle/current` resolve the plugin, including when the
integration fixture uses a `plugins {}` block in its subprojects. A standalone versioned plugin
request needs a marker publication and is not supported by this bundle.

```groovy
// Root build.gradle; replace the version/path to match the installed package.
buildscript {
    repositories {
        maven { url = uri("$rootDir/../node_modules/@sharekey/realm-kotlin/maven") }
        google()
        mavenCentral()
    }
    dependencies {
        classpath "com.sharekey.realm.kotlin:gradle-plugin:3.0.0-sharekey.1"
    }
}
// The module containing Realm models:
apply plugin: "com.sharekey.realm.kotlin"
```

The bundle includes the JVM modules needed by the compiler plugin and Android unit-test substitution.
Its native JVM runtime supports macOS only. Linux/Windows JVM runtime, Apple Kotlin/Native SDK
publications and the native-only shaded compiler distribution are outside this mobile bundle.
Root KMP metadata retains its original Apple variant declarations; do not consume those variants from
this archive. Source JARs are included; the excluded Dokka output is not a published documentation site.

Release procedure:

1. Update `Realm.version` in Config.kt for every release; never reuse a distributed version.
2. Commit the change on the maintained migration/community line and run its checks.
3. Push an annotated tag matching the version, for example `v3.0.0-sharekey.1`.
4. Wait for all jobs of **Sharekey mobile release** to succeed. The release contains
   `sharekey-realm-kotlin-<version>.tgz`, its `.sha256` and `provenance.json`.
5. In mobile, pin the exact `/releases/download/v<version>/...tgz` URL in `package.json`, run Yarn
   and regenerate Android dependency locks. Gradle reads the version from the installed package.
   Commit `package.json`, `yarn.lock` and the changed Gradle lockfiles together.
6. Verify a mobile build and the affected device flows. SDK CI does not test the app's authenticated
   JS/Kotlin file-sharing and storage lifecycle.

Ordinary mobile builds need only their existing Yarn install and Android toolchain. Gradle resolves
`com.sharekey.realm.kotlin` exclusively from the installed package's `maven/` directory, including the
buildscript plugin. A sibling checkout, `mavenLocal()` publication and registry credentials are not
part of this delivery path. The tag workflow publishes new releases without replacing existing ones.
Workflow artifacts are temporary job handoffs; the app's dependency URL always targets a Release asset.

## First published release (2026-09-24)

[Release v3.0.0-sharekey.1](https://github.com/sharekey/realm-kotlin/releases/tag/v3.0.0-sharekey.1)
was produced by [the tagged workflow](https://github.com/sharekey/realm-kotlin/actions/runs/36049141575)
from SDK commit `e013bf62f8aaeff3299f2d4cefb8d2b901095330` and Core
`d8a68400288245c01be3dcb0ca3bcd4922fee680`. The complete workflow succeeded, including publication.

- The 19.5 MB archive contains nine Maven modules and 53 package files. Its SHA-256 is
  `b664c0b48cf9366a33686aaff9aa188dde4b0ca9d89e575d2f6f42717c417a70`.
  Anonymous download matched the tested Actions artifact byte for byte; every internal checksum passed.
- Compiler tests: 5 tests, no failures/errors. JVM runtime: 989 tests, no failures/errors, 44 skipped.
  The independent packaged consumer passed its JVM CRUD test and Android APK assembly checks.
- Published Android SDK tests on API 35 x86_64: 943 tests, no failures/errors, 44 skipped.
  Both static-analysis jobs passed. Reports are attached to the workflow run.
- All four Android ABIs passed 16 KB ELF checks. The universal macOS JVM library has arm64/x86_64
  slices and a verified minimum OS of 11.0. Linux/Windows JVM and Apple Kotlin/Native publications
  remain outside this distribution.
- Mobile installed the public Release URL with immutable Yarn locks, then built an ARM64 debug APK
  and compiled releaseDev Kotlin using Gradle 9.4.1/AGP 9.2.1. APK signature and 16 KB ZIP alignment
  passed; it contains one
  RealmInitializer and the archive's ARM64 library, SHA-256
  `9975d8ecab7b397ba6c1957c700ed22f3c4a921579c2291265871c50f2ffb17c`.
  This step did not install the app or build a packaged release APK.

The public `.tgz` URL is the consumer dependency. The release uses neither registry credentials nor
SDK source compilation in mobile/TeamCity; preserve its assets and issue a new version for changes.

## Optional Maven registry publishing

A Maven registry is deferred. The comparison below is retained for a future public SDK distribution.

`-PsignBuild=true` enables Gradle signing. Provide the ASCII-armored private key as `REALM_SIGNING_KEY`
and its passphrase as `REALM_SIGNING_PASSWORD` in the environment or private Gradle user properties.
Use real newlines in the environment value. Do not pass secrets on a command line, put them in this
repository, or paste them into task messages. With signing disabled, local validation needs no key.
The old upstream key ID, Nexus profile, Nexus plugin and Sonatype credentials were removed.
`tools/publish_release.sh` fails immediately; the historical upstream snapshot/deploy tools are not
supported for Sharekey distribution. The additional `sharekey.yml` workflow runs static analysis
and plugin validation; it does not replace the inherited CI matrix or publish remotely. Those
checks alone do not establish native-runtime/release coverage. The inherited build/test jobs remain, with unsupported Gradle 7.2/7.5 consumer lanes retired.
The two legacy deployment jobs are restricted to the upstream repository because their destinations
and credentials belong to Realm/MongoDB.

Maven Central has the simplest consumer setup because downloads need no registry token. However,
its cost must be checked before choosing it. The [2026-09-08 publisher update](https://central.sonatype.org/news/20260908_publisher_tiers_commercial_use/)
says Publisher Pro is required from 2026-10-01 for commercial-nature artifacts, independently of
volume. Company maintenance alone does not establish that classification. Do not assume this fork
qualifies for free community publishing; confirm its treatment with Sonatype. Central also requires
a publisher account, verification of a Sharekey namespace and signing material. [Central requirements](https://central.sonatype.org/publish/requirements/) cover
POM metadata, sources, documentation, checksums and signatures;
[Portal publishing](https://central.sonatype.org/publish/publish-portal-api/) describes bundle upload.
No account or signing identity is created implicitly by this repository.

GitHub Packages is an alternative, but even public Maven downloads require authentication; see
[GitHub's Gradle registry instructions](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-gradle-registry).
That choice also requires provisioning read credentials for developers and TeamCity. A private Maven
registry needs its confirmed URL and the corresponding reader/publisher setup.

Before switching from the Release tarball to a Maven registry, verify the exact version can be resolved from a clean
consumer through the selected remote registry. Then replace the installed package repository,
keep plugin/runtime coordinates aligned and regenerate all Android dependency lockfiles. Keep local
SDK work behind an explicit opt-in override. Do not make CI depend on an unpublished remote version.

For a release, record the SDK commit/tag, Core SHA, artifact SHA-256 values, publication scope,
toolchain, executed tests and known limitations. Never replace the bytes of a remotely published
version; make a new version. Updating this Kotlin fork does not change Realm JS or RealmSwift.

## Registry choice and proposed CI setup (2026-09-24)

| Registry | Consumer setup | Publisher/maintenance tradeoff |
| --- | --- | --- |
| Maven Central | Existing `mavenCentral()`; anonymous public downloads | Namespace verification, PGP signatures and release requirements; confirm the applicable publisher tier |
| GitHub Packages | Explicit Maven URL and reader tokens, including TeamCity/developer machines | Convenient repository/Actions integration; public packages are free, private usage depends on plan/quotas |
| Existing company Maven registry | Company URL and its access policy | Good fit if already operated; a new server adds storage, backup, availability and access-management work |

Sources: [GitHub authentication](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-gradle-registry),
[GitHub package billing](https://docs.github.com/en/billing/concepts/product-billing/github-packages),
[hosted Maven repositories](https://help.sonatype.com/en/maven-repositories.html).
GitHub Actions can publish a package associated with its repository using `GITHUB_TOKEN`;
external consumers use suitable credentials, typically a classic PAT with `read:packages`.
Public repository visibility does not enable anonymous GitHub Maven downloads.

For an independently useful public SDK, Central is technically attractive if its publishing terms
are acceptable. GitHub Packages is a practical starting point for a team-only distribution workflow
when public packages and reader-token management are acceptable. Do not deploy a new repository
server just for this fork without an operational reason. This is a comparison, not a registry change.

If Central is selected, keep SDK publishing in the fork's GitHub Actions and mobile builds in TeamCity.
Central stores the resulting binaries; it does not run CI. TeamCity only downloads a fixed SDK version
and needs neither SDK sources nor publishing credentials for ordinary app builds.

One-time publisher setup:

1. Register in [Central Portal](https://central.sonatype.com/) and confirm the organization's publishing
   classification/plan. Use organizational access rather than making maintenance depend on one person.
2. Request namespace `com.sharekey`. Add the Portal-issued verification value as a DNS TXT record at
   `sharekey.com`, then verify the namespace. This covers group `com.sharekey.realm.kotlin`.
   [Namespace instructions](https://central.sonatype.org/register/namespace/).
3. Generate a Portal user token. Its generated username/password pair is separate from interactive
   account credentials. [Token instructions](https://central.sonatype.org/publish/generate-portal-token/).
4. Create a release PGP signing key, retain its backup and publish the public key to a supported
   keyserver. Keep the armored private key and passphrase in CI secrets.
   [Signing instructions](https://central.sonatype.org/publish/requirements/gpg/).
5. In `sharekey/realm-kotlin`, add the following repository or release-environment secrets through
   GitHub Settings. [GitHub secret setup](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).

| Proposed secret | Value |
| --- | --- |
| `CENTRAL_USERNAME` | Username from the Portal token |
| `CENTRAL_PASSWORD` | Password from the same Portal token |
| `REALM_SIGNING_KEY` | ASCII-armored private PGP signing key |
| `REALM_SIGNING_PASSWORD` | Signing-key passphrase |

The `REALM_SIGNING_*` environment variables are already read by the local Gradle publisher.
The `CENTRAL_*` names above are a proposed contract for the future uploader; no current workflow
reads them. Adding these secrets alone will not turn the existing checks into a release pipeline.

A Maven Central publication workflow would still need implementation: a version tag
selects the exact commit, initializes the pinned Core submodule, builds the declared platform set,
runs SDK/consumer tests, stages Maven artifacts with sources/documentation/metadata, signs them and
uploads through a Central Portal-compatible publisher. It must await `PUBLISHED` and verify an
anonymous consumer can resolve the release. Portal upload/status endpoints are documented in the
[Publisher API](https://central.sonatype.org/publish/publish-portal-api/). Published release bytes
cannot be replaced; corrections need a new version.

Before implementing the final upload, resolve the candidate packaging gaps described above: JVM
artifacts needed by the compiler, host JNI coverage, advertised KMP targets and documentation. A local
macOS build plus secrets is not yet a complete cross-platform release workflow. These optional
registry instructions do not provision accounts, secrets or Maven Central publications.
