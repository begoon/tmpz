package main

import (
	"encoding/hex"
	"flag"
	"fmt"
	"log"

	"google.golang.org/protobuf/encoding/protojson"
	pb "google.golang.org/protobuf/proto"

	"github.com/bufbuild/protovalidate-go"

	"go-protovalidate/internal/proto"
)

func main() {
	name := flag.String("name", "Alice", "name of the user")
	age := flag.Int("age", 30, "age of the user")
	email := flag.String("email", "a@test.com", "email of the user")
	price := flag.String("price", "$0.1", "price")
	quantity := flag.String("quantity", "1.5", "quantity")
	flag.Parse()

	user := &proto.User{
		Name:     *name,
		Age:      int32(*age),
		Email:    *email,
		Price:    *price,
		Quantity: *quantity,
	}

	data, err := pb.Marshal(user)
	if err != nil {
		log.Fatalf("serialize user: %v", err)
	}
	fmt.Println("serialized user (hex):", hex.EncodeToString(data))

	var newUser proto.User
	err = pb.Unmarshal(data, &newUser)
	if err != nil {
		log.Fatalf("Failed to deserialize user: %v", err)
	}
	fmt.Println("user:", newUser)

	jsonData, err := protojson.Marshal(&newUser)
	if err != nil {
		log.Fatalf("marshal user to json: %v", err)
	}
	fmt.Println("user json:", string(jsonData))

	err = protovalidate.Validate(&newUser)
	if err != nil {
		log.Fatalf("validation failed: %v", err)
	} else {
		fmt.Println("validation ok")
	}
}
