# Compiler plugin and model generation

## How the plugin reaches a consumer

The consumer applies `io.realm.kotlin` to the Gradle module containing its models. In
[`RealmPlugin.kt`](../../packages/gradle-plugin/src/main/kotlin/io/realm/kotlin/gradle/RealmPlugin.kt),
the plugin applies `RealmCompilerSubplugin` and substitutes JVM runtime artifacts for Android unit
test configurations. Runtime dependencies are still declared by the consumer.

[`RealmCompilerSubplugin.kt`](../../packages/gradle-plugin/src/main/kotlin/io/realm/kotlin/gradle/RealmCompilerSubplugin.kt)
selects the compiler artifact and reports its plugin ID. Its group and IDs are hard-coded; changing
`Realm.group` alone is not enough to change all artifact resolution. The Gradle plugin also generates
`PLUGIN_VERSION` and `CORE_VERSION` from build inputs.

Inspect Native resolution carefully: the current `getPluginArtifactForNative()` returns the regular
compiler artifact, while `test-base` explicitly requests `plugin-compiler-shaded`. Do not assume that
the published consumer and internal tests use identical wiring.

## Frontend and IR phases

The compiler entry point is
[`Registrar.kt`](../../packages/plugin-compiler/src/main/kotlin/io/realm/kotlin/compiler/Registrar.kt).
It registers legacy synthetic resolution, K2 FIR extensions and IR generation, and clears the schema
collector for a compilation. Several extensions run last to avoid exposing injected internals to
other plugins such as serialization.

| Stage | Source relative to `packages/plugin-compiler/src/main/kotlin/io/realm/kotlin/compiler/` |
| --- | --- |
| Plugin registration and diagnostics | `Registrar.kt`, `RealmCommandLineProcessor.kt`, `Logger.kt` |
| Legacy frontend model additions | `RealmModelSyntheticCompanionExtension.kt`, `RealmModelSyntheticMethodsExtension.kt` |
| K2 model declarations and companions | `fir/model/RealmModelRegistrar.kt`, `CompanionExtension.kt`, `ObjectExtension.kt` |
| IR transformation orchestration | `RealmModelLoweringExtension.kt` |
| Property validation, accessors and schema collection | `AccessorModifierIrGeneration.kt` |
| Generated object-reference fields, schema and constructors | `RealmModelSyntheticPropertiesGeneration.kt` |
| Generated equality/hash/string methods | `RealmModelDefaultMethodGeneration.kt` |
| Compiler symbol lookup and shared identities | `IrUtils.kt`, `Identifiers.kt` |

The lowering validates model classes, injects `RealmObjectInternal`, rewrites property accessors,
generates default methods and fills companion schema/constructor methods. On Native it also creates
an associated-object annotation so runtime lookup does not depend on JVM reflection.

Generated accessors must keep two paths correct: ordinary fields for unmanaged objects and native
object access through `RealmObjectHelper` for managed objects. The schema representation must agree
with persisted names, primary keys, embedded objects, links, backlinks and collections.

## Why Kotlin versions are coupled

This plugin compiles against `kotlin-compiler-embeddable` and calls internal FIR/IR APIs. A newer Kotlin
patch release may change method signatures or argument representation even when ordinary Kotlin
source remains compatible. Updating a version constant is therefore not a complete compiler upgrade.

Start compatibility work in [Config.kt](../../buildSrc/src/main/kotlin/Config.kt),
[`plugin-compiler/build.gradle.kts`](../../packages/plugin-compiler/build.gradle.kts) and the files in
the table. Review Kotlin compile-testing, AtomicFu, serialization, Gradle and AGP compatibility too.
Do not present an app build as proof that every supported schema compiles correctly.

## Tests and fixtures

- [`GenerationExtensionTest.kt`](../../packages/plugin-compiler/src/test/kotlin/io/realm/kotlin/compiler/GenerationExtensionTest.kt)
  checks generated code and IR fixtures under `plugin-compiler/src/test/resources`.
- [`Sample.kt`](../../packages/plugin-compiler/src/test/resources/sample/input/Sample.kt) covers a broad
  range of scalar, link and collection fields. The `schema` fixture exercises schema-related lowering.
- [`test-base/src/jvmTest/.../compiler`](../../packages/test-base/src/jvmTest/kotlin/io/realm/kotlin/test/compiler)
  contains model validation, primary key, persisted-name, collection, cyclic and backlink tests.
- `test-base/src/commonTest` verifies runtime semantics of compiled models across targets.

When a compiler update changes an IR dump, inspect the structural difference and execute the
generated model; do not merely replace the expected dump. Verify managed database operations as well
as unmanaged getters/setters. Useful cases include default and named companions, recursive models,
embedded objects, nullable collections, persisted names and coexistence with serialization.

The mobile audit compiled the original sample with Infomaniak's published Kotlin 2.2.10 plugin and
reproduced a named-companion runtime regression. Those results are evidence about that published
package, not test results for this new Sharekey checkout. Preserve the good compiler coverage while
avoiding the faulty companion optimization. See [fork maintenance](fork-maintenance.md).
