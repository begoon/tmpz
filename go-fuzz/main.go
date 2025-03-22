package main

import (
	"fmt"
)

func Check(s string) bool {
	if len(s) == 1000 && s[99] == 'a' {
		return false
	}
	return true
}

func main() {
	fmt.Println(Check("0"))
}
