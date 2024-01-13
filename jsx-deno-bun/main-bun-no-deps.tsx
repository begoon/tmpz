const msg = <h1>Hello world!</h1>
console.log(msg);

const Greating = (props: { name: string }) => <b>Hello {props.name}</b>;
const component = <h1><Greating name="Zoran"/></h1>;

console.log(component);
