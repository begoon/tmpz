<script lang="ts">
	// ── Islands ──────────────────────────────────────────────────────────────────────────
	// The import attribute is the whole API. Each of these becomes an <ogygia-region> with its
	// own tiny JS entry; the rest of this page stays server-rendered HTML.
	import Counter from '$lib/Counter.svelte' with { wake: 'load' };
	import StreamedStats from '$lib/StreamedStats.svelte' with { wake: 'load' };
	import Clock from '$lib/Clock.svelte' with { wake: 'idle' };
	import TapToWake from '$lib/TapToWake.svelte' with { wake: 'interaction' };
	import WideScreenOnly from '$lib/WideScreenOnly.svelte' with { wake: '(min-width: 900px)' };
	import LazyChart from '$lib/LazyChart.svelte' with { preset: 'chart' };
	import CartBadge from '$lib/CartBadge.svelte' with { wake: 'load' };
	import AddToCart from '$lib/AddToCart.svelte' with { wake: 'visible' };
	import ServerTime from '$lib/ServerTime.svelte' with { render: 'deferred', wake: 'load' };

	// ── Not an island ─────────────────────────────────────────────────────────────────────
	import StaticCard from '$lib/StaticCard.svelte';
	import { Cart } from '$lib/cart.svelte';

	let { data } = $props();

	// One instance handed to two islands; the `wire` codec keeps it a single live object.
	const cart = new Cart();
	cart.add('Apples');
</script>

<svelte:head>
	<title>Partial hydration with ogygia</title>
</svelte:head>

<section class="hero">
	<h1>Islands, not oceans</h1>
	<p>
		Every card below is server-rendered. Only the ones imported
		<code>with &#123; wake: … &#125;</code> download JavaScript, each on its own schedule. The page
		shell has no SvelteKit client runtime at all.
	</p>
</section>

<section class="grid">
	<StaticCard />
	<Counter start={10} />
	<Clock initial={data.serverTime} />
	<StreamedStats />
	<TapToWake />
	<WideScreenOnly query="(min-width: 900px)" />
	<CartBadge {cart} />
	<ServerTime label="Server island">
		{#snippet ogygiaFallback()}
			<article class="card server skeleton">
				<header><h3>Server island</h3></header>
				<p>⏳ fetching HTML from the server…</p>
			</article>
		{/snippet}
	</ServerTime>
</section>

<div class="spacer">
	<span>↓ scroll — the islands below use <code>wake: 'visible'</code> and only hydrate here ↓</span>
</div>

<section class="grid">
	<LazyChart values={data.chart} />
	<AddToCart {cart} products={data.products} />
</section>
