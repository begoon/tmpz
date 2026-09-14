<script lang="ts">
	import type { Snippet } from 'svelte';

	// A SERVER island (`render: 'deferred'`). This component is NOT rendered during the initial
	// page request. The page ships a placeholder (the `ogygiaFallback` snippet) and the browser
	// fetches this component's HTML from ogygia's signed endpoint afterwards. It never hydrates:
	// no JS for it reaches the client. Use it for slow or personalised fragments that must not
	// block the page.
	let { label = 'Server island', ogygiaFallback }: { label?: string; ogygiaFallback?: Snippet } =
		$props();

	// Simulate a slow upstream call (a database, an API, …).
	await new Promise((r) => setTimeout(r, 1200));
	const renderedAt = new Date().toISOString();
	const runtime = process.versions.bun ? `Bun ${process.versions.bun}` : `Node ${process.version}`;
</script>

<article class="card server">
	<header>
		<h3>{label}</h3>
		<span class="badge">🛰 fetched from server <code>render: deferred</code></span>
	</header>
	<p>Rendered on the server at <strong>{renderedAt}</strong> by {runtime}.</p>
	<p class="hint">Reload the page: the rest of the page paints first, then this hole fills in.</p>
</article>

<style>
	.badge {
		display: inline-flex;
		gap: 0.5rem;
		font-size: 0.75rem;
		color: var(--server);
	}
	.badge code {
		font-size: 0.7rem;
	}
	.hint {
		color: var(--muted);
		font-size: 0.85rem;
	}
</style>
