package main

import (
	"flag"
	"fmt"
	"io"
	"log"
	"os"

	"github.com/lionkov/ninep"
	"github.com/lionkov/ninep/clnt"
)

var (
	debuglevel = flag.Int("d", 0, "debuglevel")
	addr       = flag.String("addr", "127.0.0.1:5640", "network address")
	msize      = flag.Uint("m", 8192, "Msize for 9p")
)

func main() {
	var user ninep.User
	var err error
	var c *clnt.Clnt
	var file *clnt.File
	var d []*ninep.Dir

	flag.Parse()
	user = ninep.OsUsers.Uid2User(os.Geteuid())
	clnt.DefaultDebuglevel = *debuglevel
	c, err = clnt.Mount("tcp", *addr, "", uint32(*msize), user)
	if err != nil {
		log.Fatal(err)
	}

	lsarg := "/"
	if flag.NArg() == 1 {
		lsarg = flag.Arg(0)
	} else if flag.NArg() > 1 {
		log.Fatal("error: only one argument expected")
	}

	file, err = c.FOpen(lsarg, ninep.OREAD)
	if err != nil {
		log.Fatal(err)
	}

	for {
		d, err = file.Readdir(0)
		if len(d) == 0 || (err != nil && err != io.EOF) {
			break
		}

		for i := range d {
			os.Stdout.WriteString(d[i].Name + "\n")
		}

		if err != nil && err != io.EOF {
			log.Fatal(err)
		}
	}

	file.Close()
	if err != nil && err != io.EOF {
		log.Fatal(err)
	}

	name := "kind"
	file, err = c.FOpen(name, ninep.OREAD)
	if err != nil {
		log.Fatal(err)
	}
	content := make([]byte, 1024*8)
	n, err := file.Read(content)
	if err != nil {
		log.Fatal(fmt.Errorf("read %q error: %v", name, err))
	}
	fmt.Printf("read %d byte(s) from %q\n", n, name)
	fmt.Println(string(content[:n]))
	file.Close()
}
