package main

import (
	"fmt"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
)

func main() {
	url, err := url.Parse("http://localhost:9000")
	if err != nil {
		log.Fatal(fmt.Errorf("error parsing url: %v", err))
	}
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/health" {
			w.WriteHeader(http.StatusOK)
			w.Header().Set("Content-Type", "application/json")
			w.Write([]byte(`{"version": "0.0.1"}`))
			return
		}
		httputil.NewSingleHostReverseProxy(url).ServeHTTP(w, r)
	})
	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}
