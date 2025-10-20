package main

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"os"
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
	entries  []entry
	index    map[string]int
	nActive  int
	capacity int
}

func newDict(capacity int) *dict {
	return &dict{
		entries:  make([]entry, 0, capacity),
		index:    make(map[string]int, 1<<17),
		capacity: capacity,
	}
}

func (d *dict) add(b []byte) (int, bool) {
	if len(d.entries) >= d.capacity {
		return 0, false
	}
	id := len(d.entries)
	copy := append([]byte{}, b...)
	d.entries = append(d.entries, entry{bytes: copy, count: 1, active: true})
	d.index[string(copy)] = id
	d.nActive += 1
	return id, true
}

func (d *dict) inc(id int) { d.entries[id].count += 1 }

func (d *dict) deactivate(id int) {
	e := &d.entries[id]
	if e.active {
		delete(d.index, string(e.bytes))
		e.active = false
		if d.nActive > 0 {
			d.nActive -= 1
		}
	}
}

func (d *dict) longestMatch(buf []byte) (id int, length int, count int, ok bool) {
	var bestID int
	var bestLen int
	var bestCount int
	for i := 1; i <= len(buf) && i <= 1024; i++ {
		if id, found := d.index[string(buf[:i])]; found {
			bestID, bestLen, bestCount, ok = id, i, d.entries[id].count, true
		} else {
			break
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
		if d.entries[i].active && d.entries[i].count < median {
			d.deactivate(i)
		}
	}
}

func buildDictionary(input []byte) *dict {
	d := newDict(MaxDict)

	var lastID int = ^int(0)
	var lastCount int = 0

	for i := 0; i < len(input); i += 0 {
		look := cutUntilNewLine(input[i:])
		matchedID, len, count, found := d.longestMatch(look)
		_ = count // suppress unused variable warning
		if !found {
			addedID, added := d.add([]byte{input[i]})
			if !added {
				d.thinByMedian()
				addedID, added = d.add([]byte{input[i]})
				if !added {
					panic("dictionary exhausted")
				}
			}
			matchedID, len, count, found = addedID, 1, d.entries[addedID].count, true
		} else {
			d.inc(matchedID)
			count = d.entries[matchedID].count
		}

		free := d.capacity - d.nActive
		threshold := d.capacity
		if free != 0 {
			threshold = d.capacity / free
		}
		if threshold < 2 {
			threshold = 2
		}

		join := lastID != ^int(0) && count >= threshold && lastCount >= threshold

		if join {
			concat := append(append([]byte{}, d.entries[lastID].bytes...), d.entries[matchedID].bytes...)
			if _, ok := d.add(concat); !ok {
				d.thinByMedian()
				_, _ = d.add(concat)
			}
		} else if d.capacity-d.nActive < 2 {
			d.thinByMedian()
			if !d.entries[matchedID].active {
				d.entries[matchedID].count = 0
			}
		}

		i += len
		lastID = matchedID
		lastCount = d.entries[matchedID].count
	}
	return d
}

type codebook struct {
	sentinel byte
	table    map[byte][]byte // code -> phrase
}

func chooseSentinel(in []byte) (byte, error) {
	seen := [256]bool{}
	for _, b := range in {
		seen[b] = true
	}
	for i := 0x21; i < 128; i++ { // or the full range 0..255
		if !seen[i] {
			return byte(i), nil
		}
	}
	return 0, errors.New("no sentinel available")
}

func buildCodebook(d *dict, in []byte) (*codebook, error) {
	sentinel, err := chooseSentinel(in)
	if err != nil {
		return nil, err
	}
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

	// build printable code list 33..126; include the sentinel if you want "!!"
	codes := make([]byte, 0, 94)
	for c := byte(33); c <= 126; c++ {
		codes = append(codes, c) // keep sentinel included to allow "!!"
	}

	table := make(map[byte][]byte)
	idx := 0
	for _, cand := range c { // c is your sorted candidate list
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
		output.WriteByte(input[i])
		i += 1
	next:
	}
	fmt.Printf("%s\n", output.String())
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
		if data[i] == sentinel[0] && i+1 < len(data) {
			if phrase, found := table[data[i+1]]; found {
				if _, err := w.Write(phrase); err != nil {
					return fmt.Errorf("writing phrase for code %d: %w", data[i+1], err)
				}
				i += 2
				continue
			}
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

	fmt.Println()
	fmt.Println("*** COMPRESSION STATISTICS ***")
	fmt.Println("CODE\tFREQ\tUSAGE\tSTRING")

	type row struct {
		code byte
		freq int
		use  int
		str  []byte
	}

	rows := make([]row, 0, len(book.table))
	for code, phrase := range book.table {
		freq := int(0)
		if id, found := d.index[string(phrase)]; found && d.entries[id].active {
			freq = d.entries[id].count
		}
		rows = append(rows, row{code, freq, usage[code], phrase})
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].freq != rows[j].freq {
			return rows[i].freq > rows[j].freq
		}
		return rows[i].use > rows[j].use
	})
	for _, r := range rows {
		digram := []byte{book.sentinel, r.code}
		fmt.Printf("%-2s\t%7d\t%7d\t%s\n",
			safeString(digram),
			r.freq, r.use,
			safeString(r.str),
		)

	}

	fmt.Println()
	fmt.Printf("CHARACTERS IN INPUT  = %d\n", len(src))
	fmt.Printf("CHARACTERS IN OUTPUT = %d\n", len(data))
	fmt.Printf("COMPRESSION RATIO    = %.3f\n", float64(len(data))/float64(len(src)))
	fmt.Printf("ENCODING TABLE SIZE  = %d\n", len(book.table))
	fmt.Printf("SENTINEL BYTE        = %d\n\n", book.sentinel)

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

func main() {
	if len(os.Args) != 4 {
		fmt.Fprintf(os.Stderr, "usage: %s c|d INPUT OUTPUT\n", os.Args[0])
		os.Exit(2)
	}
	in, err := os.Open(os.Args[2])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer in.Close()
	out, err := os.Create(os.Args[3])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer out.Close()

	switch os.Args[1] {
	case "c":
		if err := compressFile(in, out); err != nil {
			fmt.Fprintln(os.Stderr, "compress:", err)
			os.Exit(1)
		}
	case "d":
		if err := decode(in, out); err != nil {
			fmt.Fprintln(os.Stderr, "decompress:", err)
			os.Exit(1)
		}
	default:
		fmt.Fprintln(os.Stderr, "first argument must be 'c' or 'd'")
		os.Exit(2)
	}
}

func safeString(b []byte) string {
	var out []byte
	for _, v := range b {
		if v <= 0x20 || v > 0x7F {
			out = append(out, fmt.Sprintf("<%02X>", v)...)
		} else {
			out = append(out, v)
		}
	}
	return string(out)
}

func cutUntilNewLine(b []byte) []byte {
	for i, c := range b {
		if c == '\n' {
			return b[:i]
		}
	}
	return b
}
