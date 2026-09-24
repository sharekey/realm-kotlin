"""Regression checks for source provenance and temporary consumer repositories."""

import hashlib
import importlib.util
import os
import shutil
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
