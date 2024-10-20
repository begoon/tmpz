package api

import (
	"bytes"
	_ "embed"
	"fmt"
	"io"
	"net/http"
)

//go:embed images/r-tape-loading-error.gif
var image []byte

func Handler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path
	fmt.Printf("path: %s\n", path)
	if path == "/" || path == "/style.css" {
		name := "style.css"
		if path == "/" {
			name = "index.html"
		}
		http.ServeFile(w, r, "api/html/"+name)
		return
	}
	if path == "/image" {
		_, err := io.Copy(w, bytes.NewReader(image))
		if err != nil {
			msg := fmt.Sprintf("error serving image: %s", err)
			http.Error(w, msg, http.StatusInternalServerError)
			return
		}
	}
	if path == "/tape" {
		http.ServeFile(w, r, "api/images/IMG_3751, square.jpeg")
		return
	}
	fmt.Fprintf(w, "<h1>ha? [%s]</h1>", path)
}
