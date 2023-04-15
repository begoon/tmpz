#!/usr/bin/env node
import { compile } from "svelte/compiler";

const filename = process.argv[2];
const result = compile(filename, { filename });
process.stdout.write(result.js.code);
