import { sveltekit } from '@sveltejs/kit/vite';
import { ogygia } from 'ogygia/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	// ogygia MUST run before sveltekit(): it rewrites `import X from '…' with { wake }`
	// into island shells before Kit compiles the route.
	plugins: [
		ogygia({
			regions: {
				// Start hydrating `wake: 'visible'` islands a little before they scroll into view.
				visible: { margin: '120px' },
				// Named presets let you reference a strategy from an import: `with { preset: 'chart' }`
				presets: {
					chart: { wake: 'visible', margin: '300px' }
				}
			}
		}),
		sveltekit()
	]
});
