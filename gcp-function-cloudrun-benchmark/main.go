package main

import (
	"net/http"

	"example.com/function/function"
)

func main() {
	http.HandleFunc("/", function.Handler)
	http.ListenAndServe(":8080", nil)
}
