package main

import (
	"net/http"
	"os"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		env := os.Environ()
		for _, e := range env {
			w.Write([]byte(e + "\n"))
		}
	})
	http.ListenAndServe(":"+port, nil)
}
