package main

import (
	"fmt"
	"runtime"
)

func x() {
	a := &[]int{1, 2, 3}
	runtime.SetFinalizer(a, func(a *[]int) {
		fmt.Println("finalizer called", a)
	})
	fmt.Println("a[]", a)
	a = nil
	runtime.GC()
	fmt.Println("a[]", a)

	s := make([]byte, 1024)
	n := runtime.Stack(s, true)
	fmt.Println("stack", string(s)[:n])
}

func main() {
	x()
}
