package main

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"golang.org/x/term"
)

func terminalSize() (int, int) {
	width, height, err := term.GetSize(int(os.Stdout.Fd()))
	if err != nil {
		panic(err)
	}
	return width, height
}

func drawBorder(w, h int) {
	// clear screen
	h = h - 1
	fmt.Print("\033[H\033[2J")
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			if y == 0 && x == 0 {
				fmt.Print("┌")
			} else if y == 0 && x == w-1 {
				fmt.Print("┐")
			} else if y == h-1 && x == 0 {
				fmt.Print("└")
			} else if y == h-1 && x == w-1 {
				fmt.Print("┘")
			} else if y == 0 || y == h-1 {
				fmt.Print("─")
			} else if x == 0 || x == w-1 {
				fmt.Print("│")
			} else {
				fmt.Print(" ")
			}
		}
		fmt.Println()
	}
}

func cursorXY(x, y int) {
	fmt.Printf("\033[%d;%dH", y, x)
}

func main() {
	resizeChan := make(chan os.Signal, 1)
	signal.Notify(resizeChan, syscall.SIGWINCH)
	defer fmt.Println("exiting...")

	for {
		w, h := terminalSize()
		drawBorder(w, h)
		cursorXY(2, 1)
		fmt.Printf(" width=%d | height=%d ", w, h)
		cursorXY(3, 3)
		fmt.Println("listening for terminal resize events...")
		<-resizeChan
	}
}
