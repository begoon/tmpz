package main

import (
	"log"
	"net/http"
	"os"
	"strings"

	"go-vercel/api"
)

//go:generate tailwindcss -m -i tailwind.css -o api/static/styles.css

func loadEnv() {
	envfile := ".env"
	if env := os.Getenv("ENV"); env != "" {
		envfile = "." + env + ".env"
		_, err := os.Stat(envfile)
		log.Fatalf("error loading %s: %s", envfile, err)
	}
	content, err := os.ReadFile(envfile)
	if err != nil && envfile != ".env" {
		log.Fatalf("error reading %s: %s", envfile, err)
	}
	for _, line := range strings.Split(string(content), "\n") {
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, "#") {
			continue
		}
		if name, value, found := strings.Cut(line, "="); !found {
			log.Fatalf("error parsing %s: invalid line: %s", envfile)
		} else {
			name = strings.TrimSpace(name)
			value = strings.TrimSpace(value)
			log.Printf("%s=%s", name, value)
			os.Setenv(name, value)
		}
	}
}

func init() {
	loadEnv()
}

func main() {
	http.HandleFunc("/", api.Handler)
	http.ListenAndServe(":8000", nil)
}
