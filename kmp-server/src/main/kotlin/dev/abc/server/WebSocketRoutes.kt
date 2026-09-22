package dev.abc.server

import com.google.protobuf.InvalidProtocolBufferException
import dev.abc.server.proto.Request
import dev.abc.server.proto.Response
import dev.abc.server.proto.ping
import dev.abc.server.proto.pong
import dev.abc.server.proto.request
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
import io.ktor.websocket.readText
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive

/** Counts received pings across connections for this application run. */
class PingCounter {
    private val count = AtomicInteger()
    val value: Int
        get() = count.get()

    fun next(): Int = count.incrementAndGet()
}

/** htmx sends JSON form values and swaps the HTML reply into the dashboard. */
fun Route.browserPingRoute(counter: PingCounter, pingStore: PingStore) {
    webSocket("/ui/pings") {
        for (frame in incoming) {
            val message =
                try {
                    val values =
                        (frame as? Frame.Text)?.readText()?.let { Json.parseToJsonElement(it) }
                    ((values as? JsonObject)?.get("message") as? JsonPrimitive)
                        ?.takeIf { it.isString }
                        ?.content
                } catch (e: SerializationException) {
                    null
                }
            if (message == null) {
                send(Frame.Text("<p>Please send a text message.</p>"))
                continue
            }
            val result =
                handle(
                    "browser",
                    request { ping = ping { this.message = message } },
                    counter,
                    pingStore,
                ) ?: return@webSocket
            send(
                Frame.Text(
                    "<p>Pong: n=${result.pong.n} — saved to MongoDB.</p>" +
                        "<hx-partial hx-target=\"#stats\">${statsFragment(counter, pingStore)}</hx-partial>"
                )
            )
        }
    }
}

/**
 * `/ws/{id}`: every binary frame is a [Request] and is answered with one [Response]. A frame that
 * is not a well-formed Request with a body closes the connection.
 */
fun Route.websocketRoute(counter: PingCounter, pingStore: PingStore) {
    webSocket("/ws/{id}") {
        val id = requireNotNull(call.parameters["id"])
        for (frame in incoming) {
            val request = parseRequest(frame)
            if (request == null || request.bodyCase == Request.BodyCase.BODY_NOT_SET) {
                close(CloseReason(CloseReason.Codes.CANNOT_ACCEPT, "expected a Request"))
                return@webSocket
            }
            val response = handle(id, request, counter, pingStore) ?: return@webSocket
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

private suspend fun DefaultWebSocketServerSession.handle(
    id: String,
    request: Request,
    counter: PingCounter,
    pingStore: PingStore,
): Response? {
    return when (request.bodyCase) {
        Request.BodyCase.PING -> {
            val n = counter.next()
            try {
                pingStore.save(StoredPing(id, request.ping.message))
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                call.application.log.error("Failed to save ws/$id ping", e)
                close(
                    CloseReason(
                        CloseReason.Codes.INTERNAL_ERROR,
                        "failed to save ping",
                    )
                )
                return null
            }
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
}
