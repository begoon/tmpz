package main

import "fmt"

func a() (string, error) {
	return "A", nil
}

func b() (s string, err error) {
	s = "explicit B"
	return "B", nil
}

func c() (s string, err error) {
	s = "explicit C"
	return
}

func d() (s string, err error) {
	defer func() {
		s = "explicit D"
		err = fmt.Errorf("error D")
	}()
	return "D", nil
}

func e() (s string, err error) {
	defer func() {
		s = "explicit E"
		err = fmt.Errorf("error E")
	}()
	return
}

func f() (s string, err error) {
	return
}

func g() (s string, err error) {
	i, err := 0, fmt.Errorf("error G")
	_ = i
	return
}

func h() (s string, err error) {
	i, err := 0, fmt.Errorf("error H")
	_ = i
	defer func() {
		err = fmt.Errorf("deferred error H")
	}()
	return
}

func main() {
	fmt.Println(a())
	fmt.Println(b())
	fmt.Println(c())
	fmt.Println(d())
	fmt.Println(e())
	fmt.Println(f())
	fmt.Println(g())
	fmt.Println(h())
}
