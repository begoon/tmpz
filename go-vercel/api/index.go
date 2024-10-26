package api

import (
	"embed"
	_ "embed"
	"fmt"
	"html/template"
	"net/http"
	"os"
	"strings"
)

//go:embed static
var staticFS embed.FS

var tmpls *template.Template = template.Must(template.ParseFS(tmplFS, "templates/*"))

//go:embed templates
var tmplFS embed.FS

func Handler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path
	if path == "/" {
		path = "/index.html"
	}
	fmt.Printf("path: %s\n", path)
	// ---
	if strings.HasPrefix(path, "/static") {
		fs := http.FS(staticFS)
		w.Header().Set("Cache-Control", "public, max-age=31536000, immutable")
		http.FileServer(fs).ServeHTTP(w, r)
		return
	}
	// ---
	data := map[string]interface{}{}
	for k, v := range r.URL.Query() {
		data[k] = v
	}
	for _, v := range os.Environ() {
		name, value, _ := strings.Cut(v, "=")
		data[name] = value
	}
	err := tmpls.ExecuteTemplate(w, path[1:], data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
