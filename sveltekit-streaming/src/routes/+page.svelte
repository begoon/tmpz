<script lang="ts">
    import { onDestroy, onMount } from "svelte";

    type Message = {
        n: number;
        when: string;
        mode: string;
    };

    let output = $state<Message[]>([]);

    const print_ = (data: string) => {
        const message = JSON.parse(data) as Message;
        output.push(message);
    };

    let streamReader: ReadableStreamDefaultReader<Uint8Array> | undefined;

    async function readStream() {
        const response = await fetch("/stream/raw");
        if (!response.ok || !response.body) {
            console.error("fetch stream:", response.statusText);
            return;
        }

        streamReader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer: string | undefined = "";

        while (true) {
            const { done, value } = await streamReader.read();
            if (done) {
                if (buffer?.trim()) print_(buffer);
                break;
            }

            buffer += decoder.decode(value, { stream: true });

            let lines: string[] = buffer?.split("\n") || [];
            buffer = lines.pop();

            for (const line of lines) print_(line);
        }
    }

    let eventSource: EventSource | undefined;

    function cancel() {
        streamReader?.cancel();
        eventSource?.close();
    }

    onMount(async () => {
        readStream();
        eventSource = new EventSource("/stream/sse");
        eventSource.onmessage = (event) => print_(event.data);
    });

    onDestroy(() => cancel());
</script>

<button onclick={() => window.location.reload()}> reload </button>
<button onclick={cancel}>stop</button>
<div style="display: grid; grid-template-columns: 3em 5em 20em; gap-x: 1em;">
    {#each output.toReversed().slice(0, 20) as line}
        <b>{line.n}</b>
        <span>{line.mode}</span>
        <span class={line.mode}>{line.when}</span>
    {/each}
</div>

<style>
    .sse {
        color: red;
    }
    .stream {
        color: blue;
    }
</style>
