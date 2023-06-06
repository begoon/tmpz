package main

import (
	"context"
	_ "embed"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"os"

	"cloud.google.com/go/storage"
	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
)

//go:embed index.html
var index []byte

func main() {
	e := echo.New()

	e.HideBanner = true
	e.Use(middleware.CORS())

	e.GET("/", func(c echo.Context) error {
		return c.Blob(200, "text/html", index)
	})

	e.POST("/upload", func(c echo.Context) error {
		file, err := c.FormFile("file")
		if err != nil {
			return err
		}
		log.Println("file", file.Filename, file.Size, file.Header.Get("Content-Type"))
		err = Save("dropzone", file)
		if err != nil {
			log.Printf("error saving file to bucket: %v", err)
			return err
		}
		log.Println("file saved")
		return c.NoContent(200)
	})

	e.Logger.Fatal(e.Start(":8000"))
}

func Save(bucket string, file *multipart.FileHeader) error {
	ctx := context.TODO()
	client, err := storage.NewClient(ctx)
	if err != nil {
		return fmt.Errorf("error storing [%s] to [%s]: %v", file.Filename, bucket, err)
	}
	w := client.Bucket(bucket).Object(file.Filename).NewWriter(ctx)
	w.ContentType = file.Header.Get("Content-Type")
	defer func() {
		_ = w.Close()
	}()

	r, err := file.Open()
	if err != nil {
		return fmt.Errorf("error opening file [%s]: %v", file.Filename, err)
	}
	defer r.Close()
	if _, err := io.Copy(w, r); err != nil {
		return fmt.Errorf("error storing [%s]: %v", file.Filename, err)
	}
	return nil
}

func SaveFile(file *multipart.FileHeader) error {
	src, err := file.Open()
	if err != nil {
		return err
	}
	defer src.Close()

	dst, err := os.Create("uploads/" + file.Filename)
	if err != nil {
		return err
	}
	defer dst.Close()

	if _, err = io.Copy(dst, src); err != nil {
		return err
	}
	return nil
}
