package dev.abc.server

import java.io.File
import java.lang.ProcessHandle

/** Resident set size of this JVM process in bytes, or 0 when the platform gives no answer. */
object ProcessMemory {
    private val pageSize: Long by lazy { runCommand("getconf", "PAGESIZE")?.toLongOrNull() ?: 4096 }

    fun rssBytes(): Long = fromProc() ?: fromPs() ?: 0

    /** Linux: second field of /proc/self/statm is the number of resident pages. */
    private fun fromProc(): Long? = runCatching {
        File("/proc/self/statm").readText().split(' ')[1].toLong() * pageSize
    }
        .getOrNull()

    /** Elsewhere (macOS, BSD): ps reports the resident set size in kilobytes. */
    private fun fromPs(): Long? =
        runCommand("ps", "-o", "rss=", "-p", ProcessHandle.current().pid().toString())
            ?.toLongOrNull()
            ?.times(1024)

    private fun runCommand(vararg command: String): String? = runCatching {
        val process = ProcessBuilder(*command).redirectErrorStream(true).start()
        val output = process.inputStream.bufferedReader().readText().trim()
        if (process.waitFor() == 0) output else null
    }
        .getOrNull()
}
