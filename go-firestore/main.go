package main

import (
	"context"
	"log"
	"math/rand"
	"os"
	"time"

	"cloud.google.com/go/firestore"
	"github.com/google/uuid"
	option "google.golang.org/api/option"

	"github.com/joho/godotenv"
)

type File struct {
	FileName  string
	Size      int
	Path      string
	CreatedAt time.Time
}

type Transaction struct {
	Metadata string
	Created  time.Time
}

func rv() string {
	return uuid.New().String()
}

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Fatalf("load .env: %v", err)
	}

	credentialsFile := os.Getenv("GOOGLE_APPLICATION_CREDENTIALS")
	if credentialsFile == "" {
		log.Fatal("GOOGLE_APPLICATION_CREDENTIALS is not set")
	}

	project := os.Getenv("PROJECT")
	if project == "" {
		log.Fatal("PROJECT is not set")
	}

	ctx := context.Background()
	c, err := firestore.NewClient(ctx, project, option.WithCredentialsFile(credentialsFile))
	if err != nil {
		log.Fatalf("error creating client: %v", err)
	}
	defer c.Close()

	id := rv()
	log.Println("id", id)

	txr := c.Collection("storage").Doc(id)

	tx := Transaction{Metadata: "metadata-" + rv(), Created: time.Now()}
	_, err = txr.Create(ctx, tx)
	if err != nil {
		log.Fatalf("error creating transaction: %v", err)
	}

	files := txr.Collection("files")

	_, err = files.Doc("image").Create(ctx, File{
		FileName:  "image-" + rv() + ".png",
		Size:      rand.Intn(256),
		Path:      rv() + "/" + rv(),
		CreatedAt: time.Now(),
	})
	if err != nil {
		log.Fatalf("creating image file: %v", err)
	}

	_, err = txr.Update(ctx, []firestore.Update{
		{Path: "Metadata", Value: "updated-metadata-" + rv()},
	})
	if err != nil {
		log.Fatalf("updating transaction: %v", err)
	}

	svg, err := os.ReadFile("gopher.svg")
	if err != nil {
		log.Fatalf("read gopher.svg: %v", err)
	}
	_, err = files.Doc("gopher.svg").Set(ctx, struct{ SVG []byte }{[]byte(svg)})
	if err != nil {
		log.Fatalf("creating svg file: %v", err)
	}
}
