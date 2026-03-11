plugins {
    id("org.jetbrains.intellij") version "1.17.3"
    kotlin("jvm") version "1.9.22"
}

group = "ai.motadata"
version = "0.1.0"

repositories {
    mavenCentral()
}

intellij {
    version.set("2023.3")
    type.set("IC") // IntelliJ IDEA Community
    plugins.set(listOf("Git4Idea"))
}

dependencies {
    implementation(kotlin("stdlib"))
    implementation("com.google.code.gson:gson:2.10.1")
    testImplementation(kotlin("test"))
    testImplementation("org.mockito:mockito-core:5.11.0")
    testImplementation("org.mockito.kotlin:mockito-kotlin:5.2.1")
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.2")
}

tasks.test {
    useJUnitPlatform()
}

kotlin {
    jvmToolchain(17)
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

