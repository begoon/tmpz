import { mount } from "svelte";
import "../app.css";
import Page from "./Page.svelte";

const app = mount(Page, {
    target: document.getElementById("app")!,
});

export default app;
