import { render } from "https://esm.sh/preact-render-to-string@6.3.1";

const msg = <h1>Hello world!</h1>
console.log(msg);

console.log("[", render(msg), "]");

const Greating = (props: { name: string }) => <b>Hello {props.name}</b>;
const component = <h1><Greating name="Zoran"/></h1>;

console.log("[", render(component), "]");
