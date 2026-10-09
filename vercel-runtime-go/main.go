package main

import (
	"log"
	"net/http"
	"os"

	"go-vercel/app"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}
	http.HandleFunc("/", app.Handler)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
