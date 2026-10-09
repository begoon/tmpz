package main

import (
	"log"
	"net/http"
	"os"

	"go-vercel/internal/web"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}
	http.HandleFunc("/", web.Handler)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
