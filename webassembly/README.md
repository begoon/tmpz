# Compile C to WebAssembly (WASM) and run it in the browser

## Introduction

A popular toolchain to compile C to WASM is `emscripten`. It provides bindings
to the standard C library and other inferfaces, like SDL2, and allows to compile C code to WASM and run it in the browser.

Unfortunately, `emscripten` is complex. It generates a lot of JavaScript code
boilerplate in HTML and JavaScript files.

If you only need to compile the C code, which does not use the standard C
library or other interfaces, you can use a simpler toolchain -- `clang` and `llc`.

The example below demonstrates how to compile C code to WASM, run it in the
browser and communicate with JavaScript using standard C types including
pointers.

## Prerequisites

On Mac, it only requires to install `llvm` from `brew` to enable the `clang`
compiler to generate WASM code:

```bash
brew install llvm
```

Then the path to `llc` toolchain must be added to the `PATH` environment:

```bash
export PATH=/opt/homebrew/opt/llvm/bin:$PATH
```

After that, the `clang` compiler should support the `--target=wasm32` target:

```bash
llc --version | grep wasm
```

## Compile C to WASM

`main.c` is:

```c
unsigned char mem[0x10000];

const char *const upper(char *const str, const int sz)
{
    for (int i = 0; i < sz; i++)
        if (str[i] >= 'a' && str[i] <= 'z')
            str[i] -= 0x20;
    return str;
}
```

compile it to WASM:

```bash
clang \
--target=wasm32 \
--no-standard-libraries \
-Wl,--export-all -Wl,--no-entry \
-o main.wasm \
main.c
```

The command creates a file `main.wasm` which is a binary WASM module.

This trivial example demonstrates basic needs to the simple C-to-WASM interface:

- an ability to use pre-allocated static memory buffer (for example, of size
  64KB)
- an ability to call C functions from JavaScript and pass primitive types
  (integers, pointers, etc.) as arguments
- an ability to return primitive types from C functions
- an ability to observe the memory buffer changes from JavaScript

The standard C library is not linked to the WASM module, so the C functions
should not use any standard C functions.

Interestingly, the result of the function `upper()`, which is a pointer, is
returned to JavaScript as a number, not as a pointer. This number is an offset
from the beginning of the WebAssembly memory buffer on the JavaScript side.

C deals with pointers, but JavaScript sees the memory buffer as a flat array
and uses offsets to access its elements.

In fact, WASM "direct memory access" is not what it literally means. WASM
memory is a reguar JavaScript object, which is a flat array of bytes. Its
lifecycle is managed by JavaScript garbage collector as any other JavaScript
objects.

## Run WASM in the browser

Use the following `main.html` file to run the WASM module in the browser:

```html
<!DOCTYPE html>

<html>
    <body>
        <script type="module">
            const log = console.log;
            console.log = (...x) => {
                document.body.innerHTML += x.join(" ") + "<br>";
                log(...x);
            };
            const wa = await WebAssembly.instantiateStreaming(
                fetch("main.wasm"),
                { js: { mem: new WebAssembly.Memory({ initial: 0 }) } }
            );
            const memPtr = wa.instance.exports.mem.value;
            console.log("memPtr", memPtr);

            const mem = new Uint8Array(wa.instance.exports.memory.buffer);

            const str = "Hello, world!";
            new TextEncoder().encodeInto(
                str,
                mem.subarray(memPtr, memPtr + str.length)
            );
            console.log(
                "upper()",
                wa.instance.exports.upper(memPtr, str.length)
            );
            console.log(
                new TextDecoder().decode(
                    mem.subarray(memPtr, memPtr + str.length)
                )
            );
        </script>
    </body>
</html>
```

The `main.html` and the `main.wasm` files need to be served by a web server.

For instance, by by Python's SimpleHTTPServer:

```python
python -m SimpleHTTPServer
```

or VSCode's Live Server extension.

You should see something like this in the browser and in the devtool console:

```text
memPtr 1024
upper() 1024
HELLO, WORLD!
```

`1024` is in fact "a pointer". `1024` is an offset from the beginning of
the `mem` C array in the WASM module memory.

The `upper()` function converts "Hello, world!" to upper case and returns the
same "pointer" `1024` to JavaScript.

That is it. The WASM module is compiled and run in the browser.
