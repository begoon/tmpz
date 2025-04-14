package main

import (
	"bytes"
	"fmt"
	"log"
	"net"
	"strings"

	"github.com/knusbaum/go9p/client"
)

func main() {
	s, err := net.Dial("tcp", "localhost:9999")
	if err != nil {
		log.Fatal(fmt.Errorf("dial: %v", err))
	}
	defer s.Close()
	c, err := client.NewClient(s, "alexander", "alexander")
	if err != nil {
		log.Fatal(fmt.Errorf("new client: %v", err))
	}
	d, err := c.Readdir("/")
	if err != nil {
		log.Fatal(fmt.Errorf("readdir: %v", err))
	}
	for _, fi := range d {
		log.Printf("%v %d", fi.Name, fi.Length)
	}
	f, err := c.Open("static", 0)
	if err != nil {
		log.Fatal(fmt.Errorf("open/static: %v", err))
	}
	defer f.Close()
	b := make([]byte, 16)
	_, err = f.Read(b)
	if err != nil {
		log.Fatal(fmt.Errorf("read/static: %v", err))
	}
	log.Printf("static [%s]", bytes.Trim(b, "\n\r\x00"))
	f, err = c.Open("dynamic", 0)
	if err != nil {
		log.Fatal(fmt.Errorf("open/dynamic: %v", err))
	}
	defer f.Close()
	b = make([]byte, 16)
	_, err = f.Read(b)
	if err != nil {
		log.Fatal(fmt.Errorf("read/dynamic: %v", err))
	}
	log.Printf("dynamic [%s]", strings.Trim(string(b), "\n\r"))
	log.Println(".")
}
