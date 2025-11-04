run:
    zig run -O ReleaseFast gomoku.zig

test:
    zig test gomoku_test.zig

serve:
	python3 -m http.server -d site 8000

wasm: wasm-build wasm-run

wasm-run:
    bun gomoku.js

wasm-build:
    zig build-exe -O ReleaseFast -target wasm32-freestanding \
    -fstrip \
    -fno-entry \
    --export=loopback \
    -femit-bin=gomoku.wasm \
    gomoku.zig
    ls -al gomoku.wasm

js: js-build js-run

js-build:
    zig build-exe -O ReleaseFast -target wasm32-freestanding \
    -fstrip \
    -fno-entry \
    --export=alloc --export=free \
    --export=init \
    --export=place --export=unplace \
    --export=choose_move \
    --export=is_winner \
    --export=print_board --export=print_board_at \
    -femit-bin=site/wasm.wasm \
    wasm.zig

js-run:
    bun index.js

