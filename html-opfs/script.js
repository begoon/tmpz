"use strict";
const $ = (id) => document.getElementById(id);
let directory;
let current = null;
let original = "";
let busy = false;
let ready = false;
function formatBytes(bytes) {
    if (bytes < 1024) {
        return `${bytes} B`;
    }
    if (bytes < 1048576) {
        return `${(bytes / 1024).toFixed(1)} KB`;
    }
    if (bytes < 1073741824) {
        return `${(bytes / 1048576).toFixed(1)} MB`;
    }
    return `${(bytes / 1073741824).toFixed(1)} GB`;
}
const isDirty = () => current !== null && $("content").value !== original;
function log(message, error = false) {
    const row = document.createElement("div");
    row.className = "log-entry" + (error ? " error" : "");
    const time = document.createElement("time");
    time.textContent = new Date().toLocaleTimeString([], { hour12: false });
    const text = document.createElement("span");
    text.textContent = message;
    row.append(time, text);
    $("log").append(row);
    while ($("log").children.length > 80) $("log").firstChild.remove();
    $("log").scrollTop = $("log").scrollHeight;
}
function updateControls() {
    for (const id of ["new", "sample"]) $(id).disabled = !ready || busy;
    for (const id of ["save", "download", "delete"]) $(id).disabled = !current || busy;
    $("content").disabled = !current || busy;
    $("dirty").textContent = isDirty() ? "● Unsaved" : current ? "Saved" : "";
    document.querySelectorAll(".file").forEach((button) => {
        button.disabled = busy;
    });
}
async function action(fn) {
    if (busy) return;
    busy = true;
    updateControls();
    try {
        await fn();
    } catch (error) {
        $("status").textContent = `${error.name}: ${error.message}`;
        log(`${error.name}: ${error.message}`, true);
    } finally {
        busy = false;
        updateControls();
    }
}
function animate() {
    $("diagram").classList.remove("active");
    void $("diagram").offsetWidth;
    $("diagram").classList.add("active");
}
function mayDiscard() {
    return !isDirty() || confirm("Discard the unsaved changes to this file?");
}
async function refresh() {
    const entries = [];
    for await (const [name, handle] of directory.entries()) {
        if (handle.kind === "file") entries.push({ name, file: await handle.getFile() });
    }
    entries.sort((a, b) => a.name.localeCompare(b.name));
    $("file-count").textContent = entries.length;
    $("lab-size").textContent = formatBytes(entries.reduce((sum, entry) => sum + entry.file.size, 0));
    $("file-list").replaceChildren();
    if (!entries.length) {
        const p = document.createElement("p");
        p.className = "empty";
        p.textContent = "A blank canvas. Create your first file or load an example to explore.";
        $("file-list").append(p);
    }
    for (const { name, file } of entries) {
        const button = document.createElement("button");
        button.className = "file" + (current === name ? " selected" : "");
        button.setAttribute("aria-pressed", String(current === name));
        button.title = name;
        const symbol = document.createElement("span");
        symbol.className = "file-symbol";
        symbol.textContent = "TXT";
        const info = document.createElement("span");
        info.className = "file-info";
        const title = document.createElement("span");
        title.className = "file-name";
        title.textContent = name;
        const size = document.createElement("span");
        size.className = "file-size";
        size.textContent = formatBytes(file.size);
        info.append(title, size);
        button.append(symbol, info);
        button.addEventListener("click", () => {
            if (current !== name && mayDiscard()) action(() => openFile(name));
        });
        $("file-list").append(button);
    }
    try {
        const estimate = await navigator.storage.estimate();
        $("usage").textContent = formatBytes(estimate.usage ?? 0);
        $("quota").textContent = estimate.quota
            ? `of ${formatBytes(estimate.quota)} estimated quota`
            : "Quota unavailable";
        $("usage-bar").style.width =
            `${estimate.quota ? Math.min(100, ((estimate.usage ?? 0) / estimate.quota) * 100) : 0}%`;
    } catch {
        $("usage").textContent = "—";
        $("quota").textContent = "Storage estimate unavailable";
    }
}
async function openFile(name) {
    const handle = await directory.getFileHandle(name);
    const file = await handle.getFile();
    if (file.size > 2 * 1024 * 1024) throw new Error("This text demo only opens files up to 2 MB.");
    const content = await file.text();
    current = name;
    original = content;
    $("content").value = content;
    $("filename").textContent = name;
    log(`getFileHandle(${JSON.stringify(name)}) → getFile() → text()`);
    $("status").textContent = `Read ${formatBytes(file.size)} from ${name}.`;
    animate();
    await refresh();
}
async function writeFile(name, content) {
    const handle = await directory.getFileHandle(name, { create: true });
    const stream = await handle.createWritable();
    try {
        await stream.write(content);
        await stream.close();
    } catch (error) {
        try {
            await stream.abort();
        } catch {}
        throw error;
    }
    log(`createWritable() → write(${new Blob([content]).size} bytes) → close()`);
    animate();
}
async function exists(name) {
    try {
        await directory.getFileHandle(name);
        return true;
    } catch (error) {
        if (error.name === "NotFoundError") return false;
        if (error.name === "TypeMismatchError") return true;
        throw error;
    }
}
$("content").addEventListener("input", updateControls);
$("new").addEventListener("click", () => {
    if (!mayDiscard()) return;
    $("new-form").reset();
    $("name-error").textContent = "";
    $("new-dialog").showModal();
    $("new-name").focus();
});
$("cancel-new").addEventListener("click", () => $("new-dialog").close());
$("new-form").addEventListener("submit", (event) => {
    event.preventDefault();
    action(async () => {
        const name = $("new-name").value.trim();
        if (!name || name === "." || name === ".." || /[\\/\u0000-\u001f]/.test(name)) {
            $("name-error").textContent = "Use a filename without slashes or control characters.";
            return;
        }
        if (await exists(name)) {
            $("name-error").textContent = "That name already exists. Choose another name.";
            return;
        }
        await writeFile(name, "");
        $("new-dialog").close();
        await openFile(name);
    });
});
$("sample").addEventListener("click", () => {
    if (!mayDiscard()) return;
    action(async () => {
        let name = "hello-opfs.txt",
            n = 2;
        while (await exists(name)) name = `hello-opfs-${n++}.txt`;
        await writeFile(
            name,
            "Hello from your private filesystem! 🌱\n\nThis is a real file stored in OPFS.\n\nTry this:\n  1. Replace this line with something worth keeping.\n  2. Click “Save to OPFS”.\n  3. Reload this page and open this file again.\n\nNo server. No upload. Just your browser.\n",
        );
        await openFile(name);
    });
});
$("save").addEventListener("click", () =>
    action(async () => {
        const content = $("content").value;
        await writeFile(current, content);
        original = content;
        await refresh();
        $("status").textContent = `Saved ${current}. Reload this page to check that it persists.`;
    }),
);
$("download").addEventListener("click", () =>
    action(async () => {
        const handle = await directory.getFileHandle(current);
        const file = await handle.getFile();
        const url = URL.createObjectURL(file);
        const link = document.createElement("a");
        link.href = url;
        link.download = current;
        document.body.append(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 10000);
        log("getFile() → download saved copy");
        $("status").textContent = "Downloaded the saved file. Unsaved editor changes are not included.";
    }),
);
$("delete").addEventListener("click", () => {
    if (!confirm(`Delete “${current}” from OPFS? This also discards any unsaved edits.`)) return;
    action(async () => {
        const name = current;
        await directory.removeEntry(name);
        log(`removeEntry(${JSON.stringify(name)})`);
        current = null;
        original = "";
        $("content").value = "";
        $("filename").textContent = "Select a file to begin";
        animate();
        await refresh();
        $("status").textContent = `Deleted ${name}.`;
    });
});
window.addEventListener("beforeunload", (event) => {
    if (isDirty() || busy) {
        event.preventDefault();
        event.returnValue = "";
    }
});
window.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        if (current && !busy) $("save").click();
    }
});
(async () => {
    try {
        if (!window.isSecureContext || !navigator.storage?.getDirectory)
            throw new Error(
                "OPFS needs a supported browser and HTTPS or localhost. Run “python3 -m http.server 8000” in this folder, then visit http://localhost:8000.",
            );
        const root = await navigator.storage.getDirectory();
        log("navigator.storage.getDirectory()");
        directory = await root.getDirectoryHandle("opfs-lab", { create: true });
        log('getDirectoryHandle("opfs-lab", { create: true })');
        ready = true;
        await refresh();
        $("connection").textContent = "OPFS CONNECTED";
        $("status").textContent = "Ready. Create a file, add an example, or open a saved file.";
    } catch (error) {
        ready = false;
        $("connection").textContent = "OPFS UNAVAILABLE";
        $("notice").hidden = false;
        $("notice").textContent = error.message;
        $("file-list").textContent = "";
        $("status").textContent = "Private storage could not be opened.";
        log(error.message, true);
    }
    updateControls();
})();
