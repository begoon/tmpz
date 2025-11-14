<script>
    import { create, turtle } from "$lib/data.remote";

    let name = $state("69");
    let query = $derived(turtle(name));
</script>

<label>
    turtle name
    <input type="text" bind:value={name} />
</label>

{#if query.error}
    <aside class="fixed top-0 right-0 bg-red-500 text-white p-2 rounded">ERROR: {JSON.stringify(query.error)}</aside>
{:else if query.loading}
    <p>loading...</p>
{:else}
    <code class="text-sm fixed font-mono whitespace-pre top-0 right-0 text-white bg-blue-600 p-2 rounded-xl">
        {JSON.stringify(query.current, null, 2)}
    </code>
    <button onclick={async () => await query.refresh()} class="bg-blue-500 text-white py-2 px-4 rounded">
        refresh
    </button>
{/if}

{#if create.result?.success}
    <p>successfully created!</p>
{/if}

<form
    {...create.enhance(async ({ form, data, submit }) => {
        try {
            alert("...creating: " + JSON.stringify(data));
            await submit();
            form.reset();
            alert("successfully created");
        } catch (error) {
            alert("something went wrong");
        }
    })}
    class="flex flex-col gap-4 border p-4 w-[50%] mt-2"
    oninput={() => create.validate()}
>
    <label>
        <h2>title</h2>
        <input {...create.fields.title.as("text")} class="w-full" />
        {#each create.fields.title.issues() as issue}
            <p class="issue">{issue.message}</p>
        {/each}
    </label>

    <label>
        <h2>content</h2>
        <textarea {...create.fields.content.as("text")} class="w-full"></textarea>
        {#each create.fields.content.issues() as issue}
            <p class="issue">{issue.message}</p>
        {/each}
    </label>

    <div class="flex gap-4">
        {#each ["windows", "mac", "linux"] as os}
            <label>
                <input {...create.fields.os.as("radio", os)} />
                {os}
            </label>
        {/each}
    </div>

    <div class="flex gap-4">
        {#each ["html", "css", "js"] as language}
            <label>
                <input {...create.fields.languages.as("checkbox", language)} />
                {language}
            </label>
        {/each}
    </div>

    <button class="bg-blue-500 text-white py-2 px-4 rounded w-fit">create</button>

    {#each create.fields.allIssues() as issue}
        <p class="issue">{issue.message}</p>
    {/each}
</form>

<style>
    .issue {
        color: red;
        font-size: 0.875rem;
    }
</style>
