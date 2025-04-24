<script lang="ts">
    import { onMount } from "svelte";

    type Message = {
        n: number;
        when: string;
        origin: string;
    };

    let streamOutput = $state<Message[]>([]);
    let sseOutput = $state<Message[]>([]);

    const print_ = (target: Message[], data: string) => {
        const message = JSON.parse(data) as Message;
        target.push(message);
    };

    let streamReader: ReadableStreamDefaultReader<Uint8Array>;

    async function readStream() {
        const response = await fetch("/stream");
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
                if (buffer?.trim()) print_(streamOutput, buffer);
                break;
            }

            buffer += decoder.decode(value, { stream: true });

            let lines: string[] = buffer?.split("\n") || [];
            buffer = lines.pop();

            for (const line of lines) {
                print_(streamOutput, line);
            }
        }
    }

    let eventSource: EventSource;

    onMount(async () => {
        readStream();
        eventSource = new EventSource("/sse");
        eventSource.onmessage = (event) => print_(sseOutput, event.data);
    });
</script>

<button onclick={() => window.location.reload()}> reload </button>
<div
    style="
        display: grid; grid-template-columns: 20em 20em; gap: 1rem; 
        width: fit-content; border: 1px solid black; padding: 1rem; 
        align-items: start;
    "
>
    <div>stream <button onclick={() => streamReader.cancel()}>stop</button></div>
    <div>sse <button onclick={() => eventSource.close()}>stop</button></div>
    <div
        style="
            display: grid; grid-template-columns: 1fr 1fr 3fr;
            gap-x: 0.1rem; border: 1px solid red; background: lightcoral;
        "
    >
        {#each streamOutput.toReversed().slice(0, 10) as line}
            <b>{line.n}</b>
            <span>{line.origin}</span>
            <span>{line.when}</span>
        {/each}
    </div>
    <div
        style="
            display: grid; grid-template-columns: 1fr 1fr 3fr; 
            gap-x: 0.1rem; border: 1px solid blue; background: lightblue;
        "
    >
        {#each sseOutput.toReversed().slice(0, 10) as line}
            <b>{line.n}</b>
            <span>{line.origin}</span>
            <span>{line.when}</span>
        {/each}
    </div>
</div>
