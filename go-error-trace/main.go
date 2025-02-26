package main

import (
	"fmt"
)

func main() {
	err := a("path", "version", 0)
	if err != nil {
		fmt.Println(err)
	}
}

func a(path, version string, n int) (err error) {
	defer Wrap(&err, "processZip (%q, %q, %d)", path, version, n)
	if n == 0 {
		return fmt.Errorf("n is zero")
	}
	return nil
}

func Wrap(errp *error, format string, args ...interface{}) {
	if *errp != nil {
		s := fmt.Sprintf(format, args...)
		*errp = fmt.Errorf("%s: %w", s, *errp)
	}
}
