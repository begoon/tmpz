<script lang="ts">
	import HydrationBadge from './HydrationBadge.svelte';
	import type { Cart } from './cart.svelte';

	let { cart, products }: { cart: Cart; products: string[] } = $props();
</script>

<article class="card">
	<header>
		<h3>Add to cart</h3>
		<HydrationBadge wake="visible" />
	</header>
	<p>
		A separate island, further down the page, mutating the same <code>Cart</code> instance. Watch
		the badge above update.
	</p>
	<div class="row wrap">
		{#each products as product}
			<button onclick={() => cart.add(product)}>+ {product}</button>
		{/each}
		<button class="ghost" onclick={() => cart.clear()}>clear</button>
	</div>
</article>
