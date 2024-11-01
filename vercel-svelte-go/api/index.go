package api

import (
	"bytes"
	"embed"
	_ "embed"
	"encoding/json"
	"fmt"
	"html/template"
	"io/fs"
	"log"
	"net/http"
	"regexp"
	"strings"
	"time"

	"github.com/go-chi/chi/middleware"
	"github.com/go-chi/chi/v5"
	"github.com/go-resty/resty/v2"
)

func must[T any](v T, err error) T {
	if err != nil {
		panic(err)
	}
	return v
}

//go:embed static
var staticEmbedFS embed.FS

var staticFS = must(fs.Sub(staticEmbedFS, "static"))

//go:embed COMMIT.txt
var commit string

const DATA = "window.__DATA__ = {}"

type (
	RouteFunc func(r *http.Request, path string, params map[string]string) *Page
	Route     struct {
		Path    *regexp.Regexp
		Handler RouteFunc
	}
)

type Page struct {
	Path   string            `json:"path"`
	Data   interface{}       `json:"data"`
	Params map[string]string `json:"params"`
	Commit string            `json:"commit"`
	Query  interface{}       `json:"query"`
}

var httpFS = http.FS(staticFS)

var assets = make(map[string]bool)

func init() {
	err := fs.WalkDir(staticFS, ".", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		fmt.Println(path, d.Type().IsRegular())
		assets["/"+path] = true
		return nil
	})
	if err != nil {
		log.Fatal(err)
	}
}

func Handler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path

	started := time.Now()
	log.Printf("REQUEST: %s %s\n", r.Method, path)
	defer func() {
		log.Printf("RESPONSE: %s\n", time.Since(started))
	}()

	chr := chi.NewRouter()
	chr.Use(middleware.Logger)
	chr.Use(middleware.URLFormat)

	chr.Get("/endpoint/users/{id}", func(w http.ResponseWriter, r *http.Request) {
		userID := chi.URLParam(r, "id")
		fmt.Fprintf(w, "user: %s", userID)
	})

	chr.Get("/endpoint/click/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		log.Printf("\t> CLICK: %#v\n", id)
	})

	chr.Get("/endpoint/public-ip", func(w http.ResponseWriter, r *http.Request) {
		ipfy := "https://api.ipify.org?format=text"
		client := resty.New()
		resp, err := client.R().Get(ipfy)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		response := struct {
			IP string `json:"ip"`
		}{
			IP: string(resp.Body()),
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)

		time.Sleep(3 * time.Second)
		if err := json.NewEncoder(w).Encode(response); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
		}
	})

	chr.Get("/a/{name}", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("PAGE /a")

		name := chi.URLParam(r, "name")
		page := &Page{
			Path: "/a",
			Data: map[string]string{
				"DATA": "A DATA (')",
			},
			Params: map[string]string{
				"name": name,
			},
		}
		render(page, w, r)
	})

	chr.Get("/b/*", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("PAGE /b")

		path := chi.URLParam(r, "*")
		page := &Page{
			Path: "/b",
			Data: map[string]string{
				"DATA": "B DATA (')",
			},
			Params: map[string]string{
				"default": "@",
				"path":    path,
			},
		}
		render(page, w, r)
	})

	chr.Get("/", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("PAGE /")

		page := &Page{
			Path: "/",
			Data: map[string]string{
				"DATA": "ROOT DATA (')",
			},
			Params: map[string]string{
				"default": "/",
			},
		}
		render(page, w, r)
	})

	if assets[path] {
		w.Header().Set("Cache-Control", "public, max-age=31536000, immutable")
		log.Printf("STATIC: %s\n", path)
		http.FileServer(httpFS).ServeHTTP(w, r)
		return
	}

	chr.ServeHTTP(w, r)
}

func render(page *Page, w http.ResponseWriter, r *http.Request) {
	path := page.Path
	if !strings.HasSuffix(path, "/") {
		path += "/"
	}
	path += "index.html"
	log.Printf("RENDER: %s [%s]\n", path, r.URL.Path)

	path = "pages" + path

	content, err := fs.ReadFile(staticFS, path)
	if err != nil {
		http.Error(w, fmt.Sprintf("error read file: %s", err), http.StatusInternalServerError)
		return
	}

	content = bytes.Replace(content, []byte("{}"), []byte("{{ . }}"), 1)

	w.Header().Set("Content-Type", "text/html")
	t := template.Must(template.New("page").Parse(string(content)))

	page.Commit = strings.TrimSpace(commit)
	log.Printf(" > PAGE DATA: %#v\n", page.Data)
	err = t.Execute(w, page)
	if err != nil {
		http.Error(w, fmt.Sprintf("error execute template: %s", err), http.StatusInternalServerError)
		return
	}
}
