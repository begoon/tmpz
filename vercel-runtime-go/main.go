package main

import (
	"go-vercel/api"
	"net/http"
)

func main() {
	http.HandleFunc("/", api.Handler)
	http.ListenAndServe(":8000", nil)
}
