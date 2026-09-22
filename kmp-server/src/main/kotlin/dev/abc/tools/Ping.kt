package dev.abc.tools

import dev.abc.server.proto.Response
import dev.abc.server.proto.ping
import dev.abc.server.proto.request
import io.ktor.client.HttpClient
import io.ktor.client.engine.cio.CIO
import io.ktor.client.plugins.websocket.WebSockets
import io.ktor.client.plugins.websocket.webSocket
import io.ktor.websocket.Frame
import io.ktor.websocket.readBytes
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout

fun main(args: Array<String>) = runBlocking {
    val message = args.getOrNull(0) ?: "hello"
    val port = System.getenv("PORT")?.toIntOrNull() ?: 8080
    val url = args.getOrNull(1)?.takeIf { it.isNotBlank() } ?: "ws://localhost:$port/ws/just-ping"

    HttpClient(CIO) { install(WebSockets) }
        .use { client ->
            withTimeout(10_000) {
                client.webSocket(url) {
                    val ping = request { ping = ping { this.message = message } }
                    send(Frame.Binary(fin = true, data = ping.toByteArray()))
                    val frame = incoming.receive()
                    check(frame is Frame.Binary) { "Expected a binary protobuf response" }
                    val response = Response.parseFrom(frame.readBytes())
                    check(response.hasPong()) { "Expected Pong, received ${response.bodyCase}" }
                    println("Pong: n=${response.pong.n}")
                }
            }
        }
}
