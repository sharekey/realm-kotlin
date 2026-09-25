import org.jetbrains.kotlin.gradle.tasks.KotlinCompilationTask

plugins {
    kotlin("multiplatform")
    id("com.android.library")
    id("com.sharekey.realm.kotlin")
}

version = "1.0"

kotlin {
    jvmToolchain(17)
    jvm()
    androidTarget()

    sourceSets {
        val commonMain by getting
        val commonTest by getting
        val androidMain by getting {
            dependencies {
                implementation("${rootProject.extra["realmGroup"]}:library-base:${rootProject.ext["realmVersion"]}")
            }
        }
        val androidInstrumentedTest by getting
        val jvmMain by getting
    }
}

android {
    namespace = "io.realm.sample.minandroidsample"
    compileSdk = 35
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    defaultConfig {
        minSdk = 21
    }
}

tasks.withType<KotlinCompilationTask<*>>().configureEach {
    compilerOptions {
        freeCompilerArgs.add("-Xexpect-actual-classes")
    }
}
