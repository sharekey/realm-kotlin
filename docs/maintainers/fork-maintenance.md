# Maintaining the Sharekey fork

Tracking task: [M-3153 — Maintain a Sharekey Realm Kotlin fork with reproducible builds](https://yt.sharekey.com/issue/M-3153).
This guide records the inspected baseline and planned adoption work. A planned release gate is not
a statement that the fork already passes it.

## Branch choice

Use **`community`** as the base for Sharekey's local-database SDK. The inspected history contains:

| Commit | Meaning |
| --- | --- |
| `49d81c21` | Removes the Kotlin Atlas Sync surface |
| `12514f3a` | Official 3.0.0 release |
| `28182c37` | Adds archived consumer documentation; current community source baseline |

`main` is a divergent history retaining `library-sync` and related APIs. It is not a more complete
version of the desired local-only SDK. Its Android pre-26 `currentTime()` fix at `9cdc4556` was
backported during the migration review, preserving millisecond precision. This is an example of
selective backporting without merging the Sync history.

The GitHub default branch is `community`, verified on 2026-09-24. The local symbolic
`origin/HEAD` pointed to `origin/main` at initial inspection and can remain stale; it does not select
the checked-out branch. No GitHub default-branch setting was changed by this work.

Develop focused changes from `community` and retain original upstream commit provenance. An
`upstream` remote for `realm/realm-kotlin` and an explicitly named Infomaniak reference remote may be
useful when importing patches. Neither was configured by this documentation pass.

## Three baselines that must not be confused

| Source | Role |
| --- | --- |
| Sharekey development checkout | Community 3.0.0 baseline adapted to Kotlin 2.2.10; original Gradle layout |
| Infomaniak Maven 3.2.9 | Previously shipped native Android SDK, compatible with Kotlin 2.2.10 |
| Sharekey SDK | Own coordinates; GitHub Release/Yarn distribution; see [release status](publishing.md) |

The mobile app uses RN 0.87.1, Kotlin 2.2.10, AGP 9.2.1 and Gradle 9.4.1 at the audit date.
Those are **consumer** versions. The SDK has its own build toolchain. Establish and document both
instead of copying the app's version constants into the SDK and assuming compatibility.

## Provenance from the 2026-09-24 mobile audit

The audit compared published Maven sources and artifacts, reviewed changes and ran isolated JVM
compiler/runtime checks. It did not rebuild all SDK binaries or execute authenticated Android flows.

- Matching Infomaniak source: [`6d2bf1582a23f2673933e33e09f8111bf8f4f8ab`](https://github.com/Infomaniak/realm-kotlin/commit/6d2bf1582a23f2673933e33e09f8111bf8f4f8ab).
  All 240 compared non-generated source files matched the published compiler, Gradle plugin and
  Android runtime source artifacts. This does not establish byte-for-byte binary reproducibility.
- Infomaniak tag `3.2.9` instead resolved to `c7e7ec7cdb16dbcd3de329638307a9fa10fa7d9d`, with KRDB
  packages and Kotlin 2.2.20. Do not use that tag to reproduce the Maven package.
- Original 3.0.0 and the matching Infomaniak revision pin Core
  `d8a68400288245c01be3dcb0ca3bcd4922fee680` (20.0.1).
- Infomaniak's cached companion optimization rejects valid models with `companion object Factory`.
  The same compiled models work with the official runtime. This defect is **not present in the
  original companion lookup currently in this repository**; do not reintroduce it while porting.
- The original compiler sample with 116 fields compiled under Infomaniak/Kotlin 2.2.10 with IR
  verification and passed generated-schema and unmanaged-accessor checks. Managed CRUD, concurrent
  encrypted access and migration need additional tests.

The full audit is in the mobile repository at `docs/realm-kotlin-fork-audit-2026-09.md`.

## Adaptation order

1. Establish a clean source/build baseline and record all inputs and resolved artifacts.
2. Port the required Kotlin compiler and build compatibility changes from the **matching** Infomaniak
   source, reviewing each change against this repository's layout. Infomaniak moved the SDK Gradle
   root; this checkout still uses `packages/`. A wholesale build-script copy would change task paths.
3. Preserve correct original runtime behavior. Add named-companion tests before importing a lookup
   optimization; separately review the nullable transaction return change and compiler recursion fix.
4. Build and test an isolated Sharekey publication, then validate its real mobile consumers.
5. Assess Core updates separately after SDK adoption is proven. Changing Core and the compiler in
   one opaque update makes failures and rollback harder to diagnose.

Potential patch sources include [Infomaniak's compiler recursion fix](https://github.com/Infomaniak/realm-kotlin/pull/3)
and [Kotlin 2.3.21 work](https://github.com/Infomaniak/realm-kotlin/pull/9). Their code and release status
must be rechecked when adopting them; neither is an instruction to upgrade beyond the agreed target.

Core 20.1.0 and 20.1.2 contain later query/migration/open fixes. The Android hardlock report concerns
external app storage and was not reproduced in Sharekey. Review applicability and shared-file
compatibility rather than presenting these as confirmed app incidents.

## Publication contract

Keep `io.realm.kotlin` model/API packages. The SDK uses Maven group and Gradle plugin ID
`com.sharekey.realm.kotlin`, version `3.0.0-sharekey.1`. Inspect all of:

- `buildSrc/src/main/kotlin/Config.kt` and `io/realm/RealmPublishPlugin.kt`;
- `packages/gradle-plugin` artifact IDs, compiler selection, substitutions and marker publication;
- SDK test substitutions, examples, integration fixtures and benchmark dependencies;
- generated version constants, native-library loading/cache paths and consumer ProGuard rules;
- workflow publish conditions and release scripts.

The Gradle publisher now stages locally without Realm's Nexus profile or fixed signing-key ID.
Signing uses Sharekey-supplied environment/user properties. The inherited release script is disabled;
other legacy distribution scripts are not a release path. The mobile distribution uses a GitHub
Release tarball containing the Maven repository; Yarn installs it for Gradle consumption. Its workflow
uses the repository token and public downloads, with no separate registry credentials. See
[publishing](publishing.md) for release and verification steps.

Each release should record SDK/Core commits, toolchain, unique version, immutable tag, checksums and
test results. Keep secrets outside tracked files. Assign a maintainer and document which Kotlin,
Gradle/AGP and consumer combinations are actually supported. This fork does not provide Realm JS or
Realm Swift builds automatically.

## Adoption gates for the mobile app

The [Sharekey integration guide](sharekey-integration.md) records the inspected app versions, model
shapes, encrypted storage lifecycle and the SDK/mobile ownership of these checks.

The app's JS and Kotlin SDKs share encrypted Realm files; app-level generation/key/lease coordination
lives in the mobile repository. Its JS Core headers identify 20.1.0, while current Kotlin Core is
20.0.1. A Kotlin Core upgrade alone does not upgrade the JS engine.

Before switching coordinates or a Core revision, require:

1. SDK/compiler tests, including default/named/CREATOR companions, plus Android instrumentation.
2. JS → Kotlin → JS reads/writes with representative app schemas and encrypted files; test the app
   policy for replacing legacy plaintext generations without enabling plaintext application opens.
3. Simultaneous opens, native push/channel writes, notification delivery and background work.
4. Interrupted work, reopening, logout/reset, stale-generation rejection and no hidden file recreation.
5. Old-file migration and rollback checks for any Core change.
6. Actual consumer debug/release builds and 16 KB device/emulator coverage; R8 checks if enabling it.

A successful SDK compilation or synthetic file round trip is useful evidence, but does not satisfy
the full adoption matrix. Record any deferred gate explicitly before making a release decision.
