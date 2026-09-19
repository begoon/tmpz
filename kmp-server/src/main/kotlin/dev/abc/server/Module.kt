package dev.abc.server

import io.ktor.serialization.kotlinx.json.json
import io.ktor.server.application.Application
import io.ktor.server.application.install
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation
import io.ktor.server.routing.routing
import io.ktor.server.websocket.WebSockets

fun Application.module() {
    install(ContentNegotiation) { json() }
    install(WebSockets)
    val pingCounter = PingCounter()
    routing {
        rootRoute()
        healthRoute()
        websocketRoute(pingCounter)
    }
}
