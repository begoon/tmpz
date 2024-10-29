import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

export default defineConfig({
    plugins: [svelte()],
    build: {
        cssCodeSplit: false,
        minify: true,
        emptyOutDir: true,
        rollupOptions: {
            input: {
                root: "./pages/index.html",
                a: "./pages/a/index.html",
                b: "./pages/b/index.html",
            },
            output: {
                dir: "api/static",
                entryFileNames: "page-[name].js",
                chunkFileNames: "assets/[name].js",
                assetFileNames: "assets/[name].[ext]",
            },
        },
    },
});
