# Publishing Sharekey Realm Kotlin

Tracking: [M-3153](https://yt.sharekey.com/issue/M-3153).

## Current status

`3.0.0-sharekey.1` is an **unpublished candidate**, not a downloadable Maven Central release.
The mobile maintainer tested the preceding local snapshot successfully and authorized adoption on
2026-09-24. The first release must still be staged and distributed through an agreed Maven registry.
No registry credentials or publication variables were configured in the GitHub repository at inspection.

| Contract | Value |
| --- | --- |
| Maven group | `com.sharekey.realm.kotlin` |
| Gradle plugin ID | `com.sharekey.realm.kotlin` |
| Candidate version | `3.0.0-sharekey.1` |
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
  -Prealm.kotlin.targets=jvm,android,compilerPlugin,gradlePlugin \
  -Prealm.kotlin.buildRealmCore=false \
  -x :library-base:dokkaHtmlPartial
./gradlew -p integration-tests/gradle/current \
  :multi-platform:jvmTest :single-platform:assembleDebug
```

Artifacts are staged under `packages/build/m2-buildrepo/com/sharekey/realm/kotlin/`.
The Gradle publisher configures only the local Test repository. It does not upload to Maven Central,
GitHub Packages, the Gradle Plugin Portal or upstream Realm infrastructure.

**This command is a local validation set, not a complete cross-platform release.** The current host
JVM JAR contains macOS JNI only; Linux/Windows native libraries and Kotlin Apple runtime publications
have not been validated. KMP root metadata advertises those targets, so an Android-first release must
explicitly settle its publication scope before upload. Do not upload this entire staging directory
and call it a complete KMP release. The excluded Dokka task also means the documentation artifact is
not release-ready. See the [migration evidence](kotlin-2.2.10-migration.md).

## Candidate checks (2026-09-24)

- `:gradle-plugin:validatePlugins` and local publication of all ten modules in the command above passed.
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
- Relative documentation file links, workflow YAML parsing and `git diff --check` passed.
  Remote CI, signing, registry upload and a clean remote consumer remain unverified.

## Signing and remote distribution

`-PsignBuild=true` enables Gradle signing. Provide the ASCII-armored private key as `REALM_SIGNING_KEY`
and its passphrase as `REALM_SIGNING_PASSWORD` in the environment or private Gradle user properties.
Use real newlines in the environment value. Do not pass secrets on a command line, put them in this
repository, or paste them into task messages. With signing disabled, local validation needs no key.
The old upstream key ID, Nexus profile, Nexus plugin and Sonatype credentials were removed.
`tools/publish_release.sh` fails immediately; the historical upstream snapshot/deploy tools are not
supported for Sharekey distribution. The additional `sharekey.yml` workflow runs static analysis
and plugin validation; it does not replace the inherited CI matrix or publish remotely. Those
checks alone do not establish native-runtime/release coverage.

For this public fork, Maven Central is the preferred destination because consumers need no registry
token. It requires a Central Portal publisher account, verification of a Sharekey namespace and
signing material. [Central requirements](https://central.sonatype.org/publish/requirements/) cover
POM metadata, sources, documentation, checksums and signatures;
[Portal publishing](https://central.sonatype.org/publish/publish-portal-api/) describes bundle upload.
No account or signing identity is created implicitly by this repository.

GitHub Packages is an alternative, but even public Maven downloads require authentication; see
[GitHub's Gradle registry instructions](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-gradle-registry).
That choice also requires provisioning read credentials for developers and TeamCity. A private Maven
registry needs its confirmed URL and the corresponding reader/publisher setup.

Before changing the app's default repository, verify the exact version can be resolved from a clean
consumer through the selected remote registry. Then remove its unconditional sibling-checkout path,
update both plugin/runtime coordinates and regenerate all Android dependency lockfiles. Keep local
SDK work behind an explicit opt-in override. Do not make CI depend on an unpublished remote version.

For a release, record the SDK commit/tag, Core SHA, artifact SHA-256 values, publication scope,
toolchain, executed tests and known limitations. Never replace the bytes of a remotely published
version; make a new version. Updating this Kotlin fork does not change Realm JS or RealmSwift.
