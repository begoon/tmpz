package main

import _ "embed"

//go:embed main.go
var myself string

func main() {
	println(myself)
}
