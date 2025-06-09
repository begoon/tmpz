const CACHE_NAME = "v1";
const urlsToCache = ["./", "./index.html", "./manifest.json", "./icon-192.png", "./icon-512.png"];

self.addEventListener("install", (event) => {
    event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache)));
});

self.addEventListener("fetch", async (event) => {
    console.log("fetching", event.request.url);

    const url = new URL(event.request.url);
    const { request } = event;

    try {
        console.log("fetching from network", url);
        const networkResponse = await fetch(request);
        const cache = await caches.open(CACHE_NAME);
        cache.put(request, networkResponse.clone());
        return networkResponse;
    } catch (error) {
        console.error("fetch failed", error);
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            console.log("returning cached response for", url);
            return cachedResponse;
        } else {
            return new Response("offline and no cached data available", {
                status: 503,
                headers: { "Content-Type": "text/plain" },
            });
        }
    }
});
