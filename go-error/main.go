package main

import (
	"errors"
	"fmt"
)

func a() error {
	return errors.New("a() error")
}

func b() error {
	return fmt.Errorf("b() error: %w", a())
}

func main() {
	err := b()
	fmt.Println(err, "-", errors.Unwrap(err))
}
