<script>
  import { onMount } from "svelte";

  let bridge = $state("checking...");
  let info = $state(null);
  let infoError = $state(null);
  let counter = $state(0);
  let counterError = $state(null);
  let busy = $state(false);

  async function loadInfo() {
    infoError = null;
    try {
      info = await window.zero.invoke("system.info");
    } catch (err) {
      infoError = err.message ?? String(err);
    }
  }

  async function refreshCounter() {
    counterError = null;
    try {
      const { value } = await window.zero.invoke("counter.get");
      counter = value;
    } catch (err) {
      counterError = err.message ?? String(err);
    }
  }

  async function bump(command) {
    if (busy) return;
    busy = true;
    counterError = null;
    try {
      const { value } = await window.zero.invoke(command);
      counter = value;
    } catch (err) {
      counterError = err.message ?? String(err);
    } finally {
      busy = false;
    }
  }

  onMount(async () => {
    if (!window.zero?.invoke) {
      bridge = "not enabled";
      return;
    }
    bridge = "available";
    await Promise.all([loadInfo(), refreshCounter()]);
  });
</script>

<main>
  <p class="eyebrow">zero-native + Svelte + Zig</p>
  <h1>Bridge Trial</h1>

  <div class="card">
    <span>Native bridge</span>
    <strong>{bridge}</strong>
  </div>

  <section class="panel">
    <header>
      <h2>system.info</h2>
      <button onclick={loadInfo} disabled={bridge !== "available"}>refresh</button>
    </header>
    {#if infoError}
      <p class="error">{infoError}</p>
    {:else if info}
      <dl>
        <dt>sysname</dt><dd>{info.sysname}</dd>
        <dt>nodename</dt><dd>{info.nodename}</dd>
        <dt>release</dt><dd>{info.release}</dd>
        <dt>machine</dt><dd>{info.machine}</dd>
        <dt>cpus</dt><dd>{info.cpus}</dd>
      </dl>
    {:else}
      <p class="muted">loading…</p>
    {/if}
  </section>

  <section class="panel">
    <header>
      <h2>counter (state lives in Zig)</h2>
      <strong class="value">{counter}</strong>
    </header>
    <div class="row">
      <button onclick={() => bump("counter.increment")} disabled={busy || bridge !== "available"}>increment</button>
      <button onclick={() => bump("counter.reset")} disabled={busy || bridge !== "available"}>reset</button>
      <button onclick={refreshCounter} disabled={busy || bridge !== "available"}>get</button>
    </div>
    {#if counterError}
      <p class="error">{counterError}</p>
    {/if}
  </section>
</main>

<style>
  main {
    max-width: 560px;
    margin: 0 auto;
    padding: 2rem 1.5rem 3rem;
    font-family: -apple-system, BlinkMacSystemFont, "Inter", system-ui, sans-serif;
    color: #1f2933;
  }
  .eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-size: 0.75rem;
    color: #6b7280;
    margin: 0 0 0.25rem;
  }
  h1 { margin: 0 0 1.25rem; font-size: 1.75rem; }
  h2 { margin: 0; font-size: 1rem; font-weight: 600; }
  .card {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.75rem 1rem; border-radius: 0.5rem;
    background: #f3f4f6; margin-bottom: 1rem;
  }
  .panel {
    border: 1px solid #e5e7eb; border-radius: 0.75rem;
    padding: 1rem 1.25rem; margin-bottom: 1rem; background: white;
  }
  .panel header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 0.75rem;
  }
  .value { font-variant-numeric: tabular-nums; font-size: 1.25rem; }
  dl {
    display: grid; grid-template-columns: 6rem 1fr; gap: 0.25rem 1rem;
    margin: 0; font-size: 0.9rem;
  }
  dt { color: #6b7280; }
  dd { margin: 0; font-family: ui-monospace, SFMono-Regular, monospace; }
  .row { display: flex; gap: 0.5rem; flex-wrap: wrap; }
  button {
    padding: 0.4rem 0.8rem; border-radius: 0.4rem;
    border: 1px solid #d1d5db; background: white; cursor: pointer;
    font-size: 0.875rem;
  }
  button:hover:not(:disabled) { background: #f9fafb; }
  button:disabled { opacity: 0.5; cursor: not-allowed; }
  .error { color: #b91c1c; margin: 0.5rem 0 0; font-size: 0.85rem; }
  .muted { color: #6b7280; margin: 0; font-size: 0.85rem; }
</style>
