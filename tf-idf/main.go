package main

import (
	"bytes"
	"context"
	"embed"
	_ "embed"
	"encoding/gob"
	"encoding/json"
	"flag"
	"fmt"
	"html/template"
	"io/fs"
	"log"
	"math"
	"net/http"
	"os"
	"sort"
	"strings"
	"time"

	"github.com/charlievieth/fastwalk"
	"github.com/dustin/go-humanize"
	"github.com/joho/godotenv"
)

type Document struct {
	Name  string
	Path  string
	Text  string
	Link  string
	Score float64

	PathLower string
}

var (
	documents []Document
	index     map[string]map[string]float64
)

var dataDir = "data"

var versions = []string{"2.4.4", "2.5.0", "2.6.0", "2.7.0", "3.1.0", "3.3.0", "3.4.0", "3.5.0"}

var debug = os.Getenv("DEBUG") != ""

var documentsSize int

func loadDocumentsFS() {
	documentsSize = 0

	skip := func(v string) bool {
		return !strings.HasPrefix(v, dataDir)
	}

	err := fastwalk.Walk(nil, dataDir, func(path string, info fs.DirEntry, err error) error {
		if err != nil {
			log.Printf("error accessing path %q: %v\n", path, err)
			return err
		}
		if info.IsDir() || skip(path) {
			return nil
		}
		content, err := os.ReadFile(path)
		if err != nil {
			log.Fatalf("error reading file %s: %v", path, err)
			return nil
		}
		documentsSize += len(content)

		relativePath := strings.TrimPrefix(path, dataDir)
		documents = append(documents, Document{
			Name:      info.Name(),
			Path:      relativePath,
			Text:      strings.ToLower(string(content)),
			PathLower: strings.ToLower(relativePath),
			Score:     0,
		})
		return nil
	})
	if err != nil {
		log.Fatalf("error walking the path %q: %v\n", dataDir, err)
	}
	fmt.Printf("fs: loaded %d documents [%s]\n", len(documents), humanize.Comma(int64(documentsSize)))
}

func loadDocumentsEmbed() {
	documentsSize = 0

	skip := func(v string) bool {
		return !strings.HasPrefix(v, dataDir)
	}

	started := time.Now()

	err := fs.WalkDir(dataEmbedFS, ".", func(path string, info fs.DirEntry, err error) error {
		if err != nil {
			log.Printf("error accessing path %q: %v\n", path, err)
			return err
		}
		if !info.IsDir() && !skip(path) {
			content, err := fs.ReadFile(dataEmbedFS, path)
			if err != nil {
				log.Printf("error reading file %s: %v", path, err)
				return nil
			}
			documentsSize += len(content)

			text := strings.ToLower(string(content))
			relativePath := strings.TrimPrefix(path, dataDir)
			pathLower := strings.ToLower(relativePath)
			documents = append(documents, Document{
				Name:      info.Name(),
				Path:      relativePath,
				Text:      text,
				Score:     0,
				PathLower: pathLower,
			})
		}
		return nil
	})
	if err != nil {
		log.Fatalf("error walking the path %q: %v\n", dataDir, err)
	}

	duration := time.Since(started)
	fmt.Printf("embed: loaded %d documents / %d bytes in %s\n", len(documents), documentsSize, duration)
}

func buildIndex() {
	index = make(map[string]map[string]float64)
	number := len(documents)

	for _, document := range documents {
		words := strings.Fields(document.Text)
		wordCount := make(map[string]int)

		for _, word := range words {
			wordCount[word]++
		}

		for word, count := range wordCount {
			if index[word] == nil {
				index[word] = make(map[string]float64)
			}
			tf := float64(count) / float64(len(words))
			index[word][document.Name] = tf
		}
	}

	for word, documentMap := range index {
		frequency := float64(len(documentMap))
		idf := math.Log(float64(number) / (1 + frequency))
		for document, tf := range documentMap {
			index[word][document] = tf * idf
		}
	}
	fmt.Printf("build index with %d words\n", len(index))
}

func storeIndex() {
	indexGob, err := os.Create("index.gob")
	if err != nil {
		log.Fatalf("error creating index file: %v", err)
		os.Exit(1)
	}
	defer indexGob.Close()

	encoder := gob.NewEncoder(indexGob)
	if err := encoder.Encode(index); err != nil {
		log.Fatalf("error encoding index: %v", err)
		os.Exit(1)
	}
	fmt.Printf("store index\n")
}

//go:embed index.gob
var IndexGob []byte

func loadIndex() {
	decoder := gob.NewDecoder(bytes.NewReader(IndexGob))
	if err := decoder.Decode(&index); err != nil {
		log.Fatalf("error decoding index: %v", err)
		os.Exit(1)
	}
	fmt.Printf("load index with %d words\n", len(index))
}

func search(query string, exact bool, version string) (foundDocuments []Document, foundFiles []Document) {
	query = strings.ToLower(query)

	version = "/" + version + "/"
	if exact {
		for _, document := range documents {
			if !strings.HasPrefix(document.Path, version) {
				continue
			}
			contentMatch := strings.Contains(document.Text, query)
			pathMatch := strings.Contains(document.PathLower, query)

			if contentMatch || pathMatch {
				document := Document{
					Name:  document.Name,
					Path:  document.Path,
					Text:  document.Text,
					Link:  strings.TrimPrefix(document.Path, version),
					Score: 1,
				}
				if contentMatch {
					foundDocuments = append(foundDocuments, document)
				}
				if pathMatch {
					foundFiles = append(foundFiles, document)
				}
			}
		}
	} else {
		scores := make(map[string]float64)
		words := strings.Fields(query)

		for _, word := range words {
			for document, tfidf := range index[word] {
				scores[document] += tfidf
			}
		}

		for _, document := range documents {
			if !strings.HasPrefix(document.Path, version) {
				continue
			}
			pathMatch := false
			for _, word := range words {
				if strings.Contains(document.PathLower, word) {
					pathMatch = true
					break
				}
			}
			score, found := scores[document.Name]
			if (found && score > 0) || pathMatch {
				document := Document{
					Name:  document.Name,
					Path:  document.Path,
					Text:  document.Text,
					Link:  strings.TrimPrefix(document.Path, version),
					Score: score,
				}
				if found && score > 0 {
					foundDocuments = append(foundDocuments, document)
				}
				if pathMatch {
					foundFiles = append(foundFiles, document)
				}
			}
		}
		sort.Slice(foundDocuments, func(i, j int) bool {
			return foundDocuments[i].Score > foundDocuments[j].Score
		})
	}
	return foundDocuments, foundFiles
}

func htmx(r *http.Request) bool {
	return r.Header.Get("HX-Request") != ""
}

type rankoneVersion struct{}

func versionHandler(w http.ResponseWriter, r *http.Request) {
	htmx := htmx(r)

	version := r.PathValue("version")
	fmt.Printf("version %s %t\n", version, htmx)

	http.SetCookie(w, &http.Cookie{
		Name:   "version",
		Value:  version,
		Path:   "/",
		MaxAge: 60 * 60 * 24 * 365,
	})

	if !htmx {
		http.Redirect(w, r, "/DOCUMENTATION.html", http.StatusSeeOther)
		return
	}

	ctx := context.WithValue(r.Context(), rankoneVersion{}, version)
	searchHandler(w, r.WithContext(ctx))
}

func searchHandler(w http.ResponseWriter, r *http.Request) {
	if !basicAuth(w, r) {
		return
	}

	htmx := htmx(r)

	query := r.URL.Query()

	q := query.Get("q")
	exact := query.Get("exact")

	version := versions[len(versions)-1]
	if r.Context().Value("version") != nil {
		version = r.Context().Value(rankoneVersion{}).(string)
		fmt.Println("version/context", version)
	} else if cookie, err := r.Cookie("version"); err == nil {
		version = cookie.Value
	}

	fmt.Printf("search exact=%t version=%s %s\n", exact != "", version, q)

	context := struct {
		Query          string
		Exact          string
		FoundDocuments []Document
		FoundFiles     []Document
		Version        string
		Versions       []string
	}{Query: q, Exact: exact, Version: version, Versions: versions}

	if context.Query != "" {
		started := time.Now()
		documents, files := search(context.Query, context.Exact != "", version)
		context.FoundDocuments = documents
		context.FoundFiles = files
		fmt.Printf("found %d documents in %s\n", len(context.FoundDocuments), time.Since(started))
	}

	templName := "search"
	if htmx {
		templName = "results"
	}
	templates.ExecuteTemplate(w, templName, context)
}

//go:embed templates/*
var templatesEmbedFS embed.FS

var templatesFS = must(fs.Sub(templatesEmbedFS, "templates"))

var templates = template.Must(template.ParseFS(templatesFS, "*.html"))

//go:embed data/*
var dataEmbedFS embed.FS

var dataFS = must(fs.Sub(dataEmbedFS, "data"))

var fileServer = http.FileServer(http.FS(dataFS))

//go:embed .env
var envEmbed string

var defaultEnv = must(godotenv.Parse(strings.NewReader(envEmbed)))

func init() {
	for name, value := range defaultEnv {
		os.Setenv(name, value)
	}
	explicitEnv := os.Getenv("ALLOWED_USERS")
	if explicitEnv != "" {
		err := godotenv.Load(explicitEnv)
		if err != nil {
			log.Printf("error reading allowed users: %v", err)
		}
	}
	for _, v := range os.Environ() {
		if strings.HasPrefix(v, "USER_") {
			user, _, _ := strings.Cut(v, "=")
			fmt.Println(user)
		}
	}
}

func basicAuth(w http.ResponseWriter, r *http.Request) bool {
	user, pass, ok := r.BasicAuth()
	if ok {
		envPass := os.Getenv("USER_" + user)
		if envPass != "" && envPass == pass {
			return true
		}
	}
	w.Header().Set("WWW-Authenticate", `Basic realm="Restricted"`)
	http.Error(w, "Unauthorized", http.StatusUnauthorized)
	return false
}

func fileHandler(w http.ResponseWriter, r *http.Request) {
	if !basicAuth(w, r) {
		return
	}

	version := "3.5.0"
	cookie, err := r.Cookie("version")
	if err == nil {
		version = cookie.Value
	}

	url := r.URL
	rawPath := url.Path

	raw := r.URL.Query().Get("r")

	if raw == "" && url.Path == "/" {
		url.Path = "/DOCUMENTATION.html"
	}
	url.Path = version + url.Path

	if debug {
		fmt.Printf("file [%s] [%s] [%s] r=[%s]\n", rawPath, url.Path, version, raw)
	}

	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("Pragma", "no-cache")
	w.Header().Set("Expires", "0")

	if rawPath == "/html/" {
		content, err := fs.ReadFile(dataFS, url.Path+"index.html")
		if err != nil {
			http.Error(w, "index.html", http.StatusNotFound)
			return
		}
		w.Write(content)
		w.Write([]byte(versionSelector(version)))
	} else {
		fileServer.ServeHTTP(w, r)
	}
}

func Indexer() {
	loadDocumentsFS()
	buildIndex()
	storeIndex()
}

var flagIndex = flag.Bool("index", false, "index documents")

func main() {
	flag.Parse()

	if *flagIndex {
		Indexer()
		return
	}

	fmt.Printf("embed: index: %d\n", len(IndexGob))

	loadDocumentsEmbed()
	loadIndex()

	http.HandleFunc("GET /-", searchHandler)
	http.HandleFunc("GET /version/{version}", versionHandler)
	http.HandleFunc("/{path...}", fileHandler)
	http.HandleFunc("GET /health", healthHandler)

	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}
	fmt.Println("listening on :" + port)
	http.ListenAndServe(":"+port, nil)
}

//go:embed VERSION.txt
var version string

//go:embed TAG.txt
var tag string

func healthHandler(w http.ResponseWriter, r *http.Request) {
	health := struct {
		Version   string   `json:"version"`
		TAG       string   `json:"tag"`
		Versions  []string `json:"versions"`
		Words     int      `json:"index"`
		Documents int      `json:"documents"`
		Data      string   `json:"data"`
	}{
		Version:   version,
		TAG:       tag,
		Versions:  versions,
		Words:     len(index),
		Documents: len(documents),
		Data:      humanize.Comma(int64(documentsSize)),
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(health)
}

func must[T any](x T, err error) T {
	if err != nil {
		panic(err)
	}
	return x
}

func versionSelector(current string) string {
	html := ""
	for _, v := range versions {
		style := ""
		if v == current {
			style = "color: white; background: #208eee;"
		}
		html += fmt.Sprintf(
			`<a style="margin-left: 2px; margin-right: 2px; padding-left: 2px; padding-right: 2px; %s" href="/version/%s" >%s</a>`,
			style, v, v,
		)
	}
	return fmt.Sprintf(versionSelectorFormat, html)
}

const versionSelectorFormat = `
<script>
	const body = document.querySelector('body')
	const div = document.createElement('div')
	div.style.position = 'fixed'
	div.style.top = '0'
	div.style.right = '0'
	div.style.background = 'white'
	div.innerHTML = '<a href="/-" class="text-decoration-line: underline;">search</a> %s'
	body.appendChild(div)
	body.onkeydown = (e) => (e.key === 'k' && e.metaKey) ? window.location = '/-' : null;
</script>
`
