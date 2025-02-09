package main

import (
	"encoding/json"
	"fmt"
	"html/template"
	"io"
	"log"
	"net/http"
	"os"
	"runtime"
	"strconv"
	"strings"
	"time"

	"cloud.google.com/go/compute/metadata"
	"github.com/dustin/go-humanize"
	_ "golang.org/x/crypto/x509roots/fallback"
)

type Writer struct {
	writer  io.Writer
	started time.Time
	size    uint64
	block   uint64
}

const blockSize = 1024 * 1024 * 50

func (w *Writer) Write(p []byte) (n int, err error) {
	n = len(p)
	w.size += uint64(n)
	w.block += uint64(n)
	if w.block > blockSize {
		elapsed := time.Since(w.started)
		throughput := float64(w.size) / elapsed.Seconds()
		fmt.Fprintf(
			w.writer, "block %s/%s | throughput %s | elapsed %s\n",
			humanize.Bytes(w.block), humanize.Bytes(w.size),
			humanize.Bytes(uint64(throughput)),
			elapsed,
		)
		w.block = w.block - blockSize
		w.writer.(http.Flusher).Flush()
	}
	return
}

const large = "http://ipv4.download.thinkbroadband.com/512MB.zip"

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

	http.HandleFunc("/speed", func(w http.ResponseWriter, r *http.Request) {
		r, err := http.NewRequest("GET", large, nil)
		r.Header.Add("User-Agent", "Mozilla/5.0")
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		resp, err := http.DefaultClient.Do(r)
		fmt.Println("response status:", resp.Status)
		defer resp.Body.Close()

		w.Header().Set("X-Content-Type-Options", "nosniff")

		started := time.Now()
		ww := &Writer{started: started, writer: w}
		fmt.Fprintln(w, "started at", started)
		written, err := io.Copy(ww, resp.Body)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		elapsed := time.Since(started)
		throughput := float64(ww.size) / elapsed.Seconds()
		fmt.Fprintf(
			w, "downloaded %s | throughput %s | elapsed %s\n",
			humanize.Bytes(uint64(written)),
			humanize.Bytes(uint64(throughput)),
			elapsed,
		)
	})

	fs := http.FileServer(http.Dir("/"))
	http.Handle("/fs/", http.StripPrefix("/fs/", fs))

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

	http.HandleFunc("GET /ls/{path...}", ls("/ls"))

	http.ListenAndServe(":"+port, nil)
}

func ls(prefix string) http.HandlerFunc {
	fmt.Println("prefix", prefix)
	return func(w http.ResponseWriter, r *http.Request) {
		path := strings.TrimPrefix(r.URL.Path, prefix)
		fmt.Println("URL", r.URL.Path, "->", "path", path)

		fi, err := os.Stat(path)
		if err != nil {
			log.Println(err)
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		if !fi.IsDir() {
			http.ServeFile(w, r, path)
			return
		}

		files, err := os.ReadDir(path)
		if err != nil {
			log.Println(err)
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		type FileInfo struct {
			Name    string
			Size    int64
			ModTime string
			IsDir   bool
		}

		var fileList []FileInfo

		for _, file := range files {
			info, err := file.Info()
			if err != nil {
				continue
			}
			fileList = append(fileList, FileInfo{
				Name:    info.Name(),
				Size:    info.Size(),
				ModTime: info.ModTime().Format("2006-01-02 15:04:05"),
				IsDir:   info.IsDir(),
			})
		}

		tmpl, err := template.New("filelist").Parse(`
        <table>
            <thead>
                <tr><th>name</th><th>size</th><th>modified</th></tr>
            </thead>
            <tbody>
                {{range .}}
                <tr>
                    <td><a href="` + prefix + path + `/{{.Name}}">{{.Name}}</a></td>
                    <td>
						{{if not .IsDir}}
						{{.Size}} bytes
						{{end}}
					</td>
                    <td>{{.ModTime}}</td>
                </tr>
                {{end}}
            </tbody>
        </table>`)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		err = tmpl.Execute(w, fileList)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
		}
	}
}
