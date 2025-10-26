package main

import (
	"fmt"
	"math"
	"time"

	"gomoku/gomoku"

	"github.com/jupiterrider/purego-sdl3/sdl"
)

func run(g *gomoku.Game) {
	if !sdl.SetHint(sdl.HintRenderVSync, "1") {
		panic(sdl.GetError())
	}
	defer sdl.Quit()
	if !sdl.Init(sdl.InitVideo) {
		panic(sdl.GetError())
	}

	var window *sdl.Window
	var renderer *sdl.Renderer
	if !sdl.CreateWindowAndRenderer("Gomoku (SDL3)", 1024, 768, sdl.WindowResizable, &window, &renderer) {
		panic(sdl.GetError())
	}
	defer sdl.DestroyRenderer(renderer)
	defer sdl.DestroyWindow(window)

	turn := gomoku.Human
	turnText := func() string {
		if turn == gomoku.Human {
			return "Your turn"
		}
		return "Computer thinking…"
	}
	sdl.SetWindowTitle(window, "Gomoku (SDL3) - "+turnText())

	var gameOver bool
	var gameOverMessage string

	var lastMove gomoku.Move = gomoku.NewMove()

	for {
		draw := func() {
			sdl.SetRenderDrawColor(renderer, 240, 228, 200, 255)
			sdl.RenderClear(renderer)

			var w, h int32
			sdl.GetWindowSize(window, &w, &h)

			drawBoard(renderer, int(w), int(h))
			drawStones(renderer, g, lastMove)
			sdl.RenderPresent(renderer)

			sdl.SetWindowTitle(window, "Gomoku (SDL3) - "+turnText())
			if gameOver {
				sdl.SetWindowTitle(window, gameOverMessage)
			}
		}
		draw()

		var event sdl.Event
		for sdl.PollEvent(&event) {
			switch event.Type() {
			case sdl.EventQuit:
				return
			case sdl.EventKeyDown:
				if event.Key().Scancode == sdl.ScancodeEscape {
					return
				}
			case sdl.EventMouseMotion:
				if turn != gomoku.Human {
					break
				}
				mx, my := int(event.Motion().X), int(event.Motion().Y)
				var w, h int32
				sdl.GetWindowSize(window, &w, &h)
				m, ok := mousePositionToMove(mx, my, int(w), int(h))
				if ok {
					if m == lastMove || !g.EmptyAt(m) {
						break
					}
					lastMove = m
					g.Place(m, gomoku.Human)
					evaluation := g.Evaluate()
					fmt.Printf("board evaluation: %d\n", evaluation)
					g.Unplace(m)
					draw()
				}
			case sdl.EventMouseButtonDown:
				if gameOver {
					break
				}
				if turn != gomoku.Human {
					break
				}
				mx, my := int(event.Button().X), int(event.Button().Y)
				var w, h int32
				sdl.GetWindowSize(window, &w, &h)
				m, ok := mousePositionToMove(mx, my, int(w), int(h))
				if ok {
					if g.Place(m, gomoku.Human) {
						draw()
						gomoku.PrintBoard(g)
						if g.CheckWinFrom(m, gomoku.Human) {
							gameOver = true
							gameOverMessage = "You win! ✨"
						}
						if !gameOver && g.IsFull() {
							gameOver = true
							gameOverMessage = "Draw."
						}
						if !gameOver {
							turn = gomoku.Computer
							// compute AI move immediately
							fmt.Println("computer is thinking...")
							started := time.Now()
							_, best := g.Minimax(2)
							elapsed := time.Since(started)
							fmt.Printf("computer chose move %s in %v\n", best, elapsed)
							g.Place(best, gomoku.Computer)
							lastMove = best
							// draw()
							gomoku.PrintBoard(g)
							// check win
							if g.CheckWinFrom(best, gomoku.Computer) {
								gameOver = true
								gameOverMessage = "Computer wins! 🤖"
							}
							if !gameOver && g.IsFull() {
								gameOver = true
								gameOverMessage = "Draw."
							}
							turn = gomoku.Human
						}
					}
				}
			}
		}
	}
}

func drawBoard(r *sdl.Renderer, w, h int) {
	// Compute square board area with margins
	size := min(h, w)
	margin := max(size/20, 16)
	board := size - 2*margin
	cell := board / gomoku.N
	// top-left origin
	x0 := (w - board) / 2
	y0 := (h - board) / 2

	// Grid
	sdl.SetRenderDrawColor(r, 60, 60, 60, 255)
	for i := 0; i <= gomoku.N; i++ {
		sdl.RenderLine(r, float32(x0), float32(y0+i*cell), float32(x0+board), float32(y0+i*cell))
		sdl.RenderLine(r, float32(x0+i*cell), float32(y0), float32(x0+i*cell), float32(y0+board))
	}
}

func drawStones(r *sdl.Renderer, g *gomoku.Game, move gomoku.Move) {
	var w, h int32
	sdl.GetRenderOutputSize(r, &w, &h)
	size := min(int(h), int(w))
	margin := max(size/20, 16)
	board := size - 2*margin
	cell := board / gomoku.N
	x0 := (int(w) - board) / 2
	y0 := (int(h) - board) / 2

	radius := max(cell/2-4, 6)

	for ri := range gomoku.N {
		for ci := range gomoku.N {
			ch := g.Board[ri][ci]
			if ch == gomoku.Empty {
				continue
			}
			cx := x0 + ci*cell + cell/2
			cy := y0 + ri*cell + cell/2
			switch ch {
			case gomoku.Computer:
				// O as circle outline
				sdl.SetRenderDrawColor(r, 30, 120, 240, 255)
				drawCircle(r, cx, cy, radius)
			case gomoku.Human:
				// X as two lines
				sdl.SetRenderDrawColor(r, 220, 60, 60, 255)
				pad := radius
				sdl.RenderLine(r, float32(cx-pad), float32(cy-pad), float32(cx+pad), float32(cy+pad))
				sdl.RenderLine(r, float32(cx+pad), float32(cy-pad), float32(cx-pad), float32(cy+pad))
			}
			// highlight last move
			m := gomoku.MoveAt(ri, ci)
			if m == move {
				sdl.SetRenderDrawColor(r, 0, 200, 0, 255)
				sdl.RenderLine(r, float32(cx-radius-2), float32(cy), float32(cx+radius+2), float32(cy))
				sdl.RenderLine(r, float32(cx), float32(cy-radius-2), float32(cx), float32(cy+radius+2))
			}
		}
	}
}

func drawCircle(r *sdl.Renderer, cx, cy, radius int) {
	const segments = 64
	var prevX, prevY int
	for i := 0; i <= segments; i++ {
		ang := float64(i) * (2 * math.Pi / segments)
		x := cx + int(float64(radius)*math.Cos(ang))
		y := cy + int(float64(radius)*math.Sin(ang))
		if i > 0 {
			sdl.RenderLine(r, float32(prevX), float32(prevY), float32(x), float32(y))
		}
		prevX, prevY = x, y
	}
}

func mousePositionToMove(mx, my, w, h int) (m gomoku.Move, ok bool) {
	N := gomoku.N
	size := min(h, w)
	margin := max(size/20, 16)
	board := size - 2*margin
	cell := board / N
	x0 := (w - board) / 2
	y0 := (h - board) / 2
	if mx < x0 || my < y0 || mx >= x0+board || my >= y0+board {
		return m, false
	}
	// m.c = (mx - x0) / cell
	// m.r = (my - y0) / cell
	m = gomoku.MoveAt((my-y0)/cell, (mx-x0)/cell)
	if m.Invalid() {
		return m, false
	}
	return m, true
}
