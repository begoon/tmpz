package dev.abc.server

import io.ktor.serialization.kotlinx.json.json
import io.ktor.server.application.Application
import io.ktor.server.application.install
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation
import io.ktor.server.plugins.swagger.swaggerUI
import io.ktor.server.routing.routing
import io.ktor.server.websocket.WebSockets

fun Application.module() {
    module(mongoPingStore())
}

fun Application.module(pingStore: PingStore) {
    install(ContentNegotiation) { json() }
    install(WebSockets)
    val pingCounter = PingCounter()
    routing {
        swaggerUI(path = "swagger", swaggerFile = "openapi/documentation.json")
        rootRoute()
        statsRoute(pingCounter, pingStore)
        healthRoute()
        assetsRoute()
        websocketRoute(pingCounter, pingStore)
        browserPingRoute(pingCounter, pingStore)
    }
}
