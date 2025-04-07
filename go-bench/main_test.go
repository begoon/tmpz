package main

import (
	"slices"
	"strings"
	"testing"
)

func BenchmarkSliceClone(b *testing.B) {
	origin := make([]byte, 0, 1024)
	for b.Loop() {
		s := slices.Clone(origin)
		_ = s
	}
}

func BenchmarkSliceCopy(b *testing.B) {
	origin := make([]byte, 0, 1024)
	for b.Loop() {
		s := origin[:]
		_ = s
	}
}

func BenchmarkRun(b *testing.B) {
	for b.Loop() {
		run("abc")
	}
}

const N = 100000

func run(s string) []byte {
	return []byte(s)
	m := make(map[int]string, N)
	for i := range N {
		m[i] = "abc"
		s = strings.Repeat("a", i)
	}
	return []byte(s)
}
