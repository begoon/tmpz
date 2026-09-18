package dev.abc.server

import io.ktor.server.application.Application
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty

fun main() {
    val port = System.getenv("PORT")?.toIntOrNull() ?: 8080
    embeddedServer(
            Netty,
            port = port,
            host = "0.0.0.0",
            module = Application::module,
        )
        .start(wait = true)
}
