plugins {
    id("org.jetbrains.intellij") version "1.17.3"
    kotlin("jvm") version "2.2.0"
}

group = "ai.motadata"
// Semver 0.MINOR.PATCH — bump MINOR (or PATCH) on each fix/rebuild you ship so the IDE shows a distinct version.
version = "0.2.2"

repositories {
    mavenCentral()
}

intellij {
    version.set("2025.3")
    type.set("IU") // IntelliJ IDEA Ultimate (unified distribution)
    // Git4Idea not on compile classpath to avoid dvcs module; plugin.xml still <depends>Git4Idea</depends> for runtime
}

// Default patched range was capped at 253.*; JetBrains Client / newer IDs need a higher until-build (e.g. JBC-261).
tasks.patchPluginXml {
    // Single source of truth: packaged plugin.xml gets this version (must match IDE “Plugins” list).
    version.set(project.version.toString())
    // Align floor with compile SDK (2025.3 → base build 253); raise ceiling for JetBrains Client 261+.
    sinceBuild.set("253")
    untilBuild.set("999.*")
}

dependencies {
    implementation("com.google.code.gson:gson:2.10.1")
    testImplementation(kotlin("test"))
    testImplementation("org.mockito:mockito-core:5.11.0")
    testImplementation("org.mockito.kotlin:mockito-kotlin:5.2.1")
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.2")
}

tasks.test {
    useJUnitPlatform()
    // Note: With IntelliJ 2025.3, the gradle-intellij-plugin can fail with "Index: 1, Size: 1"
    // in resolveIdeHomeVariable when running :test. RuntimeBridgeTest verifies availability
    // and error classification; validate manually on Windows or after upgrading to the
    // intellij-platform-gradle-plugin 2.x if needed.
}

tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile>().configureEach {
    compilerOptions.jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
}

tasks.withType<JavaCompile> {
    sourceCompatibility = "17"
    targetCompatibility = "17"
}

// Avoid buildSearchableOptions failure (Index: 1, Size: 1) with 2025.3; plugin has no searchable options
tasks.named("buildSearchableOptions") {
    enabled = false
}

// IntelliJ Platform Gradle Plugin names the packaged artifact task `buildPlugin`, not `buildInstall`.
tasks.register("buildInstall") {
    group = "intellij plugin"
    description =
        "Alias for buildPlugin. Produces build/distributions/*.zip — use Settings → Plugins → Install from Disk."
    dependsOn("buildPlugin")
}

