package main

import (
	"bytes"
	"io"
	"os"
	"testing"
)

func BenchmarkCodec(b *testing.B) {
	null, err := os.OpenFile(os.DevNull, os.O_WRONLY, 0)
	if err != nil {
		b.Fatal(err)
	}
	defer null.Close()
	stdout, stderr := os.Stdout, os.Stderr
	os.Stdout, os.Stderr = null, null
	defer func() { os.Stdout, os.Stderr = stdout, stderr }()
	text, _ := os.ReadFile("input.txt")
	abc, _ := os.ReadFile("input-abc.txt")
	for _, c := range []struct {
		name string
		data []byte
	}{{"sample", text}, {"abc", abc}, {"repeated13k", bytes.Repeat([]byte("abcabcabcabc\n"), 1000)}, {"text144k", bytes.Repeat(text, 100)}} {
		var archive bytes.Buffer
		if err := compressFile(bytes.NewReader(c.data), &archive); err != nil {
			b.Fatal(err)
		}
		b.Run(c.name+"/compress", func(b *testing.B) {
			b.ReportAllocs()
			b.SetBytes(int64(len(c.data)))
			for i := 0; i < b.N; i++ {
				if err := compressFile(bytes.NewReader(c.data), io.Discard); err != nil {
					b.Fatal(err)
				}
			}
		})
		b.Run(c.name+"/decode", func(b *testing.B) {
			b.ReportAllocs()
			b.SetBytes(int64(len(c.data)))
			for i := 0; i < b.N; i++ {
				if err := decode(bytes.NewReader(archive.Bytes()), io.Discard); err != nil {
					b.Fatal(err)
				}
			}
		})
	}
}
