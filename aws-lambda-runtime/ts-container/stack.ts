try {
    // @ts-ignore deno-ts(7022)
    a = 1;
    throw new Error("Something went wrong!");
} catch (error) {
    console.error("Error:", JSON.stringify(error.message));
    console.error("Stack Trace:", JSON.stringify(error.stack.split("\n")));
    console.error("Type's Name:", JSON.stringify(error.name));
}
