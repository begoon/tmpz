package main

import (
	"crypto/sha1"
	"fmt"
	"log"
	"time"

	"github.com/labstack/echo/v4"
)

func main() {
	e := echo.New()

	e.Static("/", ".")

	e.GET("/info", func(c echo.Context) error {
		time.Sleep(1 * time.Second)
		return c.String(200, "OK")
	})

	e.GET("/time", func(c echo.Context) error {
		return c.String(200, fmt.Sprint(time.Now()))
	})

	e.GET("/hash", func(c echo.Context) error {
		t := c.QueryParam("q")
		h := sha1.Sum([]byte(t))
		return c.String(200, t+"*"+fmt.Sprintf("%x", h[:]))
	})

	log.Fatal(e.Start(":8000"))
}
