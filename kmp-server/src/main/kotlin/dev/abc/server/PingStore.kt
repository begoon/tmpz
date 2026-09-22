package dev.abc.server

import com.mongodb.ReadPreference
import com.mongodb.WriteConcern
import com.mongodb.kotlin.client.coroutine.MongoClient
import io.github.cdimascio.dotenv.dotenv
import io.ktor.server.application.Application
import io.ktor.server.application.ApplicationStopped
import java.time.Instant
import java.util.Date
import org.bson.Document

data class StoredPing(
    val clientId: String,
    val message: String,
    val receivedAt: Instant = Instant.now(),
)

interface PingStore {
    suspend fun save(ping: StoredPing)

    suspend fun count(): Long
}

/** One shared client/connection pool per application, closed when the server stops. */
fun Application.mongoPingStore(): PingStore {
    val uri = dotenv { ignoreIfMissing = true }["MONGODB_URI"]
    require(!uri.isNullOrBlank()) { "Set MONGODB_URI in the environment or .env" }
    val client = MongoClient.create(uri)
    monitor.subscribe(ApplicationStopped) { client.close() }
    val pings =
        client
            .getDatabase("kmp")
            .getCollection<Document>("pings")
            .withReadPreference(ReadPreference.primary())
            .withWriteConcern(WriteConcern.ACKNOWLEDGED)
    return object : PingStore {
        override suspend fun save(ping: StoredPing) {
            pings.insertOne(
                Document("clientId", ping.clientId)
                    .append("message", ping.message)
                    .append("receivedAt", Date.from(ping.receivedAt))
            )
        }

        override suspend fun count(): Long = pings.countDocuments()
    }
}
