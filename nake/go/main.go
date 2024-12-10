package main

import (
	"fmt"
	"log"
	"os"
	"strings"
	"sync/atomic"
	"time"

	"golang.org/x/term"
)

const (
	h = 20
	w = 20
)

type Buffer [h][w]byte

func main() {
	initialState, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		log.Fatalf("error: %v", err)
	}
	defer func() { _ = term.Restore(int(os.Stdin.Fd()), initialState) }()

	state := struct {
		key         *int32
		frontBuffer *Buffer
		backBuffer  *Buffer
		x, y        int
		dx, dy      int
	}{
		key: new(int32),
		x:   10,
		y:   10,
	}

	input := make([]byte, 1)
	go func() {
		for {
			n, err := os.Stdin.Read(input)
			if n > 0 {
				atomic.StoreInt32(state.key, int32(input[0]))
			}
			if err != nil {
				break
			}
		}
	}()

	t := time.Now()
	for {
		state.backBuffer = new(Buffer)
		state.backBuffer[state.y][state.x] = 1

		state.frontBuffer = state.backBuffer

		fmt.Print("\033[H\033[2J") // clear screen

		fmt.Print("╭" + strings.Repeat("─", w*2) + "╮\n\r")
		for y := 0; y < h; y++ {
			fmt.Printf("│")
			for x := 0; x < w; x++ {
				ch := "  "
				if state.frontBuffer[y][x] == 1 {
					ch = "[]"
				}
				fmt.Printf("%s", ch)
			}
			fmt.Print("│\n\r")
		}
		fmt.Print("╰" + strings.Repeat("─", w*2) + "╯")

		switch atomic.SwapInt32(state.key, 0) {
		case 'w':
			state.dx = 0
			state.dy = -1
		case 's':
			state.dx = 0
			state.dy = 1
		case 'a':
			state.dx = -1
			state.dy = 0
		case 'd':
			state.dx = 1
			state.dy = 0
		case 'q':
			return
		}

		if now := time.Now(); now.Sub(t) > 100*time.Millisecond {
			t = now
			state.y = (state.y + state.dy + h) % h
			state.x = (state.x + state.dx + w) % w
		}

		time.Sleep(10 * time.Millisecond)
	}
}
