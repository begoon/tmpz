<script lang="ts">
	// Shared by every island. `$effect` never runs during SSR, so the badge starts as
	// "server HTML" and flips to "hydrated" the moment this island's JS actually executes.
	let { wake }: { wake: string } = $props();
	let hydratedAt = $state<string | null>(null);

	$effect(() => {
		hydratedAt = new Date().toLocaleTimeString(undefined, { hour12: false });
	});
</script>

<span class="badge" class:live={hydratedAt !== null}>
	{#if hydratedAt}
		⚡ hydrated at {hydratedAt}
	{:else}
		◌ server HTML only
	{/if}
	<code>wake: {wake}</code>
</span>

<style>
	.badge {
		display: inline-flex;
		gap: 0.5rem;
		align-items: center;
		font-size: 0.75rem;
		color: var(--muted);
	}
	.badge.live {
		color: var(--accent);
	}
	code {
		font-size: 0.7rem;
		background: var(--code-bg);
		padding: 0.1rem 0.35rem;
		border-radius: 4px;
	}
</style>
