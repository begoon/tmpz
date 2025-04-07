package main

import (
	"encoding/gob"
	"fmt"
	"log"
	"os"
)

func main() {
	if len(os.Args) < 4 {
		fmt.Println("Usage:")
		fmt.Println("  compress <input.txt> <output.bpe>")
		fmt.Println("  decompress <input.bpe> <output.txt>")
		os.Exit(1)
	}

	command := os.Args[1]
	inFile := os.Args[2]
	outFile := os.Args[3]

	switch command {
	case "compress":
		raw, err := os.ReadFile(inFile)
		if err != nil {
			panic(err)
		}
		compressed, rules := CompressBPE(raw, 256)

		f, err := os.Create(outFile)
		if err != nil {
			log.Fatalln(err)
		}
		defer f.Close()

		encoder := gob.NewEncoder(f)
		err = encoder.Encode(compressed)
		if err != nil {
			log.Fatalln(err)
		}
		err = encoder.Encode(rules)
		if err != nil {
			log.Fatalln(err)
		}
		fmt.Println("compression complete")

	case "decompress":
		f, err := os.Open(inFile)
		if err != nil {
			log.Fatalln(err)
		}
		defer f.Close()

		var compressed []byte
		var rules []BPERule

		decoder := gob.NewDecoder(f)
		err = decoder.Decode(&compressed)
		if err != nil {
			log.Fatalln(err)
		}
		err = decoder.Decode(&rules)
		if err != nil {
			log.Fatalln(err)
		}

		decompressed := DecompressBPE(compressed, rules)
		err = os.WriteFile(outFile, decompressed, 0o644)
		if err != nil {
			log.Fatalln(err)
		}
		fmt.Println("decompression complete")

	default:
		fmt.Println("unknown command:", command)
	}
}
