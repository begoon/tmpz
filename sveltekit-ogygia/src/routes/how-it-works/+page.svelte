<svelte:head>
	<title>How it works · ogygia</title>
</svelte:head>

<section class="prose">
	<h1>How it works</h1>

	<h2>1. Turn off the Kit client runtime</h2>
	<pre><code>// src/routes/+layout.ts
export const csr = false;</code></pre>
	<p>
		With <code>csr = false</code> SvelteKit renders every route to HTML and ships no client-side
		JavaScript. Links are ordinary full-page navigations. This page you are reading is exactly that:
		zero JS.
	</p>

	<h2>2. Add the plugin before <code>sveltekit()</code></h2>
	<pre><code>// vite.config.ts
import &#123; ogygia &#125; from 'ogygia/vite';
export default defineConfig(&#123;
  plugins: [ogygia(), sveltekit()]
&#125;);</code></pre>

	<h2>3. Mark islands with an import attribute</h2>
	<pre><code>import Counter from '$lib/Counter.svelte' with &#123; wake: 'load' &#125;;
import Chart   from '$lib/Chart.svelte'   with &#123; wake: 'visible' &#125;;
import Clock   from '$lib/Clock.svelte'   with &#123; wake: 'idle' &#125;;
import Menu    from '$lib/Menu.svelte'    with &#123; wake: 'interaction' &#125;;
import Wide    from '$lib/Wide.svelte'    with &#123; wake: '(min-width: 900px)' &#125;;
import Greet   from '$lib/Greet.svelte'   with &#123; render: 'deferred', wake: 'load' &#125;;</code></pre>
	<p>
		The plugin rewrites each marked import. On the server the component still renders normally,
		but wrapped in an <code>&lt;ogygia-region&gt;</code> custom element carrying its props
		(serialised with <code>devalue</code>) and the URL of a per-island JS entry. In the browser a
		shared runtime of roughly 8&nbsp;KB watches those elements and imports each entry when its
		<code>wake</code> condition is met.
	</p>

	<table>
		<thead><tr><th><code>wake</code></th><th>Hydrates…</th></tr></thead>
		<tbody>
			<tr><td><code>'load'</code></td><td>immediately, with <code>modulepreload</code> hints in the HTML</td></tr>
			<tr><td><code>'idle'</code></td><td>in <code>requestIdleCallback</code></td></tr>
			<tr><td><code>'visible'</code></td><td>when an <code>IntersectionObserver</code> fires (tunable <code>margin</code>)</td></tr>
			<tr><td><code>'interaction'</code></td><td>on the first pointer, focus or key event inside it, then replays the event</td></tr>
			<tr><td>a media query</td><td>when <code>matchMedia</code> matches</td></tr>
		</tbody>
	</table>

	<h2>4. Server islands</h2>
	<p>
		<code>render: 'deferred'</code> skips the component during the page request. The page ships the
		<code>ogygiaFallback</code> snippet in its place and the browser fetches the real HTML from a
		signed endpoint served by <code>handle</code> from <code>ogygia/server</code> in
		<code>hooks.server.ts</code>. Slow or per-user fragments no longer hold the whole page hostage,
		and they still ship no client JS.
	</p>

	<h2>5. Sharing state between islands</h2>
	<p>
		Islands are separate hydration roots, so props cross a serialisation boundary. Give a class a
		<code>static wire = import.meta.og.wire(&#123; encode, decode &#125;)</code> codec and every island
		receiving the same instance shares one live object in the browser. That is how the cart badge
		and the add-to-cart island on the home page stay in sync without a store or an event bus.
	</p>

	<h2>Bun</h2>
	<pre><code>bun install
bun run dev        # vite dev under Bun
bun run build      # adapter-node output in ./build
bun run start      # bun ./build/index.js</code></pre>
	<p><a href="/">← back to the islands</a></p>
</section>
