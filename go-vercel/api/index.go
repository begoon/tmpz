package handler

import (
	"fmt"
	"net/http"
)

func Handler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path[1:]
	fmt.Fprintf(w, "<h1>TEA: %s</h1>", path)
}
