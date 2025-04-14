package main

import (
	"flag"
	"log"
	"time"

	"github.com/knusbaum/go9p"
	"github.com/knusbaum/go9p/fs"
)

func main() {
	flag.Parse()

	efs, root := fs.NewFS("", "", 0o777)
	root.AddChild(fs.NewStaticFile(
		efs.NewStat("static", "me", "me", 0o666),
		[]byte("aloha\n"),
	))

	root.AddChild(fs.NewDynamicFile(
		efs.NewStat("dynamic", "me", "me", 0o666),
		func() []byte {
			return []byte(time.Now().String() + "\n")
		},
	))
	log.Fatal(go9p.Serve("0.0.0.0:9999", efs.Server()))
}
