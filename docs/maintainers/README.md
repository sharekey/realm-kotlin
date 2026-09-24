# Sharekey maintainer guide

These documents explain how to work on the SDK itself. The [consumer guides](../README.md) explain
how an application uses Realm. The source code and build scripts are authoritative when older
upstream documentation disagrees with them.

## Reading order

1. [Repository map](repository-map.md): modules, build roots and where to make a change.
2. [Runtime](runtime.md): opening files, generated models, transactions, snapshots and notifications.
3. [Compiler plugin](compiler.md): Gradle integration, FIR/IR transformations and regression tests.
4. [Build and test](build-and-test.md): prerequisites, commands, source versus artifact testing.
5. [Fork maintenance](fork-maintenance.md): branches, compatibility work, publication and app adoption.
6. [Sharekey integration](sharekey-integration.md): actual mobile model/toolchain contract, ownership
   boundaries and the checks needed before switching the app.
7. [Publishing](publishing.md): Sharekey coordinates, staging, signing and release prerequisites.

[AGENTS.md](../../AGENTS.md) is the short operating guide for automated contributors.

## Development baseline (2026-09-24)

| Item | This repository |
| --- | --- |
| Fork | `sharekey/realm-kotlin` |
| Upstream base | `community` / `28182c37` |
| SDK / Maven group | `3.0.0-sharekey.1` / `com.sharekey.realm.kotlin` (unpublished candidate) |
| Kotlin / JVM bytecode target | `2.2.10` / `17` |
| Gradle / Android Gradle Plugin | `8.14.3` / `8.10.0` |
| Realm Core gitlink | `d8a68400288245c01be3dcb0ca3bcd4922fee680` (20.0.1) |
| GitHub default branch | `community` (verified on 2026-09-24); local `origin/HEAD` can be stale |

Version sources: [Config.kt](../../buildSrc/src/main/kotlin/Config.kt),
[SDK wrapper](../../packages/gradle/wrapper/gradle-wrapper.properties), and the Git submodule entry.
Do not read these SDK versions as the versions of the consuming mobile app.

`community` is the appropriate base for Sharekey's local database usage. It contains the removal of
Atlas Sync and the 3.0.0 release. Sharekey's Kotlin 2.2.10 adaptation is developed on top of that
baseline. Own publication coordinates are configured. Remote Maven distribution still requires
registry setup; see [publishing](publishing.md).

## Evidence and maintenance status

The initial documentation commit describes the upstream baseline. The subsequent migration changes
and executed checks are recorded in [Kotlin 2.2.10 migration](kotlin-2.2.10-migration.md).
Commands in the guides alone are not a record of successful runs.

The separate mobile audit identified source provenance and a regression in Infomaniak's published
3.2.9. The [maintenance guide](fork-maintenance.md) preserves the relevant findings and distinguishes
them from the behavior of the Sharekey adaptation.

See [Kotlin 2.2.10 migration](kotlin-2.2.10-migration.md) for the toolchain and executed checks.
