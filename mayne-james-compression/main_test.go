package main

import (
	"bytes"
	"encoding/binary"
	"math/rand"
	"os"
	"path/filepath"
	"testing"
)

func TestDictionary(t *testing.T) {
	d := newDict(3)
	a, _ := d.add([]byte("a"))
	d.add([]byte("abc"))
	if id, _ := d.add([]byte("a")); id != a || d.nActive != 2 {
		t.Fatal("duplicate entry")
	}
	if _, n, _, _ := d.longestMatch([]byte("abc")); n != 3 {
		t.Fatalf("match length %d", n)
	}
	d.add([]byte("xyz"))
	d.inc(a)
	id := d.index["abc"]
	d.inc(id)
	d.thinByMedian()
	if _, ok := d.add([]byte("def")); !ok || len(d.entries) != 3 {
		t.Fatal("slot not reclaimed")
	}
	if _, ok := d.index["a"]; !ok {
		t.Fatal("literal removed")
	}
}

func roundTrip(t testing.TB, src []byte) []byte {
	t.Helper()
	var archive, decoded bytes.Buffer
	if err := compressFile(bytes.NewReader(src), &archive); err != nil {
		t.Fatal(err)
	}
	if err := decode(bytes.NewReader(archive.Bytes()), &decoded); err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(src, decoded.Bytes()) {
		t.Fatal("round trip differs")
	}
	return archive.Bytes()
}

func TestRoundTrip(t *testing.T) {
	all := make([]byte, 256)
	for i := range all {
		all[i] = byte(i)
	}
	random := make([]byte, 8192)
	rand.New(rand.NewSource(1)).Read(random)
	cases := map[string][]byte{"empty": nil, "all-bytes": all, "random": random, "newlines": bytes.Repeat([]byte{'\n'}, 65536), "repeated": bytes.Repeat([]byte("abcabcabcabc\n"), 1000), "unicode": []byte("Hello 世界 🌍\nHello 世界 🌍")}
	for _, name := range []string{"input.txt", "input-abc.txt"} {
		data, err := os.ReadFile(name)
		if err != nil {
			t.Fatal(err)
		}
		cases[name] = data
	}
	for name, data := range cases {
		t.Run(name, func(t *testing.T) {
			archive := roundTrip(t, data)
			if !bytes.Equal(archive, roundTrip(t, data)) {
				t.Fatal("nondeterministic archive")
			}
			t.Logf("input=%d archive=%d", len(data), len(archive))
		})
	}
}

func TestMalformedArchive(t *testing.T) {
	header := []byte{'M', 'J', '2', 'C', '!', 0, 0}
	for _, data := range [][]byte{nil, []byte("MJDC"), append(bytes.Clone(header), '!'), append(bytes.Clone(header), '!', 'x'), {'M', 'J', '2', 'C', '!', 1, 1}, {'M', 'J', '2', 'C', '!', 1, 0, 'a', 0, 0}, {'M', 'J', '2', 'C', '!', 1, 0, 'a', 2, 0, 'x'}, {'M', 'J', '2', 'C', '!', 2, 0, 'a', 1, 0, 'x', 'a', 1, 0, 'y'}} {
		if err := decode(bytes.NewReader(data), &bytes.Buffer{}); err == nil {
			t.Errorf("accepted %v", data)
		}
	}
}

func TestCurrentArchive(t *testing.T) {
	data, err := os.ReadFile("output.txt")
	if err != nil {
		t.Fatal(err)
	}
	want, err := os.ReadFile("input.txt")
	if err != nil {
		t.Fatal(err)
	}
	var out bytes.Buffer
	if err := decode(bytes.NewReader(data), &out); err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(out.Bytes(), want) {
		t.Fatal("current archive mismatch")
	}
}

func TestLegacyArchive(t *testing.T) {
	data, err := os.ReadFile("testdata/legacy.mjc")
	if err != nil {
		t.Fatal(err)
	}
	want, err := os.ReadFile("input.txt")
	if err != nil {
		t.Fatal(err)
	}
	var out bytes.Buffer
	if err = decode(bytes.NewReader(data), &out); err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(out.Bytes(), want) {
		t.Fatal("legacy archive mismatch")
	}
}

func TestFilePreservation(t *testing.T) {
	dir := t.TempDir()
	src := filepath.Join(dir, "in")
	dest := filepath.Join(dir, "out")
	original := []byte("keep this input")
	if err := os.WriteFile(src, original, 0600); err != nil {
		t.Fatal(err)
	}
	alias := filepath.Join(dir, "alias")
	if err := os.Link(src, alias); err != nil {
		t.Fatal(err)
	}
	for _, path := range []string{src, alias} {
		if err := run([]string{"c", src, path}); err == nil {
			t.Fatal("accepted same file")
		}
	}
	if err := os.WriteFile(dest, original, 0600); err != nil {
		t.Fatal(err)
	}
	for _, mode := range []string{"invalid", "d"} {
		if err := run([]string{mode, src, dest}); err == nil {
			t.Fatal("expected error")
		}
	}
	for _, path := range []string{src, dest} {
		data, err := os.ReadFile(path)
		if err != nil || !bytes.Equal(data, original) {
			t.Fatal("file changed on failure")
		}
	}
	if err := run([]string{"c", src, dest}); err != nil {
		t.Fatal(err)
	}
	if err := run([]string{"d", dest, filepath.Join(dir, "restored")}); err != nil {
		t.Fatal(err)
	}
}

func TestCodebookSavings(t *testing.T) {
	data, err := os.ReadFile("input.txt")
	if err != nil {
		t.Fatal(err)
	}
	archive := roundTrip(t, data)
	if len(archive) >= len(data) {
		t.Fatalf("sample expanded to %d", len(archive))
	}
	count := int(binary.LittleEndian.Uint16(archive[5:7]))
	offset := 7
	phrases := map[string]bool{}
	for i := 0; i < count; i++ {
		n := int(binary.LittleEndian.Uint16(archive[offset+1 : offset+3]))
		phrase := string(archive[offset+3 : offset+3+n])
		if phrases[phrase] {
			t.Fatal("duplicate phrase")
		}
		phrases[phrase] = true
		offset += 3 + n
	}
}

func FuzzRoundTrip(f *testing.F) {
	f.Add([]byte("abcabcabc\n"))
	f.Add([]byte{0, 255, 33})
	f.Add([]byte{})
	f.Fuzz(func(t *testing.T, data []byte) {
		if len(data) > 8192 {
			t.Skip()
		}
		roundTrip(t, data)
	})
}
