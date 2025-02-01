package main

import (
	"crypto/sha512"
	"fmt"
	"log"

	"github.com/bitfield/script"
)

func main() {
	content, err := script.File("main.go").String()
	if err != nil {
		log.Fatalf("error reading file: %v", err)
	}
	fmt.Println(content)

	n, err := script.File("main.go").Match("fmt").CountLines()
	if err != nil {
		log.Fatalf("error counting lines: %v", err)
	}
	fmt.Printf("lines %d\n", n)

	sha, err := script.File("main.go").Hash(sha512.New())
	if err != nil {
		log.Fatalf("error hashing file: %v", err)
	}
	fmt.Printf("sha512 %x\n", sha)

	script.Get("https://wttr.in/London?format=3").Stdout()

	script.Exec("ping -c 1 127.0.0.1").Stdout()

	script.Get("https://api.myip.com").JQ(".ip").Stdout()

	script.Args().ExecForEach("ping -c 1 {{.}}").Stdout()
}
