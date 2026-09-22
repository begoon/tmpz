package dev.abc.server

import dev.abc.server.proto.ping
import dev.abc.server.proto.request
import io.ktor.client.call.body
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.plugins.websocket.WebSockets
import io.ktor.client.plugins.websocket.webSocket
import io.ktor.client.request.get
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.HttpStatusCode
import io.ktor.http.contentType
import io.ktor.serialization.kotlinx.json.json
import io.ktor.server.testing.ApplicationTestBuilder
import io.ktor.server.testing.testApplication
import io.ktor.websocket.Frame
import java.net.URI
import kotlin.test.Test
import kotlin.test.assertContains
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

class RoutesTest {

    @Test
    fun `swagger UI serves a loadable specification for our endpoints`() = testApplication {
        serverUnderTest()
        val response = client.get("/swagger")
        assertEquals(HttpStatusCode.OK, response.status)
        assertTrue(response.contentType()?.match(ContentType.Text.Html) == true)
        val html = response.bodyAsText()
        assertContains(html, "SwaggerUIBundle")
        val specUrl =
            assertNotNull(Regex("""url\s*:\s*["']([^"']+)["']""").find(html)).groupValues[1]
        val specResponse =
            client.get(URI(response.call.request.url.toString()).resolve(specUrl).toString())
        assertEquals(HttpStatusCode.OK, specResponse.status)
        val spec = Json.parseToJsonElement(specResponse.bodyAsText()).jsonObject
        assertEquals("3.0.3", spec.getValue("openapi").jsonPrimitive.content)
        val paths = spec.getValue("paths").jsonObject
        for (path in listOf("/", "/health", "/stats", "/swagger", "/ws/{id}", "/ping/send")) {
            assertTrue(path in paths, "Missing endpoint $path")
        }
        assertContains(paths.getValue("/ws/{id}").toString(), "protobuf")
    }

    @Test
    fun `stats reads existing and externally added documents on every request`() = testApplication {
        val store = TestPingStore(mutableListOf(StoredPing("existing", "hello")))
        application { module(store) }
        assertContains(client.get("/stats").bodyAsText(), "<dt>MongoDB records</dt><dd>1</dd>")
        assertContains(client.get("/stats").bodyAsText(), "<dt>Pings since startup</dt><dd>0</dd>")
        store.save(StoredPing("another-server", "another ping"))
        assertContains(client.get("/stats").bodyAsText(), "<dt>MongoDB records</dt><dd>2</dd>")
    }

    private fun ApplicationTestBuilder.serverUnderTest() {
        application { module(TestPingStore()) }
    }

    @Test
    fun `root responds with html page wired to htmx`() = testApplication {
        serverUnderTest()

        val response = client.get("/")

        assertEquals(HttpStatusCode.OK, response.status)
        assertTrue(response.contentType()?.match(ContentType.Text.Html) == true)
        val html = response.bodyAsText()
        assertContains(html, "<script src=\"/assets/htmx/htmx.min.js\">")
        assertContains(html, "hx-get=\"/stats\" hx-trigger=\"load, every 5s\"")
        assertContains(html, "<button hx-get=\"/stats\" hx-target=\"#stats\"")
    }

    @Test
    fun `stats fragment shows ping count and resident memory`() = testApplication {
        serverUnderTest()
        val ws = createClient { install(WebSockets) }
        ws.webSocket("/ws/stats") {
            send(
                Frame.Binary(
                    fin = true,
                    data = request { ping = ping { message = "x" } }.toByteArray(),
                )
            )
            incoming.receive()
        }

        val response = client.get("/stats")

        assertEquals(HttpStatusCode.OK, response.status)
        assertTrue(response.contentType()?.match(ContentType.Text.Html) == true)
        val html = response.bodyAsText()
        assertContains(html, "<dt>MongoDB records</dt><dd>1</dd>")
        assertContains(html, "<dt>Pings since startup</dt><dd>1</dd>")
        assertTrue(Regex("<dd>\\d+\\.\\d MB</dd>").containsMatchIn(html), html)
    }

    @Test
    fun `htmx script is served from assets`() = testApplication {
        serverUnderTest()

        val response = client.get("/assets/htmx/htmx.min.js")

        assertEquals(HttpStatusCode.OK, response.status)
        assertTrue(response.contentType()?.match(ContentType.Text.JavaScript) == true)
        assertContains(response.bodyAsText(), "htmx")
    }

    @Test
    fun `health responds with UP status as json`() = testApplication {
        serverUnderTest()
        val client = createClient { install(ContentNegotiation) { json() } }

        val response = client.get("/health")

        assertEquals(HttpStatusCode.OK, response.status)
        assertTrue(response.contentType()?.match(ContentType.Application.Json) == true)
        assertEquals(Health(status = "UP"), response.body<Health>())
    }

    @Test
    fun `unknown path responds with 404`() = testApplication {
        serverUnderTest()

        val response = client.get("/missing")

        assertEquals(HttpStatusCode.NotFound, response.status)
    }
}
