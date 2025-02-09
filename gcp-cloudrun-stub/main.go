package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"runtime"
	"strconv"
	"strings"

	"cloud.google.com/go/compute/metadata"
	_ "golang.org/x/crypto/x509roots/fallback"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		env := os.Environ()
		for _, e := range env {
			w.Write([]byte(e + "\n"))
		}
		ctx := r.Context()

		ok := func(v string, err error) string {
			if err != nil {
				return err.Error()
			}
			return v
		}

		cpu := strconv.Itoa(runtime.NumCPU())
		w.Write([]byte("CPU=" + cpu + "\n"))

		gce := metadata.OnGCE()
		w.Write([]byte("GGE=" + strconv.FormatBool(gce) + "\n"))

		if gce {
			w.Write([]byte("\n"))
			w.Write([]byte("project=" + ok(metadata.ProjectIDWithContext(ctx)) + "\n"))
			w.Write([]byte("project_id=" + ok(metadata.NumericProjectIDWithContext(ctx)) + "\n"))
			w.Write([]byte("zone=" + ok(metadata.ZoneWithContext(ctx)) + "\n"))
			w.Write([]byte("email=" + ok(metadata.EmailWithContext(ctx, "")) + "\n"))
		}
	})

	http.HandleFunc("/fs/", func(w http.ResponseWriter, r *http.Request) {
		r.URL.Path = strings.TrimPrefix(r.URL.Path, "/fs")
		http.FileServer(http.Dir("/")).ServeHTTP(w, r)
	})

	http.HandleFunc("/ip", func(w http.ResponseWriter, r *http.Request) {
		resp, err := http.Get("https://api.myip.com/")
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		defer resp.Body.Close()
		fmt.Println("response status:", resp.Status)

		v := struct {
			IP string `json:"ip"`
		}{}
		err = json.NewDecoder(resp.Body).Decode(&v)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Write([]byte(v.IP))
	})

	http.ListenAndServe(":"+port, nil)
}
