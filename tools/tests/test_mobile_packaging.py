"""Regression checks for release provenance, metadata, ELF files and consumer repositories."""

import hashlib
import importlib.util
import os
import shutil
import struct
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pack_mobile", TOOLS / "pack-mobile.py")
pack_mobile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pack_mobile)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.STDOUT).strip()


def initialize_repo(root):
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "Packaging test")
    git(root, "config", "user.email", "packaging@example.invalid")
    (root / "source.kt").write_text("// tracked source\n")
    (root / ".gitignore").write_text("/build/\n")
    git(root, "add", ".")
    git(root, "commit", "-qm", "Test fixture")


class SourceProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        core_origin = base / "core"
        initialize_repo(core_origin)
        self.root = base / "sdk"
        initialize_repo(self.root)
        git(self.root, "-c", "protocol.file.allow=always", "submodule", "add", str(core_origin), "packages/external/core")
        git(self.root, "commit", "-qam", "Pin test Core")
        self.core = self.root / "packages/external/core"
        original_root = pack_mobile.ROOT
        pack_mobile.ROOT = self.root
        self.addCleanup(setattr, pack_mobile, "ROOT", original_root)

    def test_clean_checkout_allows_ignored_build_outputs(self):
        (self.root / "build").mkdir()
        (self.root / "build/output").write_text("generated")
        self.assertEqual(pack_mobile.verify_source(), (git(self.root, "rev-parse", "HEAD"), git(self.core, "rev-parse", "HEAD")))

    def test_rejects_untracked_sdk_source(self):
        (self.root / "untracked.kt").write_text("class Untracked")
        with self.assertRaises(ValueError):
            pack_mobile.verify_source()

    def test_rejects_untracked_core_source_even_when_git_status_ignores_submodules(self):
        git(self.root, "config", "diff.ignoreSubmodules", "all")
        (self.core / "untracked.cpp").write_text("int unexpected;")
        with self.assertRaises(ValueError):
            pack_mobile.verify_source()

    def test_rejects_modified_sources(self):
        for repository in (self.root, self.core):
            with self.subTest(repository=repository):
                source = repository / "source.kt"
                previous = source.read_text()
                source.write_text("// modified source\n")
                with self.assertRaises(ValueError):
                    pack_mobile.verify_source()
                source.write_text(previous)


class GradleMetadataTests(unittest.TestCase):
    version = "3.0.0-sharekey.1"

    def metadata(self, module):
        component = {"group": pack_mobile.GROUP, "module": module, "version": self.version}
        return {"component": component, "variants": [{"name": "runtime", "dependencies": []}]}

    def verify(self, module, metadata):
        pack_mobile.verify_metadata(module, self.version, metadata, Path("unused-no-file-variants"))

    def test_rejects_metadata_copied_from_another_module(self):
        with self.assertRaisesRegex(ValueError, "Unexpected Gradle component"):
            self.verify("gradle-plugin", self.metadata("plugin-compiler"))

    def test_platform_component_must_point_to_its_own_kmp_root(self):
        for module, root in pack_mobile.PLATFORM_ROOTS.items():
            with self.subTest(module=module):
                metadata = self.metadata(root)
                metadata["component"]["url"] = f"../../{root}/{self.version}/{root}-{self.version}.module"
                self.verify(module, metadata)
                metadata["component"]["module"] = "gradle-plugin"
                with self.assertRaisesRegex(ValueError, "Unexpected Gradle component"):
                    self.verify(module, metadata)

    def test_rejects_a_redirect_to_an_unexpected_artifact(self):
        metadata = self.metadata("cinterop")
        metadata["component"]["url"] = "../../unrelated/version/unrelated.module"
        with self.assertRaisesRegex(ValueError, "Unexpected KMP component redirect"):
            self.verify("cinterop-jvm", metadata)
        with self.assertRaisesRegex(ValueError, "Unexpected component redirect"):
            self.verify("cinterop", metadata)

    def test_rejects_legacy_dependencies_and_constraints(self):
        for field in ("dependencies", "dependencyConstraints"):
            for group in pack_mobile.LEGACY_GROUPS:
                with self.subTest(field=field, group=group):
                    metadata = self.metadata("library-base")
                    metadata["variants"][0][field] = [{
                        "group": group, "module": "cinterop", "version": {"requires": self.version},
                    }]
                    with self.assertRaisesRegex(ValueError, "Upstream SDK dependency"):
                        self.verify("library-base", metadata)

    def test_accepts_own_and_external_dependencies(self):
        metadata = self.metadata("library-base")
        metadata["variants"][0]["dependencies"] = [
            {"group": pack_mobile.GROUP, "module": "cinterop", "version": {"requires": self.version}},
            {"group": "org.jetbrains.kotlin", "module": "kotlin-stdlib", "version": {"requires": "2.2.10"}},
        ]
        self.verify("library-base", metadata)


class AndroidElfTests(unittest.TestCase):
    # Independent ELF fixtures: ELF class, e_machine, ELF header size, program header size.
    architectures = {
        "arm64-v8a": (2, 183, 64, 56),
        "armeabi-v7a": (1, 40, 52, 32),
        "x86": (1, 3, 52, 32),
        "x86_64": (2, 62, 64, 56),
    }

    def elf(self, abi, alignment=16384, segment_type=1):
        elf_class, machine, header_size, entry_size = self.architectures[abi]
        content = bytearray(header_size + entry_size)
        content[:7] = b"\x7fELF" + bytes((elf_class, 1, 1))
        struct.pack_into("<HHI", content, 16, 3, machine, 1)
        if elf_class == 2:
            struct.pack_into("<Q", content, 32, header_size)
            struct.pack_into("<HHH", content, 52, header_size, entry_size, 1)
            struct.pack_into("<IIQQQQQQ", content, header_size, segment_type, 4, 0, 0, 0,
                             len(content), len(content), alignment)
        else:
            struct.pack_into("<I", content, 28, header_size)
            struct.pack_into("<HHH", content, 40, header_size, entry_size, 1)
            struct.pack_into("<IIIIIIII", content, header_size, segment_type, 0, 0, 0,
                             len(content), len(content), 4, alignment)
        return content

    def verify(self, content, abi):
        pack_mobile.verify_elf(content, f"jni/{abi}/librealmc.so", abi)

    def test_accepts_all_four_correctly_labeled_architectures(self):
        for abi in self.architectures:
            with self.subTest(abi=abi):
                self.verify(self.elf(abi), abi)

    def test_rejects_libraries_copied_between_abi_directories(self):
        for source_abi in self.architectures:
            for destination_abi in self.architectures:
                if source_abi != destination_abi:
                    with self.subTest(source=source_abi, destination=destination_abi):
                        with self.assertRaisesRegex(ValueError, "ELF architecture does not match"):
                            self.verify(self.elf(source_abi), destination_abi)

    def test_rejects_wrong_elf_class_even_when_machine_matches(self):
        for abi in self.architectures:
            with self.subTest(abi=abi):
                content = self.elf(abi)
                content[4] = 3 - content[4]
                with self.assertRaisesRegex(ValueError, "ELF architecture does not match"):
                    self.verify(content, abi)

    def test_rejects_truncated_headers_and_program_tables(self):
        for abi in self.architectures:
            content = self.elf(abi)
            for length in (0, 6, 51, 63, len(content) - 1):
                with self.subTest(abi=abi, length=length):
                    with self.assertRaises(ValueError):
                        self.verify(content[:length], abi)

    def test_rejects_inadequate_or_invalid_page_alignment(self):
        for abi in self.architectures:
            for alignment in (4096, 24576):
                with self.subTest(abi=abi, alignment=alignment):
                    with self.assertRaisesRegex(ValueError, "not aligned for 16 KB pages"):
                        self.verify(self.elf(abi, alignment=alignment), abi)

    def test_rejects_elf_without_load_segments(self):
        for abi in self.architectures:
            with self.subTest(abi=abi):
                with self.assertRaisesRegex(ValueError, "No ELF load segments"):
                    self.verify(self.elf(abi, segment_type=4), abi)


class AndroidGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "tools").mkdir()
        shutil.copy2(TOOLS / "test-published-android.sh", self.root / "tools/test-published-android.sh")
        gradle = self.root / "gradlew"
        gradle.write_text('''#!/usr/bin/env bash
printf '%s\\n' "$@" > sdk-arguments
exit "${SDK_EXIT:-0}"
''')
        gradle.chmod(0o755)
        (self.root / "tools/test-minified-android.sh").write_text('''#!/usr/bin/env bash
touch minified-ran
exit "${MINIFIED_EXIT:-0}"
''')

    def run_gate(self, api, sdk_exit=0, minified_exit=0):
        return subprocess.run(
            ["bash", "tools/test-published-android.sh", str(api)], cwd=self.root,
            env={**os.environ, "SDK_EXIT": str(sdk_exit), "MINIFIED_EXIT": str(minified_exit)},
            capture_output=True, text=True,
        )

    def test_failed_sdk_suite_stops_before_minified_sample_on_both_apis(self):
        for api in (25, 35):
            with self.subTest(api=api):
                self.assertEqual(self.run_gate(api, sdk_exit=23).returncode, 23)
                self.assertFalse((self.root / "minified-ran").exists())

    def test_api_25_only_runs_the_clock_regression(self):
        result = self.run_gate(25)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "-Pandroid.testInstrumentationRunnerArguments.class=io.realm.kotlin.test.android.PlatformInfoTest",
            (self.root / "sdk-arguments").read_text().splitlines(),
        )
        self.assertFalse((self.root / "minified-ran").exists())

    def test_api_35_runs_the_full_suite_then_minified_sample(self):
        result = self.run_gate(35)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("InstrumentationRunnerArguments.class", (self.root / "sdk-arguments").read_text())
        self.assertTrue((self.root / "minified-ran").exists())

    def test_failed_minified_sample_fails_the_gate(self):
        self.assertEqual(self.run_gate(35, minified_exit=19).returncode, 19)
        self.assertTrue((self.root / "minified-ran").exists())

    def test_unsupported_api_fails_before_running_any_checks(self):
        self.assertEqual(self.run_gate(26).returncode, 2)
        self.assertFalse((self.root / "sdk-arguments").exists())
        self.assertFalse((self.root / "minified-ran").exists())


class ConsumerRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "tools").mkdir()
        shutil.copy2(TOOLS / "test-mobile-package.sh", self.root / "tools/test-mobile-package.sh")
        self.staging = self.root / "packages/build/m2-buildrepo"
        self.staging.mkdir(parents=True)
        (self.staging / "original").write_text("original staging content")
        package = self.root / "input/package"
        (package / "maven").mkdir(parents=True)
        content = b"only the current archive"
        (package / "maven/current").write_bytes(content)
        (package / "SHA256SUMS").write_text(f"{hashlib.sha256(content).hexdigest()}  maven/current\n")
        with tarfile.open(self.root / "sdk.tgz", "w:gz") as archive:
            archive.add(package, arcname="package")
        gradle = self.root / "gradlew"
        gradle.write_text('''#!/usr/bin/env bash
set -eu
repo=packages/build/m2-buildrepo
[[ -L "$repo" ]]
[[ "$(cat "$repo/current")" == "only the current archive" ]]
[[ "$(ls -A "$repo")" == current ]]
exit "${CONSUMER_EXIT:-0}"
''')
        gradle.chmod(0o755)
        # The old fixed extraction path must never contribute stale Maven files.
        stale = self.root / "build/mobile-package/unpacked/package/maven"
        stale.mkdir(parents=True)
        (stale / "stale").write_text("not in this archive")

    def run_consumer(self, expected_exit):
        result = subprocess.run(
            ["bash", "tools/test-mobile-package.sh", "sdk.tgz"], cwd=self.root,
            env={**os.environ, "CONSUMER_EXIT": str(expected_exit)}, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, expected_exit, result.stdout + result.stderr)
        self.assertFalse(self.staging.is_symlink())
        self.assertEqual((self.staging / "original").read_text(), "original staging content")
        self.assertEqual(list((self.root / "build/mobile-package").glob("consumer-check.*")), [])

    def test_success_and_repeat_use_fresh_archives_and_restore_staging(self):
        self.run_consumer(0)
        self.run_consumer(0)

    def test_failed_consumer_preserves_exit_code_and_restores_staging(self):
        self.run_consumer(23)
        self.run_consumer(0)

    def test_bad_archive_leaves_staging_intact(self):
        (self.root / "sdk.tgz").write_text("not a tar archive")
        result = subprocess.run(["bash", "tools/test-mobile-package.sh", "sdk.tgz"], cwd=self.root, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.staging.is_symlink())
        self.assertTrue((self.staging / "original").is_file())
        self.assertEqual(list((self.root / "build/mobile-package").glob("consumer-check.*")), [])


if __name__ == "__main__":
    unittest.main()
