# Working in Sharekey Realm Kotlin

## Start here

- Read [the maintainer index](docs/maintainers/README.md) and the guide relevant to the change.
- This repository builds a Kotlin SDK, compiler plugin and native bindings. It is not the React Native
  application; do not apply the mobile repository's Yarn commands or TypeScript conventions here.
- `community` is the local-database maintenance baseline. `main` retains Atlas Sync code. Do not merge
  `main` wholesale into `community`; review individual fixes instead.
- The initial documented checkout is upstream `community` at `28182c37`: Realm 3.0.0, Kotlin 2.0.20.
  The application's Infomaniak 3.2.9 / Kotlin 2.2.10 adaptation is not present yet. Check current source
  before treating this snapshot as a supported release.

## Find the owning layer

| Change | Starting point |
| --- | --- |
| Public API, queries, transactions, notifications | `packages/library-base` and [runtime guide](docs/maintainers/runtime.md) |
| Model generation or Kotlin compiler incompatibility | `packages/plugin-compiler` and [compiler guide](docs/maintainers/compiler.md) |
| Plugin application or compiler artifact resolution | `packages/gradle-plugin` |
| Native values, callbacks, JNI, loading | `packages/cinterop`, `packages/jni-swig-stub` |
| Storage engine, file format, encryption internals | `packages/external/core` Git submodule |
| SDK behavior and compiler regression tests | `packages/test-base` |
| Versions, publishing and style configuration | `buildSrc`, module build scripts, `config` |

See [repository map](docs/maintainers/repository-map.md) for source paths and dependency boundaries.

## Build and verification

- The SDK Gradle root is **`packages/`**. Its tasks are `:library-base:...`, `:test-base:...`, etc.,
  not `:packages:...`. The repository root orchestrates other builds.
- Read [build and test](docs/maintainers/build-and-test.md) before running Gradle. The Core submodule
  must be initialized; even configuration reads files from it.
- Check `buildSrc/src/main/kotlin/Config.kt` and the relevant Gradle wrapper for actual tool versions.
  The app's Gradle/Kotlin versions are not the SDK's build toolchain.
- Use the narrowest meaningful tests first. Compiler changes need generated-code and runtime checks;
  native or storage changes need device/interop coverage. A successful compile is not a data test.
- Report exactly what ran. Source-verified commands in the guide are not evidence of a passing build.
- For documentation-only work, check relative links and `git diff --check`; do not trigger a native
  rebuild solely to validate prose.

## Editing rules

- Make focused changes and preserve the surrounding Kotlin style. Use explicit types/visibility in
  public APIs; the library enables strict explicit API mode. Use the existing ktlint/detekt setup.
- Preserve `io.realm.kotlin` source/API packages when changing Maven publication coordinates.
  Several compiler, test and plugin paths contain hard-coded coordinates; search all of them.
- Treat model generation and runtime helpers as one contract. Keep named companions, schema names,
  persisted names, links, collection types and managed/unmanaged accessor behavior compatible.
- Do not edit generated SWIG Java/C++, generated version files, IR `output` directories or build
  artifacts. Edit their inputs; review expected IR fixture changes rather than accepting them blindly.
- Preserve tracked symlinks, including shared `buildSrc` and Android/common test sources.
- Do not mutate the Core submodule incidentally. Record its SHA and test data compatibility when it
  changes. `git submodule update --init --recursive` uses the pinned revision; `--remote` does not.
- Keep compiler/toolchain adaptation, runtime fixes and Core upgrades in separately reviewable changes.
- Update the relevant maintainer guide when the layout, commands or supported combinations change.

## Fork and release work

- Follow [fork maintenance](docs/maintainers/fork-maintenance.md). It records the audited Infomaniak
  source commit, the misleading `3.2.9` tag and the Sharekey adoption gates.
- Current publishing configuration still targets upstream Realm coordinates and infrastructure.
  Use an isolated local test repository while developing; inspect destinations before publishing.
- Keep credentials outside the repository and logs. Never add tokens, signing material or private
  environment files to documentation or commits.
- For application adoption, test Realm JS and Kotlin against the same encrypted files. This SDK's
  tests alone do not establish compatibility with the mobile application's storage lifecycle.

## Git workflow

- Preserve user changes. Prefer focused `codex/` branches from the selected maintenance baseline when
  creating a new branch; do not change the GitHub default branch or rewrite existing tags implicitly.
- Keep upstream history and commit provenance available for backports. Link maintenance work to
  [M-3153](https://yt.sharekey.com/issue/M-3153).
- Do not add AI or agent attribution trailers to commits.
