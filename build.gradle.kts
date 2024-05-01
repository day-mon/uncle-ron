import org.jetbrains.kotlin.gradle.plugin.mpp.pm20.util.archivesName

group = "org.github.daymon"
version = "1.0"


plugins {
    kotlin("jvm") version "1.9.23"
    kotlin("plugin.serialization") version "1.9.22"
    application
    id("com.github.johnrengelman.shadow") version "7.1.1"
}

application {
    mainClass.set("org.github.daymon.MainKt")
}


shadow {
    archivesName = "UncleRon.jar"
}


repositories {
    mavenCentral()
    maven(url = "https://jitpack.io")
}

// create a tasks that cleans then shadowJars
tasks.create("build-jar") {
    dependsOn("clean")
    dependsOn("shadowJar")
}

dependencies {
    implementation("net.dv8tion:JDA:5.0.0-beta.22")
    implementation("club.minnced:jda-ktx:0.11.0-beta.20")
    implementation("io.github.freya022:BotCommands:3.0.0-alpha.12")
    implementation("ch.qos.logback:logback-classic:1.4.14")
    implementation("com.github.crazzyghost:alphavantage-java:1.7.0")
    implementation("io.ktor:ktor-client-core:2.3.10")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.3")
    implementation("io.ktor:ktor-client-content-negotiation:2.3.10")
    implementation("io.ktor:ktor-serialization-kotlinx-json:2.3.10")
    implementation("io.ktor:ktor-client-cio:2.3.10")
    implementation("de.sfuhrm:YahooFinanceAPI:3.16.4")
}


tasks.test {
    useJUnitPlatform()
}
kotlin {
    jvmToolchain(17)
}