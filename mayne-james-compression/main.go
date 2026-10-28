package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"slices"
	"sort"
)

const MaxDict = 65535

type entry struct {
	bytes  []byte
	count  int
	active bool
}

type dict struct {
	entries   []entry
	index     map[string]int
	nActive   int
	capacity  int
	free      []int
	maxLength int
}

func newDict(capacity int) *dict {
	return &dict{
		entries:  make([]entry, 0, capacity),
		index:    make(map[string]int, 1<<17),
		capacity: capacity,
	}
}

func (d *dict) add(b []byte) (int, bool) {
	if id, ok := d.index[string(b)]; ok {
		return id, true
	}
	if d.nActive >= d.capacity || len(b) > 1024 {
		return 0, false
	}
	id := len(d.entries)
	e := entry{bytes: bytes.Clone(b), count: 1, active: true}
	if len(d.free) > 0 {
		id = d.free[len(d.free)-1]
		d.free = d.free[:len(d.free)-1]
		d.entries[id] = e
	} else {
		d.entries = append(d.entries, e)
	}
	d.index[string(b)] = id
	d.nActive++
	d.maxLength = max(d.maxLength, len(b))
	return id, true
}

func (d *dict) inc(id int) { d.entries[id].count += 1 }

func (d *dict) deactivate(id int) {
	e := &d.entries[id]
	if e.active {
		delete(d.index, string(e.bytes))
		e.active = false
		d.free = append(d.free, id)
		if d.nActive > 0 {
			d.nActive -= 1
		}
	}
}

func (d *dict) longestMatch(buf []byte) (id int, length int, count int, ok bool) {
	var bestID int
	var bestLen int
	var bestCount int
	for i := 1; i <= len(buf) && i <= d.maxLength; i++ {
		if id, found := d.index[string(buf[:i])]; found {
			bestID, bestLen, bestCount, ok = id, i, d.entries[id].count, true
		}
	}
	return bestID, bestLen, bestCount, ok
}

func median(a []int) int {
	if len(a) == 0 {
		return 0
	}
	slices.Sort(a)
	return a[len(a)/2]
}

func (d *dict) thinByMedian() {
	if d.nActive == 0 {
		return
	}
	counts := make([]int, 0, d.nActive)
	for i := range d.entries {
		if d.entries[i].active {
			counts = append(counts, d.entries[i].count)
		}
	}
	median := median(counts)
	for i := range d.entries {
		if d.entries[i].active && len(d.entries[i].bytes) > 1 && d.entries[i].count < median {
			d.deactivate(i)
		}
	}
}

func buildDictionary(input []byte) *dict {
	d := newDict(MaxDict)
	// Keep literals permanently available, including bytes first seen after pruning.
	for i := 0; i < 256; i++ {
		d.add([]byte{byte(i)})
	}
	var last []byte
	lastCount := 0
	for i := 0; i < len(input); {
		if input[i] == '\n' {
			last = nil
			lastCount = 0
			i++
			continue
		}
		look := cutUntilNewLine(input[i:])
		id, length, _, _ := d.longestMatch(look)
		d.inc(id)
		current := d.entries[id].bytes
		count := d.entries[id].count
		free := d.capacity - d.nActive
		threshold := max(2, d.capacity/max(1, free))
		if len(last) > 0 && count >= threshold && lastCount >= threshold {
			concat := append(bytes.Clone(last), current...)
			if len(concat) <= 1024 {
				if _, ok := d.add(concat); !ok {
					d.thinByMedian()
					d.add(concat)
				}
			}
		}
		// Slice values remain valid even when their dictionary slots are recycled.
		last, lastCount = current, count
		i += length
	}
	return d
}

type codebook struct {
	sentinel byte
	table    map[byte][]byte // code -> phrase
}

func chooseSentinel(in []byte) byte {
	var counts [256]int
	for _, b := range in {
		counts[b]++
	}
	sentinel := byte('!')
	for i, count := range counts {
		if count < counts[sentinel] {
			sentinel = byte(i)
		}
	}
	return sentinel
}

func buildCodebook(d *dict, in []byte) (*codebook, error) {
	sentinel := chooseSentinel(in)
	type candidate struct {
		i    int
		freq int
	}
	var c []candidate
	for i := range d.entries {
		if d.entries[i].active && len(d.entries[i].bytes) > 2 {
			c = append(c, candidate{i, d.entries[i].count})
		}
	}
	sort.Slice(c, func(i, j int) bool {
		if c[i].freq != c[j].freq {
			return c[i].freq > c[j].freq
		}
		li, lj := len(d.entries[c[i].i].bytes), len(d.entries[c[j].i].bytes)
		if li != lj {
			return li > lj
		}
		return bytes.Compare(d.entries[c[i].i].bytes, d.entries[c[j].i].bytes) < 0
	})

	// Keep phrase codes printable; code 0 is reserved for a literal sentinel.
	codes := make([]byte, 0, 94)
	for c := byte(33); c <= 126; c++ {
		codes = append(codes, c)
	}

	table := make(map[byte][]byte)
	if bytes.IndexByte(in, sentinel) >= 0 {
		table[0] = []byte{sentinel}
	}
	idx := 0
	for _, cand := range c {
		if idx >= len(codes) {
			break
		}
		code := codes[idx]
		table[code] = append([]byte{}, d.entries[cand.i].bytes...)
		idx++
	}
	return &codebook{sentinel: sentinel, table: table}, nil
}

func encode(d *dict, book *codebook, input []byte) ([]byte, map[byte]int) {
	phrases := make(map[string]byte, len(book.table))
	for code, phrase := range book.table {
		phrases[string(phrase)] = code
	}

	usage := make(map[byte]int)
	var output bytes.Buffer

	for i := 0; i < len(input); {
		look := cutUntilNewLine(input[i:])
		if _, length, _, matched := d.longestMatch(look); matched {
			phrase := input[i : i+length]
			if code, found := phrases[string(phrase)]; found {
				output.WriteByte(book.sentinel)
				output.WriteByte(code)
				usage[code] += 1
				i += length
				continue
			}
			for fallbackLength := length - 1; fallbackLength >= 3; fallbackLength-- {
				if code, found := phrases[string(input[i:i+fallbackLength])]; found {
					output.WriteByte(book.sentinel)
					output.WriteByte(code)
					usage[code] += 1
					i += fallbackLength
					goto next
				}
			}
		}
		if input[i] == book.sentinel {
			output.WriteByte(book.sentinel)
			output.WriteByte(0)
			usage[0]++
		} else {
			output.WriteByte(input[i])
		}
		i += 1
	next:
	}
	return output.Bytes(), usage
}

func decode(r io.Reader, w io.Writer) error {
	magic := make([]byte, 4)
	if _, err := io.ReadFull(r, magic); err != nil {
		return fmt.Errorf("reading magic: %w", err)
	}
	if !bytes.Equal(magic, []byte("MJ2C")) {
		return fmt.Errorf("invalid magic: %q", magic)
	}
	var sentinel [1]byte
	if _, err := io.ReadFull(r, sentinel[:]); err != nil {
		return fmt.Errorf("reading sentinel: %w", err)
	}
	codesNumber, err := readU16(r)
	if err != nil {
		return fmt.Errorf("reading number of codes: %w", err)
	}
	if codesNumber > 256 {
		return fmt.Errorf("too many codes: %d", codesNumber)
	}
	table := make(map[byte][]byte, codesNumber)
	for i := 0; i < int(codesNumber); i++ {
		var code [1]byte
		if _, err := io.ReadFull(r, code[:]); err != nil {
			return fmt.Errorf("reading code %d: %w", i, err)
		}
		sz, err := readU16(r)
		if err != nil {
			return fmt.Errorf("reading length for code %d: %w", i, err)
		}
		if sz == 0 {
			return fmt.Errorf("empty phrase for code %d", code[0])
		}
		if _, exists := table[code[0]]; exists {
			return fmt.Errorf("duplicate code %d", code[0])
		}
		data := make([]byte, sz)
		if _, err := io.ReadFull(r, data); err != nil {
			return fmt.Errorf("reading data for code %d: %w", i, err)
		}
		table[code[0]] = data
	}
	data, err := io.ReadAll(r)
	if err != nil {
		return fmt.Errorf("reading data: %w", err)
	}
	for i := 0; i < len(data); {
		if data[i] == sentinel[0] {
			if i+1 == len(data) {
				return fmt.Errorf("truncated escape at %d", i)
			}
			if phrase, found := table[data[i+1]]; found {
				if _, err := w.Write(phrase); err != nil {
					return fmt.Errorf("writing phrase for code %d: %w", data[i+1], err)
				}
				i += 2
				continue
			}
			return fmt.Errorf("undefined code %d at %d", data[i+1], i)
		}
		if _, err := w.Write(data[i : i+1]); err != nil {
			return fmt.Errorf("writing data at %d: %w", i, err)
		}
		i += 1
	}
	return nil
}

func compressFile(in io.Reader, out io.Writer) error {
	src, err := io.ReadAll(in)
	if err != nil {
		return fmt.Errorf("reading input: %w", err)
	}

	d := buildDictionary(src)
	book, err := buildCodebook(d, src)
	if err != nil {
		return fmt.Errorf("building codebook: %w", err)
	}
	data, usage := encode(d, book, src)
	// Drop phrases whose actual savings do not pay for their table entry.
	// Re-encode after removal because shorter phrases can become useful.
	for {
		removed := false
		for code, phrase := range book.table {
			if len(phrase) > 2 && usage[code]*(len(phrase)-2) <= len(phrase)+3 {
				delete(book.table, code)
				removed = true
			}
		}
		if !removed {
			break
		}
		data, usage = encode(d, book, src)
	}
	archiveSize := 7 + len(data)
	for _, phrase := range book.table {
		archiveSize += 3 + len(phrase)
	}
	fmt.Fprintf(os.Stderr, "INPUT BYTES = %d\nARCHIVE BYTES = %d\n", len(src), archiveSize)
	if len(src) > 0 {
		fmt.Fprintf(os.Stderr, "COMPRESSION RATIO = %.3f\n", float64(archiveSize)/float64(len(src)))
	}

	if _, err := out.Write([]byte("MJ2C")); err != nil {
		return fmt.Errorf("writing magic: %w", err)
	}

	if _, err := out.Write([]byte{book.sentinel}); err != nil {
		return fmt.Errorf("writing sentinel: %w", err)
	}

	if err := writeU16(out, uint16(len(book.table))); err != nil {
		return fmt.Errorf("writing table size: %w", err)
	}

	codes := make([]int, 0, len(book.table))
	for code := range book.table {
		codes = append(codes, int(code))
	}
	sort.Ints(codes)

	for _, v := range codes {
		code := byte(v)
		phrase := book.table[code]
		if _, err := out.Write([]byte{code}); err != nil {
			return fmt.Errorf("writing code %d: %w", code, err)
		}
		if err := writeU16(out, uint16(len(phrase))); err != nil {
			return fmt.Errorf("writing length for code %d: %w", code, err)
		}
		if _, err := out.Write(phrase); err != nil {
			return fmt.Errorf("writing phrase for code %d: %w", code, err)
		}
	}
	_, err = out.Write(data)
	return err
}

func readU16(r io.Reader) (uint16, error) {
	var v uint16
	err := binary.Read(r, binary.LittleEndian, &v)
	return v, err
}

func writeU16(w io.Writer, v uint16) error {
	return binary.Write(w, binary.LittleEndian, v)
}

// Transform to a temporary file, publishing it only after successful completion.
func run(args []string) error {
	if len(args) != 3 || (args[0] != "c" && args[0] != "d") {
		return fmt.Errorf("usage: mjc c|d INPUT OUTPUT")
	}
	in, err := os.Open(args[1])
	if err != nil {
		return err
	}
	defer in.Close()
	info, err := in.Stat()
	if err != nil {
		return err
	}
	if dest, err := os.Stat(args[2]); err == nil {
		if os.SameFile(info, dest) {
			return fmt.Errorf("input and output must be different files")
		}
	} else if !os.IsNotExist(err) {
		return err
	}
	out, err := os.CreateTemp(filepath.Dir(args[2]), ".mjc-*")
	if err != nil {
		return err
	}
	defer os.Remove(out.Name())
	defer out.Close()
	if args[0] == "c" {
		err = compressFile(in, out)
	} else {
		err = decode(in, out)
	}
	if err != nil {
		return err
	}
	if err = out.Close(); err != nil {
		return err
	}
	return os.Rename(out.Name(), args[2])
}

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func cutUntilNewLine(b []byte) []byte {
	b = b[:min(len(b), 1024)]
	for i, c := range b {
		if c == '\n' {
			return b[:i]
		}
	}
	return b
}
