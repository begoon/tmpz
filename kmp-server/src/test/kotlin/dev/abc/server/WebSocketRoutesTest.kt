package dev.abc.server

import dev.abc.server.proto.Request
import dev.abc.server.proto.Response
import dev.abc.server.proto.ping
import dev.abc.server.proto.queryStatus
import dev.abc.server.proto.request
import io.ktor.client.HttpClient
import io.ktor.client.plugins.websocket.DefaultClientWebSocketSession
import io.ktor.client.plugins.websocket.WebSockets
import io.ktor.client.plugins.websocket.webSocket
import io.ktor.client.request.get
import io.ktor.http.HttpStatusCode
import io.ktor.server.testing.ApplicationTestBuilder
import io.ktor.server.testing.testApplication
import io.ktor.websocket.CloseReason
import io.ktor.websocket.Frame
import io.ktor.websocket.readBytes
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertTrue

class WebSocketRoutesTest {

    private fun ApplicationTestBuilder.wsClient(): HttpClient {
        application { module() }
        return createClient { install(WebSockets) }
    }

    private suspend fun DefaultClientWebSocketSession.send(request: Request) =
        send(Frame.Binary(fin = true, data = request.toByteArray()))

    private suspend fun DefaultClientWebSocketSession.sendPing(message: String) =
        send(request { ping = ping { this.message = message } })

    private suspend fun DefaultClientWebSocketSession.receive(): Response {
        val frame = incoming.receive()
        assertIs<Frame.Binary>(frame)
        return Response.parseFrom(frame.readBytes())
    }

    private suspend fun DefaultClientWebSocketSession.receivePong(): Int {
        val response = receive()
        assertEquals(Response.BodyCase.PONG, response.bodyCase)
        return response.pong.n
    }

    private suspend fun DefaultClientWebSocketSession.assertClosedAsNotAcceptable() {
        val reason = closeReason.await()
        assertEquals(CloseReason.Codes.CANNOT_ACCEPT.code, reason?.code)
    }

    @Test
    fun `ping is answered with pong number 1`() = testApplication {
        val client = wsClient()

        client.webSocket("/ws/first") {
            sendPing("hello")

            assertEquals(1, receivePong())
        }
    }

    @Test
    fun `pong numbers count pings across connections and ids`() = testApplication {
        val client = wsClient()

        client.webSocket("/ws/a") {
            sendPing("one")
            assertEquals(1, receivePong())
            sendPing("two")
            assertEquals(2, receivePong())
        }
        client.webSocket("/ws/b") {
            sendPing("three")
            assertEquals(3, receivePong())
        }
    }

    @Test
    fun `get status is answered with ok state and resident memory`() = testApplication {
        val client = wsClient()

        client.webSocket("/ws/s") {
            send(request { queryStatus = queryStatus {} })

            val response = receive()
            assertEquals(Response.BodyCase.STATUS, response.bodyCase)
            assertEquals("ok", response.status.state)
            assertTrue(response.status.memory > 0, "memory should be positive")
        }
    }

    @Test
    fun `status requests do not count as pings`() = testApplication {
        val client = wsClient()

        client.webSocket("/ws/s") {
            send(request { queryStatus = queryStatus {} })
            receive()
            sendPing("first ping")

            assertEquals(1, receivePong())
        }
    }

    @Test
    fun `text frame closes the connection as not acceptable`() = testApplication {
        val client = wsClient()

        client.webSocket("/ws/x") {
            send(Frame.Text("not a protobuf"))

            assertClosedAsNotAcceptable()
        }
    }

    @Test
    fun `malformed binary frame closes the connection as not acceptable`() = testApplication {
        val client = wsClient()

        client.webSocket("/ws/x") {
            // Field 1 declared as 5 bytes long, but the payload ends immediately
            send(Frame.Binary(fin = true, data = byteArrayOf(0x0A, 0x05)))

            assertClosedAsNotAcceptable()
        }
    }

    @Test
    fun `request without a body closes the connection as not acceptable`() = testApplication {
        val client = wsClient()

        client.webSocket("/ws/x") {
            send(request {})

            assertClosedAsNotAcceptable()
        }
    }

    @Test
    fun `plain http request to the websocket path is rejected`() = testApplication {
        val client = wsClient()

        val response = client.get("/ws/x")

        assertEquals(HttpStatusCode.NotFound, response.status)
    }
}
