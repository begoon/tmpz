<script lang="ts">
	import HydrationBadge from './HydrationBadge.svelte';
	import type { Cart } from './cart.svelte';

	let { cart }: { cart: Cart } = $props();
</script>

<article class="card">
	<header>
		<h3>Cart badge</h3>
		<HydrationBadge wake="load" />
	</header>
	<p>Reads the shared <code>Cart</code>. It never writes to it.</p>
	<output class="count">🛒 {cart.count} item{cart.count === 1 ? '' : 's'}</output>
	{#if cart.items.length}
		<ul>
			{#each cart.items as item}<li>{item}</li>{/each}
		</ul>
	{/if}
</article>

<style>
	.count {
		font-size: 1.5rem;
		font-weight: 600;
	}
	ul {
		margin: 0.5rem 0 0;
		padding-left: 1.25rem;
		color: var(--muted);
	}
</style>
