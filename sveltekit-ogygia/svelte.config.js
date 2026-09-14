import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { ogygia } from 'ogygia/vite';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// ogygia's preprocessor handles the `ogygiaFallback` snippet on server islands.
	// It is a no-op for everything else.
	preprocess: [vitePreprocess(), ...ogygia.preprocess()],
	compilerOptions: {
		// Server islands may `await` at the top of their <script>.
		experimental: { async: true }
	},
	kit: {
		// adapter-node output is plain ESM and runs under Bun: `bun ./build/index.js`
		adapter: adapter()
	}
};

export default config;
