package main

import (
	"strings"
	"testing"
)

func BenchmarkRun1(b *testing.B) {
	for b.Loop() {
		run("abc")
	}
}

const N = 100000

func run(s string) []byte {
	m := make(map[int]string, N)
	for i := range N {
		m[i] = "abc"
		s = strings.Repeat("a", i)
	}
	return []byte(s)
}
