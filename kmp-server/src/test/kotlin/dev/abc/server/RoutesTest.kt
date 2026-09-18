package dev.abc.server

import io.ktor.client.call.body
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.get
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.HttpStatusCode
import io.ktor.http.contentType
import io.ktor.serialization.kotlinx.json.json
import io.ktor.server.testing.ApplicationTestBuilder
import io.ktor.server.testing.testApplication
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class RoutesTest {

    private fun ApplicationTestBuilder.serverUnderTest() {
        application { module() }
    }

    @Test
    fun `root responds with ok`() = testApplication {
        serverUnderTest()

        val response = client.get("/")

        assertEquals(HttpStatusCode.OK, response.status)
        assertEquals("ok", response.bodyAsText())
        assertTrue(response.contentType()?.match(ContentType.Text.Plain) == true)
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
