package api

import (
	"bytes"
	"embed"
	_ "embed"
	"encoding/json"
	"fmt"
	"io/fs"
	"net/http"
	"strings"
	"time"
)

//go:embed static
var staticFS embed.FS

const DATA = "window.__DATA__ = {}"

func Handler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path
	if path == "/" {
		path = "/index.html"
	}
	if strings.HasSuffix(path, "/") {
		path += "index.html"
	}
	if !strings.Contains(path, ".") {
		path += "/index.html"
	}
	fmt.Printf("path: %s [%s]\n", path, r.URL.Path)

	subFS, err := fs.Sub(staticFS, "static")
	if err != nil {
		http.Error(w, fmt.Sprintf("error subfs static: %s", err), http.StatusInternalServerError)
		return
	}

	if strings.HasSuffix(path, ".html") {
		path = "pages" + path
		fmt.Printf("-> %s\n", path)
		content, err := fs.ReadFile(subFS, path)
		if err != nil {
			http.Error(w, fmt.Sprintf("error read file: %s", err), http.StatusInternalServerError)
			return
		}
		data := struct {
			Path string    `json:"path"`
			When time.Time `json:"when"`
		}{
			Path: path,
			When: time.Now(),
		}
		b, err := json.Marshal(data)
		if err != nil {
			http.Error(w, fmt.Sprintf("error marshal json: %s", err), http.StatusInternalServerError)
			return
		}
		content = bytes.ReplaceAll(
			content,
			[]byte(DATA),
			[]byte(fmt.Sprintf("window.__DATA__ = %s;", string(b))),
		)
		w.Header().Set("Content-Type", "text/html")
		w.Write(content)
		return
	}

	fs := http.FS(subFS)
	w.Header().Set("Cache-Control", "public, max-age=31536000, immutable")
	http.FileServer(fs).ServeHTTP(w, r)
}
