import { svelte } from "@sveltejs/vite-plugin-svelte";
import { resolve } from "path";
import sveltePreprocess from "svelte-preprocess";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
    root: "lib",
    plugins: [svelte({ preprocess: sveltePreprocess() })],
    build: {
        outDir: "../dist",
        emptyOutDir: true,
        rollupOptions: {
            input: {
                root: resolve(__dirname, "./lib/index.html"),
                life: resolve(__dirname, "./lib/life/index.html"),
                blog: resolve(__dirname, "./lib/blog/index.html"),
            },
        },
    },
});
