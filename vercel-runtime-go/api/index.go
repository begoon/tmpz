package api

import (
	"crypto/sha256"
	"embed"
	"encoding/hex"
	"fmt"
	"html/template"
	"net/http"
	"os"
	"strings"
)

//go:embed static
var staticFS embed.FS

//go:embed templates
var tmplFS embed.FS

var tmpls = template.Must(template.New("").Funcs(template.FuncMap{"static": staticURL}).ParseFS(tmplFS, "templates/*"))

// staticURL returns the URL of an embedded static file with a content hash
// appended, so the immutable CDN cache is bypassed whenever the file changes.
func staticURL(name string) string {
	content, err := staticFS.ReadFile("static/" + name)
	if err != nil {
		return "/static/" + name
	}
	sum := sha256.Sum256(content)
	return "/static/" + name + "?v=" + hex.EncodeToString(sum[:8])
}

var secretEnv = map[string]bool{
	"AWS_ACCESS_KEY_ID":     true,
	"AWS_SECRET_ACCESS_KEY": true,
	"AWS_SESSION_TOKEN":     true,
}

func redact(s string) string {
	if len(s) <= 8 {
		return "..."
	}
	return s[:4] + "..." + s[len(s)-4:]
}

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
		if secretEnv[name] {
			value = redact(value)
		}
		data[name] = value
	}
	err := tmpls.ExecuteTemplate(w, path[1:], data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
