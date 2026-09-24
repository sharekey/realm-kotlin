# Sharekey mobile integration

Observed **2026-09-24**. Inline paths below refer to the separate `sharekey/mobile` repository;
relative links refer to this SDK repository. This records the Android consumer contract and adoption status. A reported manual app test
is not an enumerated record of every shared-file scenario below.

## Toolchains and dependencies

| Setting | Mobile Android consumer | SDK build |
| --- | --- | --- |
| Kotlin / JVM target | 2.2.10 / 17 | 2.2.10 / 17 |
| Gradle / AGP | 9.4.1 / 9.2.1 | 8.14.3 / 8.10.0 |
| Minimum / compile / target API | 24 / 37 / 36 | 21 / 35 / 35 |
| NDK | 28.2.13676358 | 27.0.12077973 |

Mobile sources are `android/build.gradle`, `android/app/build.gradle`, the wrapper and
`android/gradle.properties`. The AGP 9 consumer uses `android.builtInKotlin=false` and
`android.newDsl=false`. SDK versions live in [Config.kt](../../buildSrc/src/main/kotlin/Config.kt).
Keep the SDK's build toolchain independent; validate the app's consumer combination instead of
changing every SDK tool version to match it. The isolated consumer checks and their limits are in
[migration validation](kotlin-2.2.10-migration.md).

The app previously consumed Infomaniak 3.2.9. A local Sharekey snapshot was built and manually
accepted by the mobile maintainer on 2026-09-24, who authorized permanent adoption. Release
preparation now uses `com.sharekey.realm.kotlin` for both plugin and Maven group; remote publication
remains pending. Its `android/app/gradle.lockfile` already resolves coroutines 1.10.2, atomicfu 0.29.0
and serialization 1.9.0, matching this fork. Direct coroutines declarations still say 1.10.0;
the resolved graph is the relevant comparison. Change plugin and runtime coordinates together during
adoption, preserve `io.realm.kotlin` model imports, and regenerate the app's Android dependency locks.

## Models, queries and shared storage

Native definitions are in `android/app/src/main/java/com/sharekey/realm/schema/`; registrations are in
`android/app/src/main/java/com/sharekey/realm/RealmInstanceConfig.kt`. Shapes include indexed integers/longs,
string primary keys, linked objects, embedded participants/profiles, object/primitive/nullable-string lists,
binary and nullable-binary fields, unnamed companions and secondary constructors. Native consumers
query IDs and `isDirect == true AND participants.id == $0`. The native channel fetcher,
`android/app/src/main/java/com/sharekey/reactModules/notification/ChannelFetcher.kt`, updates channels
through `writeBlocking` and `copyToRealm(UpdatePolicy.ALL)` while JS may be active.
Notifications, incoming-call UI, channel decryption and sharing shortcuts depend on these reads.

`src/services/realm-storage/RealmStorageService.ts` opens all 13 encrypted files before publishing
readiness. `android/app/src/main/java/com/sharekey/realm/RealmBuilder.kt` opens the same generation
directory, schema version and 64-byte key. The coordinator,
`android/app/src/main/java/com/sharekey/realm/RealmStorageCoordinator.kt`, owns account/backend binding, leases,
native instance closure and reset coordination. Files live under `noBackupFilesDir`. A schema-version
change recreates the entire generation and resets synchronization; independent
`deleteRealmIfMigrationNeeded` is disabled. Keep this policy in the app, outside the SDK.

Realm JS 20.2.0's installed Android Core headers identify **20.1.0**
(`node_modules/realm/prebuilds/android/arm64-v8a/include/realm/version_numbers.hpp`). The preceding
Infomaniak SDK and this fork use **Core 20.0.1**. This pairing predates adoption; it is not evidence of
either incompatibility or proven concurrent access. A Kotlin SDK/Core change does not update JS or
Realm Swift. Review Core upgrades separately from compiler adaptation.

The [synthetic models](../../packages/test-base/src/commonMain/kotlin/io/realm/kotlin/entities/SharekeyCompatibilityModels.kt)
and [combined regression](../../packages/test-base/src/commonTest/kotlin/io/realm/kotlin/test/common/SharekeyCompatibilityTests.kt)
cover generated accessors, encrypted reopen, participant queries, native-style updates and preserved
nested/list/binary data. They neither copy the app schemas nor execute Realm JS, its generation
coordinator or concurrent SDK access. Existing app Jest/portable lease tests also do not establish
that full Android contract.

## Retain versus exclude from Android release jobs

Retain compiler generation, companions/reflection, encryption, embedded objects/lists, frozen-reference
ownership, JNI scheduling and the native loader. Keep JVM regression tests: Android shares the SDK's
`jvm` source set, and host tests provide useful coverage. Unused public data types are not safe deletion
candidates solely because the current app does not declare them.

The app uses unnamed companions and has release R8 disabled. Keep the named-companion consumer fix
and minified sample regression as SDK protection; they are not a current app minification incident.
No native app use of `RealmInstant` was found; timestamps use integer/long/string fields. The API
24/25 clock correction is SDK maintenance within the app's supported range, not an observed app
timestamp defect. The app's Detox configuration targets API 28, so it cannot cover that branch.

Kotlin Apple binaries, old Compose/KMM examples, historical Gradle fixtures and benchmarks need not
block an Android-only release job. Sharekey iOS uses RealmSwift. Exclude unsupported consumer jobs
explicitly rather than deleting cross-platform source or claiming those targets were validated.
Publication target selection does not universally disable target configuration; see
[build controls](build-and-test.md#native-build-and-publication-controls).

## Adoption gates and ownership

1. **SDK maintainers:** run compiler/runtime tests and Android instrumentation, including API 24/25
   and a modern 16 KB environment; verify packaged artifacts and actual consumer toolchains.
2. **Mobile maintainers:** use representative Channel/User and linked app schemas for encrypted
   JS → Kotlin → JS reads/writes, simultaneous opens and native notification/channel updates.
   Verify nullability, binary/list/embedded data and existing-file reopen without hidden recreation.
3. **Mobile maintainers:** exercise offline cold start, incoming push/call/sharing work, interrupted
   writes, logout/reset with active consumers, stale-generation rejection and process restart.
   Check wrong/missing keys and owner/backend mismatch remain fail-closed. Legacy plaintext coverage
   must verify the app's encrypted-generation replacement, not authorize plaintext application opens.
4. **SDK and mobile maintainers:** verify upgrade from the shipped SDK and rollback using test copies
   of existing encrypted files; for a Core change, explicitly cover file-format migration/rollback.
   Do not bump app schema versions merely to hide an SDK incompatibility.
5. **Release maintainers:** configure Sharekey publication destinations/immutable versions, change both
   app dependency coordinates, regenerate locks and run actual app debug/release builds and device
   flows. Record SDK/Core commits, resolved versions, commands, devices, results and deferred gates.

See [fork maintenance](fork-maintenance.md#publication-contract) for publication scope and
[runtime ownership](runtime.md#sharekeys-extra-compatibility-boundary) for the SDK/app boundary.
