import { form, getRequestEvent, query } from "$app/server";
import { error } from "@sveltejs/kit";
import * as v from "valibot";

export const turtle = query(v.pipe(v.string(), v.minLength(2)), async (name: string) => {
    console.log("name", name);
    const request = getRequestEvent();
    console.log(request.url.href);
    const response = await (await fetch("http://localhost:5173/data?q=" + encodeURIComponent(name))).json();
    console.log("data", response);
    if (name === "418") error(418, "turtle 418");
    if (name === "500") error(500, "turtle 500");
    if (name === "400") error(400, "turtle 400");
    if (name === "123") throw new Error(`turtle error: [${name}]`);
    return {
        now: new Date().toISOString(),
        data: response,
        name,
    };
});

export const create = form(
    v.object({
        title: v.pipe(v.string(), v.nonEmpty("title cannot be empty")),
        content: v.pipe(v.string(), v.nonEmpty("content cannot be empty")),
        os: v.optional(v.picklist(["windows", "mac", "linux"]), "mac"),
        languages: v.optional(v.array(v.picklist(["html", "css", "js"]))),
    }),
    async (data, invalid) => {
        console.log("form data:", data);
        const { title, content } = data;
        console.log("creating:", { title, content });
        if (title === "error") invalid(invalid.title(`title cannot be 'error'`));
        return { success: true };
    }
);
