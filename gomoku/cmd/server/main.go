package main

import (
	"net/http"
)

func main() {
	server()
}

func server() {
	http.Handle("/", http.FileServer(http.Dir("site")))
	http.ListenAndServe(":8000", nil)
}
