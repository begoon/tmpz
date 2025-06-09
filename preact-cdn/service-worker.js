const CACHE_NAME = "color-grid-cache-v1";
const urlsToCache = ["./", "./index.html", "./manifest.json", "./icon-192.png", "./icon-512.png"];

self.addEventListener("install", (event) => {
    event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache)));
});

self.addEventListener("fetch", (event) => {
    console.log("fetching", event.request.url);

    const url = new URL(event.request.url);

    if (url.pathname === "/abc") {
        event.respondWith(new Response("abc?", { headers: { "Content-Type": "text/plain" } }));
        return;
    }
    event.respondWith(caches.match(event.request).then((response) => response || fetch(event.request)));
});
