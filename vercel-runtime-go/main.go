package main

import (
	"net/http"

	"go-vercel/api"
)

//go:generate tailwindcss -m -i tailwind.css -o api/static/styles.css

func main() {
	http.HandleFunc("/", api.Handler)
	http.ListenAndServe(":8000", nil)
}
