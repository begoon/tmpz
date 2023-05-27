package main

import (
	"context"
	"log"
	"math/rand"
	"time"

	"cloud.google.com/go/firestore"
	"github.com/google/uuid"
)

const project = "iproov-chiro"

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
	ctx := context.Background()
	c, err := firestore.NewClient(ctx, project)
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
		log.Fatalf("error creating image file: %v", err)
	}

	_, err = txr.Update(ctx, []firestore.Update{
		{Path: "Metadata", Value: "updated-metadata-" + rv()},
	})
	if err != nil {
		log.Fatalf("error updating transaction: %v", err)
	}

	_, err = files.Doc("crop").Create(ctx, File{
		FileName:  "crop-" + rv() + ".png",
		Size:      rand.Intn(256),
		Path:      rv() + "/" + rv(),
		CreatedAt: time.Now(),
	})
	if err != nil {
		log.Fatalf("error creating crop file: %v", err)
	}
}
