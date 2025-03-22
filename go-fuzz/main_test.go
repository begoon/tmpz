package main

import (
	"testing"
)

func FuzzCheck(f *testing.F) {
	f.Fuzz(func(t *testing.T, input string) {
		result := Check(input)
		if !result {
			t.Errorf("Check(%s) = %v; want false", input, result)
		}
	})
}
