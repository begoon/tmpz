package main

import _ "embed"

//go:embed files/index.html
var file string

func main() {
	println(file)
}
