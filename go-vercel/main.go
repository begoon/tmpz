package main

import (
	"net/http"

	"go-vercel/api"
)

func main() {
	http.HandleFunc("/", api.Handler)
	http.ListenAndServe(":8000", nil)
}
