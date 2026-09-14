<script lang="ts">
	import HydrationBadge from './HydrationBadge.svelte';

	let { query }: { query: string } = $props();
	let taps = $state(0);
</script>

<article class="card">
	<header>
		<h3>Media-query island</h3>
		<HydrationBadge wake={query} />
	</header>
	<p>
		Hydrates only when <code>{query}</code> matches. Resize the window below that width and reload:
		the button stays inert.
	</p>
	<button onclick={() => taps++}>taps {taps}</button>
</article>
