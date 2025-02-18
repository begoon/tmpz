package main

import (
	"context"
	"embed"
	"flag"
	"fmt"
	"io/fs"
	"net/http"
	"os"
	"time"

	"github.com/chromedp/cdproto/page"
	"github.com/chromedp/chromedp"
)

func must[T any](x T, err error) T {
	if err != nil {
		panic(err)
	}
	return x
}

//go:embed content/*.*
var contentFS embed.FS

var (
	dataFS     = must(fs.Sub(contentFS, "content"))
	fileServer = http.FileServer(http.FS(dataFS))
)

func main() {
	flagHTTP := flag.Bool("http", false, "run http server")
	flag.Parse()

	ready := make(chan struct{})
	url := "http://localhost:8000"

	http.Handle("/", fileServer)

	go func() {
		ready <- struct{}{}
		err := http.ListenAndServe(":8000", nil)
		fmt.Println(err)
	}()

	<-ready
	fmt.Println("listening on :8000")

	ctx, cancel := chromedp.NewContext(context.Background())
	defer cancel()

	if *flagHTTP {
		select {}
	}

	ctx, cancel = context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	r, err := http.Get(url + "/index.html")
	if err != nil {
		fmt.Println("get html:", err)
		return
	}
	defer r.Body.Close()
	fmt.Println("html fetched", r.Status, r.ContentLength)

	var b []byte

	started := time.Now()
	err = chromedp.Run(ctx,
		chromedp.Navigate(url),
		chromedp.ActionFunc(func(ctx context.Context) error {
			var err error
			b, _, err = page.PrintToPDF().
				WithPrintBackground(true).
				WithScale(1.0).
				WithPaperHeight(11.66).
				WithPaperWidth(8.25).
				WithTransferMode(page.PrintToPDFTransferModeReturnAsBase64).
				Do(ctx)
			return err
		}),
	)
	if err != nil {
		fmt.Println("create pdf:", err)
		return
	}

	fmt.Println("pdf created in", time.Since(started))

	outfile := os.Getenv("OUTFILE")
	if outfile == "" {
		outfile = "example-go.pdf"
	}
	err = os.WriteFile(outfile, b, 0o644)
	if err != nil {
		fmt.Println("save pdf:", err)
		return
	}
	fmt.Println("pdf saved:", outfile)
}
