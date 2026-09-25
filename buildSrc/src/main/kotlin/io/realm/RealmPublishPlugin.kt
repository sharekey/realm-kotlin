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
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
 * or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package io.realm.kotlin

import Realm
import org.gradle.api.Action
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.publish.PublishingExtension
import org.gradle.api.publish.maven.MavenPublication
import org.gradle.api.publish.maven.plugins.MavenPublishPlugin
import org.gradle.kotlin.dsl.create
import org.gradle.kotlin.dsl.findByType
import org.gradle.kotlin.dsl.getByType
import org.gradle.kotlin.dsl.withType
import org.gradle.plugins.signing.SigningExtension
import org.gradle.plugins.signing.SigningPlugin
import java.io.File

// Custom options for POM configurations that might differ between Realm modules
open class PomOptions {
    open var name: String = ""
    open var description: String = ""
}

// Configure how the Realm module is published
open class RealmPublishExtensions {
    open var pom: PomOptions = PomOptions()
    open fun pom(action: Action<PomOptions>) {
        action.execute(pom)
    }
}

fun getPropertyValue(project: Project, propertyName: String, defaultValue: String = ""): String {
    if (project.hasProperty(propertyName)) {
        return project.property(propertyName) as String
    }
    val systemValue: String? = System.getenv(propertyName)
    return systemValue ?: defaultValue
}

// Stage Maven publications locally. Uploading a release is a separate, explicit operation.
class RealmPublishPlugin : Plugin<Project> {
    override fun apply(project: Project): Unit = project.run {
        // The root is an orchestrator, not a Maven artifact.
        if (project != project.rootProject) {
            configureSubProject(project, getPropertyValue(project, "signBuild").toBoolean())
            configureTestRepository(project)
        }
    }

    private fun configureTestRepository(project: Project) {
        val relativePathToTestRepository: String = getPropertyValue(project, "testRepository")
        val testRepository = File(project.rootProject.rootDir.absolutePath + File.separator + relativePathToTestRepository.replace("/", File.separator))
        if (relativePathToTestRepository.isNotEmpty()) {
            project.extensions.getByType<PublishingExtension>().apply {
                repositories {
                    maven {
                        name = "Test"
                        url = testRepository.toURI()
                    }
                }
            }
        }
    }

    private fun configureSubProject(project: Project, signBuild: Boolean) {
        with(project) {
            plugins.apply(SigningPlugin::class.java)
            plugins.apply(MavenPublishPlugin::class.java)

            // Create the RealmPublish plugin. It must evaluate after all other plugins as it modifies their output.
            // Only allow configuration from sub projects as the top-level project is just a placeholder
            extensions.create<RealmPublishExtensions>("realmPublish")

            afterEvaluate {
                project.extensions.findByType<RealmPublishExtensions>()?.run {
                    configurePom(project, pom)
                }
            }

            if (signBuild) {
                val signingKey = getPropertyValue(project, "REALM_SIGNING_KEY")
                val signingPassword = getPropertyValue(project, "REALM_SIGNING_PASSWORD")
                require(signingKey.isNotBlank()) {
                    "Signed publication requires REALM_SIGNING_KEY in the environment or Gradle user properties."
                }
                extensions.getByType<SigningExtension>().apply {
                    isRequired = true
                    useInMemoryPgpKeys(signingKey, signingPassword)
                    sign(project.extensions.getByType<PublishingExtension>().publications)
                }
            }
        }
    }

    private fun configurePom(project: Project, options: PomOptions) {
        project.extensions.getByType<PublishingExtension>().apply {
            publications.withType<MavenPublication>().all {
                pom {
                    name.set(options.name)
                    description.set(options.description)
                    url.set(Realm.projectUrl)
                    licenses {
                        license {
                            name.set(Realm.License.name)
                            url.set(Realm.License.url)
                        }
                    }
                    issueManagement {
                        system.set(Realm.IssueManagement.system)
                        url.set(Realm.IssueManagement.url)
                    }
                    scm {
                        connection.set(Realm.SCM.connection)
                        developerConnection.set(Realm.SCM.developerConnection)
                        url.set(Realm.SCM.url)
                    }
                    developers {
                        developers {
                            developer {
                                name.set(Realm.Developer.name)
                                id.set("sharekey")
                                url.set(Realm.projectUrl)
                                organization.set(Realm.Developer.organization)
                                organizationUrl.set(Realm.Developer.organizationUrl)
                            }
                        }
                    }
                }
            }
        }
    }
}
