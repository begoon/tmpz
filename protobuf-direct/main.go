package main

import (
	"fmt"
	"log"

	"github.com/jhump/protoreflect/desc/protoparse"
	"github.com/jhump/protoreflect/dynamic"
)

const protoDefinition = `
syntax = "proto3";
package adhoc;

message NiceMessage {
    string name = 1;
    int32 id = 2;
}
`

func main() {
	parser := protoparse.Parser{
		Accessor: protoparse.FileContentsFromMap(map[string]string{
			"adhoc.proto": protoDefinition,
		}),
	}

	fileDescriptor, err := parser.ParseFiles("adhoc.proto")
	if err != nil {
		log.Fatalf("error parsing proto file: %v", err)
	}

	descriptor := fileDescriptor[0].FindMessage("adhoc.NiceMessage")
	if descriptor == nil {
		log.Fatalf("could not find message descriptor")
	}

	msg1 := dynamic.NewMessage(descriptor)

	originalJSON := `{"name": "example", "id": 123}`
	fmt.Println("original JSON", originalJSON)

	err = msg1.UnmarshalJSON([]byte(originalJSON))
	if err != nil {
		log.Fatalf("error unmarshalling JSON: %v", err)
	}
	fmt.Println("msg1/fromJSON", msg1)

	json1, err := msg1.MarshalJSONIndent()
	if err != nil {
		log.Fatalf("error marshalling to JSON: %v", err)
	}
	fmt.Println("msg1/toJSON", string(json1))

	bin1, err := msg1.Marshal()
	if err != nil {
		log.Fatalf("error marshalling to binary: %v", err)
	}
	fmt.Println("msg1/binary", bin1)

	msg2 := dynamic.NewMessage(descriptor)
	msg2.SetFieldByName("name", "*NAME*")
	msg2.SetFieldByName("id", int32(987654321))
	fmt.Println("msg2/scratch", msg2)

	json2, err := msg2.MarshalJSONIndent()
	if err != nil {
		log.Fatalf("error marshalling to JSON: %v", err)
	}
	fmt.Println("msg2/JSON", string(json2))

	bin2, err := msg2.Marshal()
	if err != nil {
		log.Fatalf("error marshalling to binary: %v", err)
	}
	fmt.Println("msg2/binary", bin2)
}
