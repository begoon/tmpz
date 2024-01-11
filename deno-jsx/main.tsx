console.log("jsx");

export function Greeting({ name }: { name: string }) {
  return (
    <>
      Hello {name}!
    </>
  );
}

console.log(
  <Greeting name="World" />,
);
