<script lang="ts">
	import { page } from '$app/state';
	import '../app.css';

	let { children } = $props();

	const links = [
		{ href: '/', label: 'Islands' },
		{ href: '/how-it-works', label: 'How it works' }
	];
</script>

<div class="frame">
	<header class="top">
		<a class="brand" href="/">
			<span class="logo" aria-hidden="true"></span>
			SvelteKit × ogygia × Bun
		</a>
		<nav>
			{#each links as { href, label }}
				<a {href} aria-current={page.url.pathname === href ? 'page' : undefined}>{label}</a>
			{/each}
		</nav>
	</header>

	<main>
		{@render children()}
	</main>

	<footer>
		Page shell is static HTML (<code>csr = false</code>). Green outlines mark islands that have
		hydrated; open DevTools → Network → JS to see exactly which chunks were fetched.
	</footer>
</div>
