# Alexander Demin

**Staff Software Engineer** · London, UK · [demin.ws](https://demin.ws) · [LinkedIn](https://www.linkedin.com/in/alexanderdemin/)

I design and build distributed systems and cloud infrastructure, currently at [iProov](https://www.iproov.com) (biometric identity verification). 20+ years of engineering across backend, platform, embedded and low-level work.

Away from work I write compilers, emulators and solvers, mostly for Soviet-era 8-bit machines and classic algorithms. Things that are slightly closer to the metal, and occasionally problems that probably did not need solving.

## What I do professionally

- **Distributed systems at iProov.** I work on the backend platform behind iProov's biometric identity verification service. The work spans service boundaries, data flows, latency budgets, reliability and cloud cost.
- **Cloud and platform engineering.** Infrastructure as code, CI/CD, observability and release engineering on GCP and AWS. Certified on AWS (Solutions Architect, Developer, SysOps), Google Cloud (Professional Cloud Developer) and Terraform.
- **Technical leadership.** Design reviews, mentoring, setting engineering standards and turning loosely defined product goals into systems that ship and keep running.
- **Depth below the framework.** 20+ years across backend, embedded and systems programming means I debug protocols, performance and memory problems at whatever layer they live in, from Kubernetes down to the instruction set.
- **Writing and teaching.** Author of the blog [Programming DIY](https://demin.ws/english/) since 2009 (also in [Russian](https://demin.ws)), and of articles for [PragPub](https://pragprog.com/magazines/) on iOS development, Go concurrency and CPU design.
- **PhD in Computer Science** from Moscow Aviation Institute. The thesis, the [Combined Method for integer linear programming](https://github.com/begoon/dissertation), is published with its implementation and benchmarks.

**Languages and stack:** Go, Python, TypeScript/JavaScript, C, Zig, Assembly (Intel 8080/Z80), Svelte, WASM, GCP, AWS, Kubernetes, Terraform, Docker, GitHub Actions.

## Highlights

- [i8080-core](https://github.com/begoon/i8080-core) (★83) - Cycle-accurate Intel 8080 (KR580VM80A) core in C, verified against the 8080/8085 CPU exercisers; the basis of several emulators
- [rapira](https://github.com/begoon/rapira) (★57) - Full interpreter for the Soviet educational language Rapira in TypeScript, with an [online playground](https://begoon.github.io/rapira) and `npx rapira`
- [rk86-js](https://github.com/begoon/rk86-js) (★28) - Радио-86РК emulator with built-in debugger, assembler, C and PL/M compilers, shipped as a web component on [rk86.ru](https://rk86.ru) and in the terminal via `npx rk86`
- [dissertation](https://github.com/begoon/dissertation) - Combined Method for Integer Linear Programming: a four-stage MILP solver (LP relaxation, vector-lattice search, filter row, bounded final search), with implementation, analysis and benchmarks
- [gomoku](https://github.com/begoon/gomoku-zig) - Gomoku AI in Zig/WASM: Minimax with alpha-beta pruning, local move pre-sorting and quiescence deepening to mitigate the horizon problem ([play](https://demin.ws/gomoku-zig/))
- [go-tcpspy](https://github.com/begoon/go-tcpspy) (★53) - TCP/IP proxy and traffic spy in Go, with [Python](https://github.com/begoon/py-tcpspy) and [Erlang](https://github.com/begoon/erl-tcpspy) ports

The full list of public repositories sorted by stars is in [stars.md](stars.md).

## Language implementation

Compilers, interpreters and assemblers, all written from scratch and runnable in the browser or via `npx`.

- [c8080-js](https://github.com/begoon/c8080-js) - Intel 8080 C compiler ported to TypeScript (`npx c8080`, [online](https://rk86.ru/beta/c8080))
- [plm80](https://github.com/begoon/plm80) - PL/M compiler for Intel 8080 and Радио-86РК (`npx plm80`, [online](https://demin.ws/plm80/))
- [asm8](https://github.com/begoon/asm8) - Intel 8080 assembler in TypeScript (`npx asm8080`, [online](https://begoon.github.io/asm8/))
- [easy](https://github.com/begoon/easy) - compiler for the EASY language (`npx @begoon/easyc`, [online](https://begoon.github.io/easy/))
- [snobol](https://github.com/begoon/snobol) - SNOBOL4 interpreter in TypeScript (`npx snobol`)
- [trac](https://github.com/begoon/trac) - TRAC 64 interpreter (`npx trac64i`, [online](https://begoon.github.io/trac/))
- [peg](https://github.com/begoon/tmpz/tree/main/peg) - PEG parser generator in Python: ordered choice, predicates, character classes, AST construction
- [nor](https://github.com/begoon/nor) - one-instruction CPU (OISC) based on NOR: DSL, compiler and executor
- [rapira](https://github.com/begoon/rapira) - Rapira ([Рапира](https://github.com/begoon/rapira/blob/main/RAPIRA.md)) interpreter, see Highlights

## Emulation and reverse engineering

- [intel8080.com](https://github.com/begoon/intel8080.com) - interactive Intel 8080 and КР580 instruction reference ([online](https://intel8080.com))
- [rk86-js](https://github.com/begoon/rk86-js) - Радио-86РК emulator, see Highlights; also available as a [web component](https://rk86.ru/web)
- [i8080-js](https://github.com/begoon/i8080-js) - Intel 8080 core in JavaScript (★48)
- [rk86-tape](https://github.com/begoon/rk86-tape) - WAV tape decoder for Радио-86РК, with a [signal visualiser](https://demin.ws/rk86-tape/) and a [write-up of the encoding](https://github.com/begoon/rk86-tape/blob/main/README-EN.md)
- [rk86-monitor](https://github.com/begoon/rk86-monitor) - annotated disassembly of the original 2 KB ROM monitor
- [rk86-reverse](https://github.com/begoon/rk86-reverse) - Claude Code skills for disassembling and reverse-engineering Intel 8080 programs
- Byte-exact annotated disassemblies and remakes of 1980s Радио-86РК games:
  [Volcano](https://github.com/begoon/volcano),
  [Лестница](https://github.com/begoon/lestnica),
  [Диверсант](https://github.com/begoon/diverse),
  [Алмаз](https://github.com/begoon/aliaz1),
  [ПВО](https://github.com/begoon/pvo),
  [Клад](https://github.com/begoon/klad),
  [SPACE](https://github.com/begoon/space)

## Hardware

- [rk86-maximite](https://github.com/begoon/rk86-maximite) - Радио-86РК emulator for the PIC32-based Maximite microcomputer
- [gmc4-loader](https://github.com/begoon/gmc4-loader) - USB loader for the GMC-4 microcomputer

## Algorithms and research

- [dissertation](https://github.com/begoon/dissertation) - Combined Method for ILP, see Highlights
- [svg-draw](https://github.com/begoon/svg-draw) - web playground for a JavaScript DSL that draws scientific illustrations ([online](https://begoon.github.io/svg-draw))
- [gomoku](https://github.com/begoon/gomoku-zig) - Gomoku AI agent, see Highlights
- [sokoban-solver](https://github.com/begoon/zig-sokoban-solver) - Sokoban solver in Zig and WASM ([online](https://demin.ws/zig-sokoban-solver/)), plus [60 Sokoban maps](https://github.com/begoon/sokoban-maps) (★49)
- [mastermind](https://github.com/begoon/tmpz/tree/main/mastermind) - Mastermind solver using Knuth's five-guess algorithm, implemented in Python, V and Zig
- [mastermind-web](https://github.com/begoon/mastermind) - browser game where the computer guesses your code and detects inconsistent answers ([play](https://demin.ws/mastermind/))
- [etudes-vegenere](https://github.com/begoon/etudes-vegenere) - Vigenère cipher breaker, the etude from Wetherell's "Etudes for Programmers"
- [ssb](https://github.com/begoon/ssb) - in-browser demonstration of Single Side Band radio modulation ([online](https://begoon.github.io/ssb))
- [Mayne-James compression](https://github.com/begoon/tmpz/tree/main/mayne-james-compression) (an LZ precursor) and the [GPM macro processor](https://github.com/begoon/tmpz/tree/main/gpm-macro)

## Tools

- [cloudrun-primer](https://github.com/begoon/cloudrun-primer) - Go starter for GCP Cloud Run with environment inspection, network diagnostics and filesystem browsing
- [go-tcpspy](https://github.com/begoon/go-tcpspy) - TCP/IP proxy and spy, see Highlights
- [go-reverse-proxy](https://github.com/begoon/go-reverse-proxy) - Go reverse-proxy example serving Python, Node and Go applications from one Docker container
- [openvpn-docker](https://github.com/begoon/openvpn-docker) - containerised OpenVPN client with TOTP and a SOCKS5 proxy
- [ngrok-ts](https://github.com/begoon/ngrok-ts) - TypeScript helper for running ngrok tunnels within applications during local development
- [http-server](https://github.com/begoon/http-server) - the same minimal HTTP REST server implemented in many languages, down to assembly (★37)

## CI/CD

- [gcp-cli](https://github.com/begoon/gcp-cli) - Go command-line tools for Cloud Run deployments, Compute Engine VMs and everyday development tasks
- [ghasha](https://github.com/begoon/ghasha) - GitHub Action exposing SHA, SHORT_SHA and BRANCH for the current commit ([marketplace](https://github.com/marketplace/actions/ghasha-sha-and-branch))
- [ghasecret](https://github.com/begoon/ghasecret) - GitHub Action for debugging CI: encodes a value so it survives the workflow log masking ([marketplace](https://github.com/marketplace/actions/ghasecret))
- [diskspace-action](https://github.com/begoon/diskspace-action) - GitHub Action checking remote disk space over SSH before deployment ([marketplace](https://github.com/marketplace/actions/disk-space))

## Frameworks

- [go-svelte](https://github.com/begoon/go-svelte) - Svelte + Go hybrid SPA/MPA application (★32)
- [sveltekit-bot](https://github.com/begoon/sveltekit-bot) - Telegram webhook bot built with SvelteKit and deployed on Vercel

## Applications

- [xc](https://github.com/begoon/xc) - portable single-file dual-panel file manager with a VFS layer (S3, GCS, SSH), `uvx xcfm` from [PyPI](https://pypi.org/project/xcfm/)
- [tube](https://github.com/begoon/tfl) - Transport for London timetable and line status viewer ([online](https://demin.ws/tfl))
- [imf](https://github.com/begoon/imf) - diet setup calculator for Lyle McDonald's *Intermittent Modified Fasting* book ([online](https://demin.ws/imf/))
- [morse](https://github.com/begoon/morse) - browser-based Morse trainer with listening and keying practice ([online](https://demin.ws/morse))

## iOS, macOS, Swift and Objective-C

- [openvpn-otp](https://github.com/begoon/openvpn-otp) - macOS OpenVPN connector in SwiftUI with automatic one-time password (TOTP) generation
- [otp-generator-swift](https://github.com/begoon/otp-generator-swift) - macOS menu bar TOTP generator in SwiftUI with clipboard copying
- [usvisa-app](https://github.com/begoon/usvisa-app) - US Visa app for iPhone in Objective-C
- [usvisa-api](https://github.com/begoon/usvisa-api) - Go/App Engine service for usvisa-app
- [buyround](https://github.com/begoon/buyround) - iPhone app to help buy a round at the pub

## Games

Browser remakes of classic and Soviet-era games, playable online.

- [volcano](https://github.com/begoon/volcano) - JavaScript remake of Volcano (Вулкан) from the Радио-86РК ([play](https://demin.ws/volcano/html))
- [paratrooper](https://github.com/begoon/paratrooper) - the 1982 arcade classic ([play](https://begoon.github.io/paratrooper))
- [fighter](https://github.com/begoon/fighter) - Fighter from the Агат-7 ([play](https://begoon.github.io/fighter))
- [kling](https://github.com/begoon/kling) - Космические Войны from the Агат-9 ([play](https://begoon.github.io/kling))
- [skittles](https://github.com/begoon/skittles) - a web reimagining of Городки ([play](https://begoon.github.io/skittles))
- [durak](https://github.com/begoon/durak) - the card game Переводной Дурак ([play](https://begoon.github.io/durak))
- [psycho](https://github.com/begoon/psycho) - a reflexive game "Платный психолог" ([play](https://begoon.github.io/psycho))
- [conix](https://github.com/begoon/conix) - port of `conix` to Python and TypeScript
- [life](https://github.com/begoon/life) - Life (in Svelte) in the browser ([play](https://svelte-life.vercel.app))
- [ucl](https://github.com/begoon/ucl) - HTML/JS remake of the 1996 UCL DOS demo ([view](https://demin.ws/ucl))

## Writing

I have been writing the blog "Программирование - это просто!" (Programming DIY) at [demin.ws](https://demin.ws) since 2009, mostly about low-level programming, emulation and algorithms.
