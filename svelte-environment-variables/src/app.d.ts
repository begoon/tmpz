// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
    namespace App {
        // interface Error {}
        // interface Locals {}
        interface PageData {
            client: Record<string, unknown> | undefined;
            server: Record<string, unknown> | undefined;
        }
        // interface PageState {}
        // interface Platform {}
    }
}

export {};
