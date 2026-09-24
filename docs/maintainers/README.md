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

[AGENTS.md](../../AGENTS.md) is the short operating guide for automated contributors.

## Baseline inspected on 2026-09-24

| Item | This repository |
| --- | --- |
| Fork | `sharekey/realm-kotlin` |
| Checked-out branch / source commit | `community` / `28182c37` |
| SDK / Maven group | `3.0.0` / `io.realm.kotlin` |
| Kotlin / JVM bytecode target | `2.0.20` / `1.8` |
| Gradle / Android Gradle Plugin | `7.6` / `7.3.1` |
| Realm Core gitlink | `d8a68400288245c01be3dcb0ca3bcd4922fee680` (20.0.1) |
| Core checkout at inspection | Uninitialized |
| Local `origin/HEAD` at inspection | `origin/main`, not the maintenance baseline |

Version sources: [Config.kt](../../buildSrc/src/main/kotlin/Config.kt),
[SDK wrapper](../../packages/gradle/wrapper/gradle-wrapper.properties), and the Git submodule entry.
Do not read these SDK versions as the versions of the consuming mobile app.

`community` is the appropriate base for Sharekey's local database usage. It contains the removal of
Atlas Sync and the 3.0.0 release. Our Kotlin 2.2.10 compatibility work has **not** been applied to this
checkout. Its packaging and CI are also still inherited from upstream.

## Evidence and maintenance status

This documentation pass inspected the source and task definitions. It did not initialize Core, build
the SDK, change dependencies, publish artifacts or run device tests. Commands below are documented
entry points, not a record of successful runs on the new fork.

The separate mobile audit identified source provenance and a regression in Infomaniak's published
3.2.9. The [maintenance guide](fork-maintenance.md) preserves the relevant findings and distinguishes
them from the behavior of this unmodified community baseline.
