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
import io.ktor.client.statement.bodyAsText
import io.ktor.http.HttpStatusCode
import io.ktor.server.testing.ApplicationTestBuilder
import io.ktor.server.testing.testApplication
import io.ktor.websocket.CloseReason
import io.ktor.websocket.Frame
import io.ktor.websocket.readBytes
import io.ktor.websocket.readText
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertContains
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertTrue

class WebSocketRoutesTest {

    @Test
    fun `pong count resets on restart while database records persist`() {
        val store = TestPingStore(mutableListOf(StoredPing("old-client", "existing ping")))
        for (expected in 2..3) {
            testApplication {
                val client = wsClient(store)
                client.webSocket("/ws/restarted") {
                    sendPing("new ping")
                    assertEquals(1, receivePong())
                }
                val html = client.get("/stats").bodyAsText()
                assertContains(html, "<dt>Pings since startup</dt><dd>1</dd>")
                assertContains(html, "<dt>MongoDB records</dt><dd>$expected</dd>")
            }
        }
    }

    @Test
    fun `count failure still allows pong and shows unavailable database count`() = testApplication {
        val saved = mutableListOf<StoredPing>()
        val store =
            object : PingStore {
                override suspend fun save(ping: StoredPing) {
                    saved.add(ping)
                }

                override suspend fun count(): Long = error("count unavailable")
            }
        val client = wsClient(store)
        client.webSocket("/ws/count-failure") {
            sendPing("saved and acknowledged")
            assertEquals(1, receivePong())
        }
        assertEquals(1, saved.size)
        val html = client.get("/stats").bodyAsText()
        assertContains(html, "<dt>Pings since startup</dt><dd>1</dd>")
        assertContains(html, "<dt>MongoDB records</dt><dd>Unavailable</dd>")
    }

    @Test
    fun `browser pings are saved and share the protobuf counter`() = testApplication {
        val saved = mutableListOf<StoredPing>()
        val client = wsClient(TestPingStore(saved))
        client.webSocket("/ping/send") {
            send(Frame.Text("""{"message":"<script>alert(1)</script>","headers":{}}"""))
            val html = (incoming.receive() as Frame.Text).readText()
            assertContains(html, "Pong: n=1")
            assertContains(html, "<hx-partial hx-target=\"#stats\">")
            assertContains(html, "<dt>Pings since startup</dt><dd>1</dd>")
            assertTrue(!html.contains("<script>"))
            assertEquals("browser", saved.single().clientId)
            assertEquals("<script>alert(1)</script>", saved.single().message)
        }
        client.webSocket("/ws/cli") {
            sendPing("second")
            assertEquals(2, receivePong())
        }
        assertEquals(2, saved.size)
    }

    @Test
    fun `invalid browser messages are rejected without saving and connection stays usable`() =
        testApplication {
            val saved = mutableListOf<StoredPing>()
            val client = wsClient(TestPingStore(saved))
            client.webSocket("/ping/send") {
                for (message in listOf("not json", "{}", "[]", """{"message":42}""")) {
                    send(Frame.Text(message))
                    assertContains(
                        (incoming.receive() as Frame.Text).readText(),
                        "Please send a text message",
                    )
                }
                assertTrue(saved.isEmpty())
                send(Frame.Text("""{"message":"hello"}"""))
                assertContains((incoming.receive() as Frame.Text).readText(), "Pong: n=1")
                assertEquals(1, saved.size)
            }
        }

    @Test
    fun `browser save failure closes without a success reply`() = testApplication {
        val client = wsClient(TestPingStore { error("database unavailable") })
        client.webSocket("/ping/send") {
            send(Frame.Text("""{"message":"hello"}"""))
            assertEquals(CloseReason.Codes.INTERNAL_ERROR.code, closeReason.await()?.code)
            for (frame in incoming) {
                assertTrue(frame !is Frame.Text, "A failed save must not report success")
            }
        }
    }

    private fun ApplicationTestBuilder.wsClient(
        pingStore: PingStore = TestPingStore()
    ): HttpClient {
        application { module(pingStore) }
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
    fun `every ping is saved before its pong and status is not saved`() = testApplication {
        val saved = mutableListOf<StoredPing>()
        val client = wsClient(TestPingStore(saved))
        val started = Instant.now()

        client.webSocket("/ws/a") {
            send(request { queryStatus = queryStatus {} })
            receive()
            assertTrue(saved.isEmpty())
            for (n in 1..2) {
                sendPing("message $n")
                assertEquals(n, receivePong())
                assertEquals(n, saved.size)
            }
        }
        client.webSocket("/ws/b") {
            sendPing("message 3")
            assertEquals(3, receivePong())
            assertEquals(3, saved.size)
        }
        assertEquals(listOf("a", "a", "b"), saved.map { it.clientId })
        assertEquals(listOf("message 1", "message 2", "message 3"), saved.map { it.message })
        assertTrue(saved.all { it.receivedAt >= started && it.receivedAt <= Instant.now() })
    }

    @Test
    fun `failed save closes with internal error without a pong`() = testApplication {
        val client = wsClient(TestPingStore { error("database unavailable") })
        client.webSocket("/ws/failure") {
            sendPing("not saved")
            assertEquals(CloseReason.Codes.INTERNAL_ERROR.code, closeReason.await()?.code)
            for (frame in incoming) {
                assertTrue(frame !is Frame.Binary, "A failed insert must not produce a pong")
            }
        }
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
