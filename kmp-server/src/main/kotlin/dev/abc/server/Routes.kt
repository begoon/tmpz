package dev.abc.server

import io.ktor.http.ContentType
import io.ktor.server.http.content.staticResources
import io.ktor.server.response.respond
import io.ktor.server.response.respondText
import io.ktor.server.routing.Route
import io.ktor.server.routing.get
import java.time.LocalTime
import java.time.format.DateTimeFormatter
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.Serializable

@Serializable data class Health(val status: String)

/** Dashboard page; the stats block is loaded and refreshed by htmx from [statsRoute]. */
fun Route.rootRoute() {
    get("/") { call.respondText(PAGE, ContentType.Text.Html) }
}

/** HTML fragment with the current ping count and resident memory, swapped into the page. */
fun Route.statsRoute(counter: PingCounter, pingStore: PingStore) {
    get("/stats") { call.respondText(statsFragment(counter, pingStore), ContentType.Text.Html) }
}

fun Route.healthRoute() {
    get("/health") { call.respond(Health(status = "UP")) }
}

/** Serves the vendored htmx script (see `just htmx`) at /assets/htmx/htmx.min.js. */
fun Route.assetsRoute() {
    staticResources("/assets/htmx", "assets/htmx")
}

private val TIME = DateTimeFormatter.ofPattern("HH:mm:ss")

internal suspend fun statsFragment(counter: PingCounter, pingStore: PingStore): String {
    val records =
        try {
            pingStore.count().toString()
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            "Unavailable"
        }
    val pings = counter.value
    val megabytes = ProcessMemory.rssBytes() / (1024.0 * 1024.0)
    return """
        <dl>
          <dt>Pings since startup</dt><dd>$pings</dd>
          <dt>MongoDB records</dt><dd>$records</dd>
          <dt>Resident memory</dt><dd>${"%.1f".format(megabytes)} MB</dd>
        </dl>
        <p class="updated">Updated at ${LocalTime.now().format(TIME)}</p>
        """
        .trimIndent()
}

private val PAGE =
    """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>kmp-server</title>
      <script src="/assets/htmx/htmx.min.js"></script>
      <script src="/assets/htmx/hx-ws.min.js"></script>
      <style>
        body { font-family: system-ui, sans-serif; max-width: 32rem; margin: 3rem auto; padding: 0 1rem; }
        dl { display: grid; grid-template-columns: max-content auto; gap: 0.5rem 1.5rem; }
        dt { color: #666; }
        dd { margin: 0; font-variant-numeric: tabular-nums; }
        .updated { color: #999; font-size: 0.85rem; }
        button { padding: 0.4rem 1rem; }
        section { margin-top: 2rem; border-top: 1px solid #ddd; padding-top: 1rem; }
        form { display: flex; gap: 0.5rem; flex-wrap: wrap; }
        label { flex-basis: 100%; }
        input { flex: 1; min-width: 0; padding: 0.5rem; font: inherit; }
        button:disabled { opacity: 0.5; }
      </style>
    </head>
    <body>
      <h1>kmp-server</h1>
      <div id="stats" hx-get="/stats" hx-trigger="load, every 5s" hx-swap="innerHTML">Loading…</div>
      <button hx-get="/stats" hx-target="#stats" hx-swap="innerHTML">Refresh</button>
      <section id="ping-ui" hx-ws:connect="/ui/pings" hx-target="#ping-result">
        <h2>Send a ping</h2>
        <p id="ping-connection" role="status">Connecting…</p>
        <form hx-ws:send>
          <label for="ping-message">Message</label>
          <input id="ping-message" name="message" value="Hello from the browser" autocomplete="off">
          <button id="ping-send" type="submit" disabled>Send ping</button>
        </form>
        <div id="ping-result" role="status" aria-live="polite">No pings sent yet.</div>
      </section>
      <script>
        const pingUi = document.getElementById('ping-ui');
        const pingButton = document.getElementById('ping-send');
        const pingConnection = document.getElementById('ping-connection');
        pingUi.addEventListener('htmx:ws:after:connection', () => {
          pingConnection.textContent = 'Connected';
          pingButton.disabled = false;
        });
        pingUi.addEventListener('htmx:ws:before:message:outgoing', () => {
          document.getElementById('ping-result').textContent = 'Sending…';
          pingButton.disabled = true;
        });
        pingUi.addEventListener('htmx:ws:after:message:incoming', () => {
          pingButton.disabled = false;
        });
        pingUi.addEventListener('htmx:ws:close', (event) => {
          pingConnection.textContent = event.detail.code === 1011
            ? 'Could not confirm the ping. Reconnecting…'
            : 'Disconnected. Reconnecting…';
          pingButton.disabled = true;
        });
        pingUi.addEventListener('htmx:ws:error', () => {
          pingConnection.textContent = 'Connection error. Waiting to reconnect…';
          pingButton.disabled = true;
        });
      </script>
    </body>
    </html>
    """
        .trimIndent()
