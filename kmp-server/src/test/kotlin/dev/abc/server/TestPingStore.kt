package dev.abc.server

/** Database substitute shared across application instances in persistence tests. */
class TestPingStore(
    val pings: MutableList<StoredPing> = mutableListOf(),
    private val beforeSave: suspend () -> Unit = {},
) : PingStore {
    override suspend fun save(ping: StoredPing) {
        beforeSave()
        pings.add(ping)
    }

    override suspend fun count(): Long = pings.size.toLong()
}
