package main

import (
	"flag"
)

func main() {
	depth := flag.Int("depth", 2, "search depth for AI (2-4 is reasonable)")
	flag.Parse()
	if *depth < 1 {
		*depth = 1
	}

	g := NewGame(*depth)
	run(g)
}
