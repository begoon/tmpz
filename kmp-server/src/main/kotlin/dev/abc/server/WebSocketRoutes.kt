package dev.abc.server

import com.google.protobuf.InvalidProtocolBufferException
import dev.abc.server.proto.Request
import dev.abc.server.proto.Response
import dev.abc.server.proto.pong
import dev.abc.server.proto.response
import dev.abc.server.proto.status
import io.ktor.server.application.log
import io.ktor.server.routing.Route
import io.ktor.server.websocket.DefaultWebSocketServerSession
import io.ktor.server.websocket.webSocket
import io.ktor.websocket.CloseReason
import io.ktor.websocket.Frame
import io.ktor.websocket.close
import io.ktor.websocket.readBytes
import java.util.concurrent.atomic.AtomicInteger

/** Counts every Ping received since the application started, across all connections. */
class PingCounter {
    private val count = AtomicInteger()

    fun next(): Int = count.incrementAndGet()
}

/**
 * `/ws/{id}`: every binary frame is a [Request] and is answered with one [Response]. A frame that
 * is not a well-formed Request with a body closes the connection.
 */
fun Route.websocketRoute(counter: PingCounter) {
    webSocket("/ws/{id}") {
        val id = call.parameters["id"]
        for (frame in incoming) {
            val response =
                parseRequest(frame)?.let { request -> handle(id, request, counter) }
                    ?: run {
                        close(CloseReason(CloseReason.Codes.CANNOT_ACCEPT, "expected a Request"))
                        return@webSocket
                    }
            send(Frame.Binary(fin = true, data = response.toByteArray()))
        }
    }
}

private fun parseRequest(frame: Frame): Request? =
    if (frame is Frame.Binary) {
        try {
            Request.parseFrom(frame.readBytes())
        } catch (e: InvalidProtocolBufferException) {
            null
        }
    } else null

private fun DefaultWebSocketServerSession.handle(
    id: String?,
    request: Request,
    counter: PingCounter,
): Response? =
    when (request.bodyCase) {
        Request.BodyCase.PING -> {
            val n = counter.next()
            call.application.log.info("ws/$id ping #$n: ${request.ping.message}")
            response { pong = pong { this.n = n } }
        }
        Request.BodyCase.QUERY_STATUS ->
            response {
                status = status {
                    memory = ProcessMemory.rssBytes()
                    state = "ok"
                }
            }
        Request.BodyCase.BODY_NOT_SET,
        null -> null
    }
