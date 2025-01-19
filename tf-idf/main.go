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

	"github.com/joho/godotenv"

	"github.com/charlievieth/fastwalk"
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
	documents  []Document
	tfidfIndex map[string]map[string]float64
)

var dataDir = "data"

var loadDocuments = loadDocumentsEmbed

var verions = []string{"2.4.4", "2.5.0", "2.6.0", "2.7.0", "3.1.0", "3.3.0", "3.4.0", "3.5.0"}

func loadDocumentsFS() {
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
	fmt.Printf("loaded %d documents\n", len(documents))
}

func loadDocumentsEmbed() {
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

	fmt.Printf("embed: loaded %d documents in %s\n", len(documents), duration)
}

func buildIndex() {
	tfidfIndex = make(map[string]map[string]float64)
	number := len(documents)

	for _, document := range documents {
		words := strings.Fields(document.Text)
		wordCount := make(map[string]int)

		for _, word := range words {
			wordCount[word]++
		}

		for word, count := range wordCount {
			if tfidfIndex[word] == nil {
				tfidfIndex[word] = make(map[string]float64)
			}
			tf := float64(count) / float64(len(words))
			tfidfIndex[word][document.Name] = tf
		}
	}

	for word, documentMap := range tfidfIndex {
		frequency := float64(len(documentMap))
		idf := math.Log(float64(number) / (1 + frequency))
		for document, tf := range documentMap {
			tfidfIndex[word][document] = tf * idf
		}
	}

	fmt.Printf("build index with %d words\n", len(tfidfIndex))

	indexGob, err := os.Create("index.gob")
	if err != nil {
		log.Fatalf("error creating index file: %v", err)
		os.Exit(1)
	}
	defer indexGob.Close()

	encoder := gob.NewEncoder(indexGob)
	if err := encoder.Encode(tfidfIndex); err != nil {
		log.Fatalf("error encoding index: %v", err)
		os.Exit(1)
	}

	fmt.Printf("write index to index.gob\n")
}

func search(query string, exact bool, version string) (foundDocuments []Document, foundFiles []Document) {
	query = strings.ToLower(query)

	words := strings.Fields(query)

	scores := make(map[string]float64)

	version = "/" + version + "/"
	if exact {
		for _, document := range documents {
			fmt.Println(document.Path)
			if !strings.HasPrefix(document.Path, version) {
				continue
			}
			pathMatch := strings.Contains(document.PathLower, query)
			match := strings.Contains(document.Text, query)

			if match || pathMatch {
				document := Document{
					Name:  document.Name,
					Path:  document.Path,
					Text:  document.Text,
					Link:  strings.TrimPrefix(document.Path, version),
					Score: 1,
				}
				if match {
					foundDocuments = append(foundDocuments, document)
				}
				if pathMatch {
					foundFiles = append(foundFiles, document)
				}
			}
		}
	} else {
		for _, word := range words {
			for document, tfidf := range tfidfIndex[word] {
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

func versionHandler(w http.ResponseWriter, r *http.Request) {
	htmx := r.Header.Get("HX-Request") != ""

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

	q := r.URL.Query().Get("q")
	exact := r.URL.Query().Get("exact")
	fmt.Println(q, exact)

	ctx := context.WithValue(r.Context(), "version", version)
	searchHandler(w, r.WithContext(ctx))
}

func searchHandler(w http.ResponseWriter, r *http.Request) {
	if !basicAuth(w, r) {
		return
	}

	htmx := r.Header.Get("HX-Request") != ""

	query := r.URL.Query()
	fmt.Println(query)

	q := query.Get("q")
	exact := query.Get("exact")

	version := "3.5.0"
	if r.Context().Value("version") != nil {
		version = r.Context().Value("version").(string)
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
	}{Query: q, Exact: exact, Version: version, Versions: verions}

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
var env string

var ENV = must(godotenv.Parse(strings.NewReader(env)))

func init() {}

func basicAuth(w http.ResponseWriter, r *http.Request) bool {
	user, pass, ok := r.BasicAuth()
	if ok {
		envPass := ENV["USER_"+user]
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

	fmt.Printf("file [%s] [%s] [%s] r=[%s]\n", rawPath, url.Path, version, raw)

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
	loadDocuments()
	buildIndex()
}

//go:embed index.gob
var IndexGob []byte

func loadIndex() {
	decoder := gob.NewDecoder(bytes.NewReader(IndexGob))
	if err := decoder.Decode(&tfidfIndex); err != nil {
		log.Fatalf("error decoding index: %v", err)
		os.Exit(1)
	}
	fmt.Printf("loaded index with %d words\n", len(tfidfIndex))
}

var flagIndex = flag.Bool("index", false, "index documents")

func main() {
	flag.Parse()

	if *flagIndex {
		Indexer()
		return
	}

	fmt.Printf("loaded index: %d\n", len(IndexGob))

	loadDocuments()
	loadIndex()

	http.HandleFunc("GET /-", searchHandler)
	http.HandleFunc("GET /version/{version}", versionHandler)
	http.HandleFunc("/{path...}", fileHandler)
	http.HandleFunc("GET /health", healthHandler)

	fmt.Println("listening on :8000")
	http.ListenAndServe(":8000", nil)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	health := struct {
		Version string `json:"version"`
	}{
		Version: "0.0.0",
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
	for _, v := range verions {
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
