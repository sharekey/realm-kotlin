// This project can only build against local deployed artifacts
buildscript {
    val androidGradlePluginVersion = providers.gradleProperty("androidGradlePluginVersion").getOrElse("8.10.0")
    val realmConfig = file("${rootProject.rootDir.absolutePath}/../../buildSrc/src/main/kotlin/Config.kt")
        .readLines()
    for ((key, constant) in mapOf("realmVersion" to "version", "realmGroup" to "group")) {
        extra[key] = realmConfig.first { it.contains("const val $constant =") }
            .substringAfter("\"").substringBefore("\"")
    }

    repositories {
        maven(url = "file://${rootProject.rootDir.absolutePath}/../../packages/build/m2-buildrepo")
        gradlePluginPortal()
        google()
        mavenCentral()
        maven(url = "https://oss.sonatype.org/content/repositories/snapshots")
    }
    dependencies {
        classpath("com.android.tools.build:gradle:$androidGradlePluginVersion")
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:2.2.10")
        classpath("${rootProject.extra["realmGroup"]}:gradle-plugin:${rootProject.extra["realmVersion"]}")
    }
}

tasks.create("clean", Delete::class) {
    delete.add(rootProject.buildDir)
}

allprojects {
    repositories {
        maven(url = "file://${rootProject.rootDir.absolutePath}/../../packages/build/m2-buildrepo")
        google()
        mavenCentral()
        maven(url = "https://oss.sonatype.org/content/repositories/snapshots")
    }
}
