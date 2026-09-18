package dev.abc.server

import io.ktor.server.response.respond
import io.ktor.server.response.respondText
import io.ktor.server.routing.Route
import io.ktor.server.routing.get
import kotlinx.serialization.Serializable

@Serializable data class Health(val status: String)

fun Route.rootRoute() {
    get("/") { call.respondText("ok") }
}

fun Route.healthRoute() {
    get("/health") { call.respond(Health(status = "UP")) }
}
