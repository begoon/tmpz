plugins {
    alias(libs.plugins.kotlin.jvm)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ktfmt)
    application
}

group = "dev.abc"

version = "0.1.0"

kotlin { jvmToolchain(17) }

// Sources generated from proto/protocol.proto by `just protobuf`; committed, so the build
// needs no protoc. Excluded from ktfmt, which would otherwise reformat them.
sourceSets {
    main {
        java.srcDir("src/main/generated/java")
        kotlin.srcDir("src/main/generated/kotlin")
    }
}

ktfmt {
    kotlinLangStyle()
    srcSetPathExclusionPattern.set(Regex(".*[\\\\/](build|generated)[\\\\/].*"))
}

application { mainClass.set("dev.abc.server.ApplicationKt") }

dependencies {
    implementation(libs.ktor.server.core)
    implementation(libs.ktor.server.netty)
    implementation(libs.ktor.server.content.negotiation)
    implementation(libs.ktor.serialization.json)
    implementation(libs.ktor.server.websockets)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.protobuf.kotlin)
    implementation(libs.logback.classic)

    testImplementation(kotlin("test"))
    testImplementation(libs.ktor.server.test.host)
    testImplementation(libs.ktor.client.content.negotiation)
    testImplementation(libs.ktor.client.websockets)
}

tasks.test {
    useJUnitPlatform()
    testLogging { events("passed", "failed", "skipped") }
}
