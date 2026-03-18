plugins {
    id("org.jetbrains.intellij") version "1.17.3"
    kotlin("jvm") version "2.2.0"
}

group = "ai.motadata"
version = "0.1.0"

repositories {
    mavenCentral()
}

intellij {
    version.set("2025.3")
    type.set("IU") // IntelliJ IDEA Ultimate (unified distribution)
    // Git4Idea not on compile classpath to avoid dvcs module; plugin.xml still <depends>Git4Idea</depends> for runtime
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

