package main

import (
	"embed"
	_ "embed"
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
)

type Document struct {
	Name  string
	Path  string
	Text  string
	Score float64

	PathLower string
}

var (
	documents  []Document
	tfidfIndex map[string]map[string]float64
)

var rootDir = "data"

func loadDocuments() {
	skip := func(v string) bool {
		return !strings.HasPrefix(v, rootDir)
	}

	err := fastwalk.Walk(nil, rootDir, func(path string, info fs.DirEntry, err error) error {
		if err != nil {
			log.Printf("error accessing path %q: %v\n", path, err)
			return err
		}
		if !info.IsDir() && !skip(path) {
			content, err := os.ReadFile(path)
			if err != nil {
				log.Printf("error reading file %s: %v", path, err)
				return nil
			}
			text := strings.ToLower(string(content))
			relativePath := strings.TrimPrefix(path, rootDir)
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
		log.Fatalf("error walking the path %q: %v\n", rootDir, err)
	}
	fmt.Printf("loaded %d documents\n", len(documents))
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
}

func search(query string, exact bool, version string) ([]Document, []Document) {
	query = strings.ToLower(query)

	words := strings.Fields(query)

	scores := make(map[string]float64)

	var foundDocuments []Document
	var foundFiles []Document

	if exact {
		for _, document := range documents {
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
	http.Redirect(w, r, "/", http.StatusSeeOther)
}

func searchHandler(w http.ResponseWriter, r *http.Request) {
	htmx := r.Header.Get("HX-Request") != ""

	query := r.URL.Query()

	q := query.Get("q")
	exact := query.Get("exact")
	version := query.Get("v")

	if version != "" {
		http.SetCookie(w, &http.Cookie{
			Name:   "version",
			Value:  version,
			Path:   "/",
			MaxAge: 60 * 60 * 24 * 365,
		})
		w.Header().Set("HX-Redirect", "/!")
		return
	} else {
		cookie, err := r.Cookie("version")
		if err == nil {
			version = cookie.Value
		}
	}

	if version == "" {
		version = "3.5.0"
	}
	fmt.Printf("search %q exact=%t version=%s\n", q, exact != "", version)

	var tmpl *template.Template
	context := struct {
		Query          string
		Exact          string
		FoundDocuments []Document
		FoundFiles     []Document
		Version        string
	}{Query: q, Exact: exact, Version: version}

	if context.Query != "" {
		started := time.Now()
		documents, files := search(context.Query, context.Exact != "", version)
		context.FoundDocuments = documents
		context.FoundFiles = files
		fmt.Printf("found %d documents in %s\n", len(context.FoundDocuments), time.Since(started))
	}

	templName := "search.html"
	if htmx {
		templName = "results.html"
	}
	tmpl = template.Must(template.ParseFiles("templates/" + templName))
	tmpl.Execute(w, context)
}

//go:embed data/*
var data embed.FS

var fileServer = http.FileServer(http.Dir("./data"))

func fileHandler(w http.ResponseWriter, r *http.Request) {
	version := "3.5.0"
	cookie, err := r.Cookie("version")
	if err == nil {
		version = cookie.Value
	}
	if r.URL.Path == "/" {
		r.URL.Path = "/DOCUMENTATION.html"
	}
	r.URL.Path = version + r.URL.Path
	fmt.Printf("fileserver %s %s\n", version, r.URL.Path)
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("Pragma", "no-cache")
	w.Header().Set("Expires", "0")
	fileServer.ServeHTTP(w, r)
}

func main() {
	started := time.Now()
	loadDocuments()
	fmt.Printf("loaded documents in %s\n", time.Since(started))

	started = time.Now()
	buildIndex()
	fmt.Printf("built index in %s\n", time.Since(started))

	http.HandleFunc("GET /!", searchHandler)
	http.HandleFunc("GET /v/{version}", versionHandler)
	http.HandleFunc("/{path...}", fileHandler)

	fmt.Println("listening on :8000")
	http.ListenAndServe(":8000", nil)
}
