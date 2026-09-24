#!/usr/bin/env python3
"""Package the staged Android/macOS JVM SDK as a Yarn-installable Maven repository."""

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUP = "com.sharekey.realm.kotlin"
MODULES = (
    "cinterop", "cinterop-android", "cinterop-jvm", "gradle-plugin", "jni-swig-stub",
    "library-base", "library-base-android", "library-base-jvm", "plugin-compiler",
)
ABIS = ("arm64-v8a", "armeabi-v7a", "x86", "x86_64")


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def sdk_version():
    config = (ROOT / "buildSrc/src/main/kotlin/Config.kt").read_text()
    version = re.search(r'const val version = "([^"]+)"', config).group(1)
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+-sharekey\.[0-9]+", version):
        raise ValueError(f"Expected an immutable Sharekey release version, found {version}")
    return version


def verify_elf(content, name):
    if content[:4] != b"\x7fELF" or content[5] != 1:
        raise ValueError(f"Unexpected ELF format: {name}")
    is_64 = content[4] == 2
    offset = struct.unpack_from("<Q" if is_64 else "<I", content, 32 if is_64 else 28)[0]
    entry_size, count = struct.unpack_from("<HH", content, 54 if is_64 else 42)
    loads = 0
    for index in range(count):
        start = offset + index * entry_size
        if struct.unpack_from("<I", content, start)[0] == 1:
            loads += 1
            alignment = struct.unpack_from("<Q" if is_64 else "<I", content, start + (48 if is_64 else 28))[0]
            if alignment < 16384:
                raise ValueError(f"{name} is not aligned for 16 KB pages")
    if not loads:
        raise ValueError(f"No ELF load segments: {name}")


def verify_source():
    if git("status", "--porcelain", "--untracked-files=all", "--ignore-submodules=none"):
        raise ValueError("Commit or remove modified and untracked SDK/Core sources before packaging")
    source_commit = git("rev-parse", "HEAD")
    core_commit = git("rev-parse", "HEAD:packages/external/core")
    if git("-C", "packages/external/core", "rev-parse", "HEAD") != core_commit:
        raise ValueError("Realm Core checkout does not match the pinned gitlink")
    if git("-C", "packages/external/core", "status", "--porcelain", "--untracked-files=all", "--ignore-submodules=none"):
        raise ValueError("Realm Core has modified or untracked sources")
    return source_commit, core_commit


def pack(output):
    version = sdk_version()
    source_commit, core_commit = verify_source()
    tag = os.environ.get("GITHUB_REF", "")
    if tag.startswith("refs/tags/") and tag != f"refs/tags/v{version}":
        raise ValueError("Release tag and SDK version differ")

    output.mkdir(parents=True, exist_ok=True)
    tarball_name = f"sharekey-realm-kotlin-{version}.tgz"
    if (output / tarball_name).exists():
        raise ValueError(f"Refusing to replace {output / tarball_name}")
    source = ROOT / "packages/build/m2-buildrepo" / GROUP.replace(".", "/")
    with tempfile.TemporaryDirectory(prefix="realm-mobile-") as temporary:
        package = Path(temporary) / "package"
        repository = package / "maven" / GROUP.replace(".", "/")
        for module in MODULES:
            directory = source / module / version
            prefix = f"{module}-{version}"
            pom = ET.parse(directory / f"{prefix}.pom").getroot()
            ns = {"m": "http://maven.apache.org/POM/4.0.0"}
            gav = tuple(pom.findtext(f"m:{key}", namespaces=ns) for key in ("groupId", "artifactId", "version"))
            if gav != (GROUP, module, version):
                raise ValueError(f"Unexpected POM coordinates: {gav}")
            for dependency in pom.findall(".//m:dependency", ns):
                group = dependency.findtext("m:groupId", namespaces=ns)
                if group in {"io.realm.kotlin", "com.infomaniak.realm.kotlin"}:
                    raise ValueError(f"Upstream SDK dependency remains in {module}")
                if group == GROUP:
                    artifact = dependency.findtext("m:artifactId", namespaces=ns)
                    dep_version = dependency.findtext("m:version", namespaces=ns)
                    if artifact not in MODULES or dep_version != version:
                        raise ValueError(f"SDK dependency missing from bundle: {artifact}:{dep_version}")
            destination = repository / module / version
            destination.mkdir(parents=True)
            for file in sorted(directory.iterdir()):
                if file.suffix in {".aar", ".jar", ".module", ".pom"}:
                    shutil.copyfile(file, destination / file.name)
            metadata = json.loads((destination / f"{prefix}.module").read_text())
            component = metadata["component"]
            if component["group"] != GROUP or component["version"] != version:
                raise ValueError(f"Unexpected Gradle component in {module}")
            for variant in metadata["variants"]:
                for dependency in variant.get("dependencies", []):
                    if dependency["group"] == GROUP and (
                        dependency["module"] not in MODULES or dependency["version"].get("requires") != version
                    ):
                        raise ValueError(f"SDK dependency missing from bundle: {dependency}")
                for file in variant.get("files", []):
                    if Path(file["url"]).name != file["url"]:
                        raise ValueError(f"Unexpected artifact path: {file['url']}")
                    content = (destination / file["url"]).read_bytes()
                    if len(content) != file["size"] or hashlib.sha512(content).hexdigest() != file["sha512"]:
                        raise ValueError(f"Artifact does not match Gradle metadata: {file['url']}")
            if not (destination / f"{prefix}-sources.jar").is_file():
                raise ValueError(f"Missing source artifact for {module}")

        native_hashes = {}
        aar = repository / "cinterop-android" / version / f"cinterop-android-{version}.aar"
        with zipfile.ZipFile(aar) as archive:
            natives = {name for name in archive.namelist() if name.endswith("/librealmc.so")}
            if natives != {f"jni/{abi}/librealmc.so" for abi in ABIS}:
                raise ValueError("Android publication must contain all four Realm ABIs")
            for name in sorted(natives):
                content = archive.read(name)
                verify_elf(content, name)
                native_hashes[name] = hashlib.sha256(content).hexdigest()
        jvm = repository / "cinterop-jvm" / version / f"cinterop-jvm-{version}.jar"
        with zipfile.ZipFile(jvm) as archive:
            native_hashes["jni/macos/librealmc.dylib"] = hashlib.sha256(
                archive.read("jni/macos/librealmc.dylib")
            ).hexdigest()
        plugin = repository / "gradle-plugin" / version / f"gradle-plugin-{version}.jar"
        with zipfile.ZipFile(plugin) as archive:
            archive.getinfo(f"META-INF/gradle-plugins/{GROUP}.properties")

        shutil.copyfile(ROOT / "LICENSE", package / "LICENSE")
        licenses = package / "licenses"
        licenses.mkdir()
        for name in ("LICENSE", "THIRD-PARTY-NOTICES"):
            shutil.copyfile(ROOT / "packages/external/core" / name, licenses / f"realm-core-{name}")
        manifest = {
            "name": "@sharekey/realm-kotlin",
            "version": version,
            "private": True,
            "description": "Prebuilt Sharekey Realm Kotlin Maven repository for the mobile Android app",
            "license": "Apache-2.0",
            "repository": {"type": "git", "url": "https://github.com/sharekey/realm-kotlin.git"},
            "files": ["maven", "licenses", "provenance.json", "SHA256SUMS", "README.md"],
        }
        (package / "package.json").write_text(json.dumps(manifest, indent=2) + "\n")
        provenance = {
            "group": GROUP, "version": version,
            "kotlin": re.search(r'const val kotlin = "([^"]+)"', (ROOT / "buildSrc/src/main/kotlin/Config.kt").read_text()).group(1),
            "coreCommit": core_commit,
            "sourceCommit": source_commit, "modules": list(MODULES), "androidAbis": list(ABIS),
            "nativeJvmPlatforms": ["macos"], "nativeSha256": native_hashes,
            "workflowRun": os.environ.get("GITHUB_RUN_ID"),
            "sourceRepository": "https://github.com/sharekey/realm-kotlin",
        }
        (package / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
        (package / "README.md").write_text(
            f"# Sharekey Realm Kotlin {version}\n\n"
            "This package contains a prebuilt Maven repository, not JavaScript runtime code.\n"
            "Install its exact GitHub Release URL with Yarn, then use its `maven/` directory\n"
            "as an exclusive Gradle repository for `com.sharekey.realm.kotlin`.\n\n"
            "Scope: Android (four ABIs) and macOS JVM native runtime. Linux/Windows JVM and\n"
            "Kotlin/Native Apple SDK publications are not included. Root KMP metadata retains\n"
            "upstream Apple variant declarations; those variants are outside this bundle.\n"
            "Realm JS and RealmSwift are separate dependencies.\n\n"
            f"Source: https://github.com/sharekey/realm-kotlin/tree/{source_commit}\n\n"
            "See `provenance.json`, `SHA256SUMS`, `LICENSE` and `licenses/` for provenance and notices.\n"
        )
        files = sorted(path for path in package.rglob("*") if path.is_file())
        (package / "SHA256SUMS").write_text("".join(
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(package).as_posix()}\n"
            for path in files
        ))
        subprocess.run(
            ["npm", "pack", "--ignore-scripts", "--pack-destination", str(output.resolve())],
            cwd=package, check=True,
        )
    tarball = output / tarball_name
    digest = hashlib.sha256(tarball.read_bytes()).hexdigest()
    (output / f"{tarball_name}.sha256").write_text(f"{digest}  {tarball_name}\n")
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"Packed {tarball_name}: SHA-256 {digest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--version", action="store_true", help="Print the source SDK version")
    mode.add_argument("--check-source", action="store_true", help="Verify the clean SDK/Core checkout before building")
    parser.add_argument("--output", type=Path, default=ROOT / "build/mobile-package")
    arguments = parser.parse_args()
    try:
        if arguments.version:
            print(sdk_version())
        elif arguments.check_source:
            verify_source()
        else:
            pack(arguments.output)
    except (OSError, ValueError, KeyError, ET.ParseError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Mobile package failed: {error}\n")
