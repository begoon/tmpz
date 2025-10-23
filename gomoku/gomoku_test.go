package main

import "testing"

func BenchmarkEvaluate(b *testing.B) {
	g := NewGame(3)

	for b.Loop() {
		g.evaluate()
	}
}
