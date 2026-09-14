<script lang="ts">
	// A regular Svelte component imported WITHOUT an attribute. It renders on the server and
	// ships zero JavaScript. Try clicking the button: nothing happens, because nothing hydrated.
	let clicks = 0;
</script>

<article class="card static">
	<header>
		<h3>Static component</h3>
		<span class="badge">◌ server HTML only <code>no attribute</code></span>
	</header>
	<p>
		Plain <code>import StaticCard from '$lib/StaticCard.svelte'</code>. Svelte still rendered it to
		HTML, but no JS for it reaches the browser.
	</p>
	<button onclick={() => clicks++}>clicked {clicks} times (dead button)</button>
</article>

<style>
	.badge {
		display: inline-flex;
		gap: 0.5rem;
		font-size: 0.75rem;
		color: var(--muted);
	}
	.badge code {
		font-size: 0.7rem;
	}
</style>
