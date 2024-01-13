# JSX in Deno and Bun

- <https://bun.sh/docs/runtime/jsx>
- <https://docs.deno.com/runtime/manual/advanced/jsx_dom/jsx>

<https://github.com/preactjs/preact-render-to-string>

<https://github.com/denoland/deno/issues/20582>

<https://github.com/denoland/deno/issues/21927>

## Deno with preact/preact-render-to-string

```bash
deno run main-deno.tsx
```

```text
{
  type: "h1",
  props: { children: "Hello world!" },
  key: undefined,
  ref: undefined,
  __k: null,
  __: null,
  __b: 0,
  __e: null,
  __d: undefined,
  __c: null,
  constructor: undefined,
  __v: -1,
  __i: -1,
  __u: 0,
  __source: undefined,
  __self: undefined
}
[ <h1>Hello world!</h1> ]
[ <h1><b>Hello Alexander</b></h1> ]
```

## Bun vanilla, no dependencies

```bash
bun main-bun-no-deps.tsx
```

```text
<h1>Hello world!</h1>
<h1>
  <NoName name="Zoran" />
</h1>
```

## Bun with preact

```bash
bun main-bun.tsx
```

```text
<h1>Hello world!</h1>
[  ]
[ <h1>
  <NoName name="Zoran" />
</h1> ]
[  ]
```
