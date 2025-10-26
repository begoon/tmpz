package gomoku

import (
	"fmt"
	"testing"
)

func BenchmarkEvaluate(b *testing.B) {
	g := NewGame()

	for b.Loop() {
		g.Evaluate()
	}
}

type position struct {
	layout []string
	move   Move
}

func placePosition(g *Game, position position) {
	layout := position.layout
	w := len(layout[0])
	for i, v := range layout {
		if len(v) != w {
			panic(fmt.Sprintf("invalid position at row %d", i))
		}
	}
	offsetX := (N - w/2) / 2
	offsetY := (N - len(layout)) / 2

	for r, row := range layout {
		for c, v := range row[1:] {
			if c&1 == 0 {
				continue
			}
			m := Move{offsetY + r, offsetX + c/2}
			switch v {
			case 'X':
				g.Place(m, Human)
			case 'O':
				g.Place(m, Computer)
			}
		}
	}
	m := Move{offsetY + position.move.r, offsetX + position.move.c}
	g.Place(m, Human)
}

var trivia = position{
	layout: []string{
		// 0 1 2
		"  X O X", // 0
		"    X O", // 1
		"    O ?", // 2
	},
	move: Move{2, 2},
}

func TestPlacePosition(t *testing.T) {
	g := NewGame()
	placePosition(g, trivia)
}

func BenchmarkMinimax(b *testing.B) {
	g := NewGame()

	placePosition(g, trivia)
	for b.Loop() {
		v, m := g.Minimax(1)
		if v != 41980 {
			b.Fatalf("expected 41980, got %d (move: %+v)", v, m)
		}
	}
}
