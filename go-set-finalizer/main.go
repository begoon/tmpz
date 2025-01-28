package main

import (
	"fmt"
	"runtime"
	"time"
)

func x() {
	a := &[]int{1, 2, 3}
	runtime.SetFinalizer(a, func(a *[]int) {
		fmt.Println("finalizer called", a)
	})
	fmt.Println("a[]", a)
	a = nil
	runtime.GC()
	time.Sleep(1 * time.Second)
	fmt.Println("a[]", a)
}

func main() {
	x()
}
