<script lang="ts">
	import { page } from '$app/state';
	import HydrationBadge from './HydrationBadge.svelte';

	// `page.data` inside an island works like in any Kit page. A promise returned from `load`
	// streams: the page and this island's pending branch paint immediately, the value lands later.
	type Stats = { visitors: number; uptime: string };
	const stats = $derived(page.data.stats as Promise<Stats>);
</script>

<article class="card">
	<header>
		<h3>Streamed page data</h3>
		<HydrationBadge wake="load" />
	</header>
	<p>
		<code>+page.server.ts</code> returns a promise. The shell paints at once; the island resolves it
		live. Current path from <code>page.url</code>: <code>{page.url.pathname}</code>
	</p>
	{#await stats}
		<p class="pending">⏳ waiting for stats…</p>
	{:then s}
		<dl>
			<div><dt>Visitors</dt><dd>{s.visitors.toLocaleString()}</dd></div>
			<div><dt>Uptime</dt><dd>{s.uptime}</dd></div>
		</dl>
	{:catch err}
		<p>Failed: {err.message}</p>
	{/await}
</article>

<style>
	.pending {
		color: var(--muted);
	}
	dl {
		display: flex;
		gap: 2rem;
		margin: 0;
	}
	dt {
		font-size: 0.75rem;
		color: var(--muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	dd {
		margin: 0;
		font-size: 1.5rem;
		font-weight: 600;
	}
</style>
