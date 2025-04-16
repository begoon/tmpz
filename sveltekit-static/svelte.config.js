import adapter from "@sveltejs/adapter-static";
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";
import * as child_process from "node:child_process";

/** @type {import('@sveltejs/kit').Config} */
const config = {
    preprocess: vitePreprocess(),

    kit: {
        adapter: adapter(),
        output: { bundleStrategy: "inline" },
        router: { type: "hash" },
        version: {
            name: child_process.execSync("git rev-parse --short HEAD").toString().trim(),
        },
    },
};

export default config;
