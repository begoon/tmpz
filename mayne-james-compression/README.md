# Mayne-James compression

An experimental two-pass dictionary compressor in Go 1.27 or later.

```sh
go run . c input.txt /tmp/input.mjc
go run . d /tmp/input.mjc /tmp/restored.txt
go test ./...
go vet ./...
go test -fuzz=FuzzRoundTrip -fuzztime=10s
go test -run='^$' -bench=. -benchmem -count=3
```

Input and output must be different files (including hard-link and symlink
aliases). Output is written to a temporary file in the destination directory
and renamed into place only after successful processing and close. A failure
preserves an existing destination. Newly written archives use private file
permissions. Statistics go to stderr and include the entire archive size;
no ratio is reported for empty input.

Dictionary entries are unique, bounded to 1,024 bytes, and matched even when
intermediate prefixes are absent. Pruning recycles inactive slots while keeping
single-byte literals. Newlines delimit phrase construction and matching. The
codebook retains only phrases whose measured payload savings exceed their
stored table cost, re-encoding after pruning.

## File format

All integers are unsigned and little-endian. The existing `MJ2C` format is
retained; `output.txt` is the current archive of `input.txt`. The original archive is
retained in `testdata/legacy.mjc` for backward-compatibility testing.

```text
4 bytes : magic "MJ2C"
1 byte  : sentinel
u16     : code_count
repeat code_count times:
  1 byte : code
  u16    : phrase_length (nonzero)
  bytes  : phrase
bytes   : encoded payload, continuing to EOF
```

A payload byte other than the sentinel is literal. A sentinel followed by a
code expands to that code's phrase, without recursive expansion. The encoder
uses printable codes 33–126 for phrases. If the chosen sentinel occurs in the
input, code 0 maps to its single-byte literal value; occurrences are escaped
as `sentinel, 0`. This supports all 256 byte values without changing the format.

The decoder rejects invalid magic, truncated headers/table entries, more than
256 entries, duplicate codes, empty phrases, undefined codes, and dangling
sentinels. There is no checksum or original-length field, so corruption or
truncation at a valid payload boundary cannot always be detected.

Benchmarks exercise the in-memory codec with output discarded and diagnostics
redirected to the null device. They include dictionary construction and normal
diagnostic formatting, but exclude CLI startup and filesystem I/O.

## Limitations

This is an in-memory experimental implementation, not a streaming compressor.
Small or incompressible inputs may expand. Codebook selection is heuristic and
does not guarantee the smallest archive. The format has no raw-storage mode.
