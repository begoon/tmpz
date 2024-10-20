package main

import (
	"net/http"

	"go-vercel/api"
)

//go:generate tailwindcss -i api/style.css -o api/html/style.css

func main() {
	http.HandleFunc("/", api.Handler)
	http.ListenAndServe(":8000", nil)
}
