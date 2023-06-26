import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [svelte()],
    build: {
        outDir: "dist",
        publicDir: "public",
        assetsInlineLimit: 0,
        rollupOptions: {
            output: {
                assetFileNames: "[name][extname]",
                chunkFileNames: "[name].js",
                entryFileNames: "[name].js",
            },
        },
    },
});
