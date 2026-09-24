plugins {
    java
    kotlin("jvm")
    id("me.champeau.jmh") version Versions.jmhPlugin
}

dependencies {
    jmh(project(":shared"))
    jmh("${Realm.group}:library-base:${Realm.version}")
    jmh("org.openjdk.jmh:jmh-core:${Versions.jmh}")
    jmh("org.openjdk.jmh:jmh-generator-annprocess:${Versions.jmh}")
}

jmh {
    if (extra.has("jmh.include")) {
        includes.add(extra.get("jmh.include") as String)
    }
    resultFormat.set("json")
    resultsFile.set(file("build/reports/benchmarks.json"))
}

kotlin {
    jvmToolchain(17)
}
