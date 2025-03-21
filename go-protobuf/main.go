package main

import (
	"encoding/hex"
	"flag"
	"fmt"
	"log"

	"go-protobuf/internal/proto"

	pb "google.golang.org/protobuf/proto"
)

func main() {
	name := flag.String("name", "Alice", "name of the user")
	age := flag.Int("age", 30, "age of the user")
	flag.Parse()

	user := &proto.User{
		Name: *name,
		Age:  int32(*age),
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

	err = validateUser(&newUser)
	if err != nil {
		log.Fatalf("validation failed: %v", err)
	} else {
		fmt.Println("validation ok")
	}
}

func validateUser(user *proto.User) error {
	return user.ValidateAll()
}
