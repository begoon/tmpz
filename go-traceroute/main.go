package main

import (
	"flag"
	"fmt"
	"net"
	"os"
	"path"
	"time"

	"golang.org/x/net/icmp"
	"golang.org/x/net/ipv4"
)

func main() {
	var (
		host    = flag.String("host", "", "host to traceroute")
		maxHops = flag.Int("max-hops", 30, "maximum number of hops")
		timeout = flag.Duration("timeout", 2*time.Second, "timeout for each hop")
	)
	flag.Parse()

	if *host == "" {
		name := path.Base(os.Args[0])
		fmt.Printf("usage: %s -host <hostname or IP>\n", name)
		os.Exit(0)
	}

	addr, err := net.ResolveIPAddr("ip4", *host)
	if err != nil {
		fmt.Fprintf(os.Stderr, "resolving host: %v\n", err)
		os.Exit(1)
	}

	traceRoute(addr, *maxHops, *timeout)
}

func traceRoute(addr *net.IPAddr, maxHops int, timeout time.Duration) {
	conn, err := net.ListenPacket("ip4:icmp", "0.0.0.0")
	if err != nil {
		fmt.Fprintf(os.Stderr, "listening for icmp: %v\n", err)
		os.Exit(1)
	}
	defer conn.Close()

	ipv4Conn := ipv4.NewPacketConn(conn)

	for ttl := 1; ttl <= maxHops; ttl++ {
		err := ipv4Conn.SetTTL(ttl)
		if err != nil {
			fmt.Fprintf(os.Stderr, "setting ttl: %v\n", err)
			return
		}

		message := icmp.Message{
			Type: ipv4.ICMPTypeEcho,
			Code: 0,
			Body: &icmp.Echo{
				ID:   os.Getpid() & 0xffff,
				Seq:  ttl,
				Data: []byte("aloha!"),
			},
		}

		msgBytes, err := message.Marshal(nil)
		if err != nil {
			fmt.Fprintf(os.Stderr, "marshaling icmp message: %v\n", err)
			return
		}

		startTime := time.Now()
		_, err = conn.WriteTo(msgBytes, addr)
		if err != nil {
			fmt.Fprintf(os.Stderr, "sending icmp message: %v\n", err)
			return
		}

		conn.SetReadDeadline(time.Now().Add(timeout))

		reply := make([]byte, 1500)
		n, peerAddr, err := conn.ReadFrom(reply)

		elapsed := time.Since(startTime)

		if err != nil {
			if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
				fmt.Printf("%d.  * %v\n", ttl, elapsed)
				continue
			}
			fmt.Fprintf(os.Stderr, "%d. reading icmp reply: %v\n", ttl, err)
			break
		}

		rm, err := icmp.ParseMessage(ipv4.ICMPTypeTimeExceeded.Protocol(), reply[:n])
		if err != nil && rm == nil {
			rm, err = icmp.ParseMessage(ipv4.ICMPTypeEchoReply.Protocol(), reply[:n])
			if err != nil {
				fmt.Fprintf(os.Stderr, "%d. Error parsing icmp reply: %v\n", ttl, err)
				break
			}

		}

		if rm.Type == ipv4.ICMPTypeTimeExceeded {
			fmt.Printf("%d. %v %v\n", ttl, peerAddr, elapsed)
		} else if rm.Type == ipv4.ICMPTypeEchoReply {
			fmt.Printf("%d. %v %v\n", ttl, peerAddr, elapsed)
			break
		} else {
			fmt.Printf("%d. unknown icmp reply %v\n", ttl, elapsed)
		}
	}
}
