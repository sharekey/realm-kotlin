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
have not been validated. The Android compiler plugin classpath also resolves `cinterop-jvm` and the JNI stub, so
JVM artifacts cannot simply be omitted from an Android publication. KMP root metadata advertises
all configured targets, so an Android-first release must
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
- The mobile app passed ARM64 debug APK assembly and releaseDev Kotlin compilation with
  Gradle 9.4.1/AGP 9.2.1. Its 32 runtime dependency graphs resolve the Sharekey candidate, preserving
  all other runtime lock entries. APK signatures and 16 KB ZIP alignment passed; its version string,
  single initializer and native-library hash match this candidate. No packaged app release or new
  device test is claimed for this step. Mobile details: `docs/realm-kotlin-local-testing.md`.
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
checks alone do not establish native-runtime/release coverage. All inherited build/test jobs remain
in place; only the two legacy deployment jobs are restricted to the upstream repository because
their destinations and credentials belong to Realm/MongoDB.

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

Before changing the app's default repository, verify the exact version can be resolved from a clean
consumer through the selected remote registry. Then remove its unconditional sibling-checkout path,
update both plugin/runtime coordinates and regenerate all Android dependency lockfiles. Keep local
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

The release workflow still needs implementation: a version tag (for example `v3.0.0-sharekey.1`)
selects the exact commit, initializes the pinned Core submodule, builds the declared platform set,
runs SDK/consumer tests, stages Maven artifacts with sources/documentation/metadata, signs them and
uploads through a Central Portal-compatible publisher. It must await `PUBLISHED` and verify an
anonymous consumer can resolve the release. Portal upload/status endpoints are documented in the
[Publisher API](https://central.sonatype.org/publish/publish-portal-api/). Published release bytes
cannot be replaced; corrections need a new version.

Before implementing the final upload, resolve the candidate packaging gaps described above: JVM
artifacts needed by the compiler, host JNI coverage, advertised KMP targets and documentation. A local
macOS build plus secrets is not yet a complete cross-platform release workflow. Neither new accounts,
secrets, remote publications nor changes to mobile's TeamCity pipeline were made by this guide.
