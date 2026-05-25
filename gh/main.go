package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
)

func aboutHandler() http.HandlerFunc {
	const version = "0.1.0"

	return func(w http.ResponseWriter, r *http.Request) {
		tag := r.PathValue("tag")
		data := struct {
			Version string `json:"version"`
			Tag     string `json:"tag"`
		}{Version: version, Tag: tag}

		err := json.NewEncoder(w).Encode(data)
		if err != nil {
			http.Error(w, "encode response", http.StatusInternalServerError)
			return
		}
	}
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}
	fmt.Printf("listening on %s\n", port)

	http.HandleFunc("GET /info/{tag}", aboutHandler())

	err := http.ListenAndServe(":"+port, nil)
	if err != nil {
		panic(err)
	}
}
