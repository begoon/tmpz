package dev.abc.server

import io.ktor.http.ContentType
import io.ktor.server.http.content.staticResources
import io.ktor.server.response.respond
import io.ktor.server.response.respondText
import io.ktor.server.routing.Route
import io.ktor.server.routing.get
import java.time.LocalTime
import java.time.format.DateTimeFormatter
import kotlinx.serialization.Serializable

@Serializable data class Health(val status: String)

/** Dashboard page; the stats block is loaded and refreshed by htmx from [statsRoute]. */
fun Route.rootRoute() {
    get("/") { call.respondText(PAGE, ContentType.Text.Html) }
}

/** HTML fragment with the current ping count and resident memory, swapped into the page. */
fun Route.statsRoute(counter: PingCounter) {
    get("/stats") { call.respondText(statsFragment(counter.value), ContentType.Text.Html) }
}

fun Route.healthRoute() {
    get("/health") { call.respond(Health(status = "UP")) }
}

/** Serves the vendored htmx script (see `just htmx`) at /assets/htmx/htmx.min.js. */
fun Route.assetsRoute() {
    staticResources("/assets/htmx", "assets/htmx")
}

private val TIME = DateTimeFormatter.ofPattern("HH:mm:ss")

private fun statsFragment(pings: Int): String {
    val megabytes = ProcessMemory.rssBytes() / (1024.0 * 1024.0)
    return """
        <dl>
          <dt>Pings received</dt><dd>$pings</dd>
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
      <style>
        body { font-family: system-ui, sans-serif; max-width: 32rem; margin: 3rem auto; padding: 0 1rem; }
        dl { display: grid; grid-template-columns: max-content auto; gap: 0.5rem 1.5rem; }
        dt { color: #666; }
        dd { margin: 0; font-variant-numeric: tabular-nums; }
        .updated { color: #999; font-size: 0.85rem; }
        button { padding: 0.4rem 1rem; }
      </style>
    </head>
    <body>
      <h1>kmp-server</h1>
      <div id="stats" hx-get="/stats" hx-trigger="load, every 5s" hx-swap="innerHTML">Loading…</div>
      <button hx-get="/stats" hx-target="#stats" hx-swap="innerHTML">Refresh</button>
    </body>
    </html>
    """
        .trimIndent()
