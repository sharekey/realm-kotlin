/*
 * Copyright 2020 Realm Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
plugins {
    kotlin("jvm")
    `java-gradle-plugin`
    id("com.gradle.plugin-publish") version Versions.gradlePluginPublishPlugin
    id("realm-publisher")
}

dependencies {
    compileOnly(kotlin("gradle-plugin"))
}

val mavenPublicationName = "gradlePlugin"

fun createMarkerArtifact(): Boolean {
    val value = properties.getOrDefault("generatePluginArtifactMarker", "false") as String
    return value.toBoolean()
}

pluginBundle {
    website = Realm.projectUrl
    vcsUrl = Realm.SCM.url
    tags = listOf("MongoDB", "Realm", "Database", "Kotlin", "Mobile", "Multiplatform", "Android", "KMM")

    mavenCoordinates {
        groupId = Realm.group
        artifactId = Realm.gradlePluginId
        version = Realm.version
    }
}

gradlePlugin {
    plugins {
        create("RealmPlugin") {
            id = Realm.pluginPortalId
            displayName = "Sharekey Realm Kotlin Plugin"
            description = "Gradle plugin for the Realm Kotlin SDK, supporting Android and Multiplatform. " +
                "Realm is a mobile database: Build better apps faster."
            implementationClass = "io.realm.kotlin.gradle.RealmPlugin"
        }
        isAutomatedPublishing = createMarkerArtifact()
    }
}

realmPublish {
    pom {
        name = "Gradle Plugin"
        description = "Gradle plugin for Realm Kotlin. Realm is a mobile database: Build better apps faster."
    }
}

publishing {
    publications {
        register<MavenPublication>(mavenPublicationName) {
            artifactId = Realm.gradlePluginId
            from(components["java"])
        }
    }
}

java {
    withSourcesJar()
    withJavadocJar()
    sourceCompatibility = Versions.sourceCompatibilityVersion
    targetCompatibility = Versions.targetCompatibilityVersion
}

// Make version information available at runtime
val versionDirectory = "$buildDir/generated/source/version/"
sourceSets {
    main {
        java.srcDir(versionDirectory)
    }
}

// Task to generate the Gradle plugin runtime version constant
val versionConstants: Task = tasks.create("versionConstants") {
    inputs.property("version", project.version)
    inputs.property("group", project.group)
    val outputDir = file(versionDirectory)
    outputs.dir(outputDir)

    doLast {
        val versionFile = file("$outputDir/io/realm/kotlin/gradle/version.kt")
        versionFile.parentFile.mkdirs()
        versionFile.writeText(
            """
            // Generated file. Do not edit!
            package io.realm.kotlin.gradle
            internal const val PLUGIN_VERSION = "${project.version}"
            internal const val PLUGIN_GROUP = "${project.group}"
            """.trimIndent()
        )
    }
}

tasks.getByName("compileKotlin").dependsOn(versionConstants)
tasks.getByName("sourcesJar").dependsOn(versionConstants)
afterEvaluate {
    tasks.getByName("publishPluginJar").dependsOn(versionConstants)
}
