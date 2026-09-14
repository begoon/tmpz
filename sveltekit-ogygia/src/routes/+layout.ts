// The whole point: ship ZERO SvelteKit client runtime for the page shell.
// Only components imported `with { wake: … }` get JavaScript in the browser.
export const csr = false;
