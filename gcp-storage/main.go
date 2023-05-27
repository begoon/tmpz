package main

import (
	"context"
	"encoding/json"
	"log"

	"cloud.google.com/go/storage"
)

const bucket = "alexander-test"

func main() {
	v := struct {
		Name string `json:"name"`
		Size int    `json:"size"`
	}{
		Name: "test",
		Size: 1,
	}
	err := StorageSave(bucket, "test.json", v)
	if err != nil {
		log.Fatalf("error saving: %v", err)
	}
	log.Println("saved")
}

func StorageSave(bucket string, name string, v interface{}) error {
	ctx := context.TODO()
	client, err := storage.NewClient(ctx)
	if err != nil {
		return err
	}
	w := client.Bucket(bucket).Object(name).NewWriter(ctx)
	defer func() {
		_ = w.Close()
	}()

	w.ContentType = "application/json"
	b, err := json.Marshal(&v)
	if err != nil {
		return err
	}
	_, err = w.Write(b)
	return err
}
