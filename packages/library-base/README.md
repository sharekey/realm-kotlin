# Realm Kotlin runtime library

`library-base` contains the public local-database API and its runtime implementation. It depends on
`cinterop` for the native boundary and on compiler-generated model/schema accessors in consuming apps.

- [Runtime architecture](../../docs/maintainers/runtime.md): configuration, object ownership,
  transactions, snapshots and notifications.
- [Repository map](../../docs/maintainers/repository-map.md): related compiler and native modules.
- [Build and test](../../docs/maintainers/build-and-test.md): SDK commands run from `packages/`.
- [Consumer documentation](../../docs/README.md): application-facing usage examples.

Start with `src/commonMain/kotlin/io/realm/kotlin/Realm.kt`, `RealmConfiguration.kt` and `internal/`.
The `jvm` source set is shared by Android and desktop JVM. Darwin-specific actuals live under
`nativeDarwin`, `nativeIos` and `nativeMacos`.

Shared runtime tests live in the separate `test-base` module. Native libraries are built through
`cinterop` and the pinned Core submodule; there is no `cpp_engine` directory in this checkout.
