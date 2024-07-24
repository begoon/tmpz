package main

import (
	"fmt"
	"image/color"
	"log"
	"os"
	"strconv"
	"strings"

	"github.com/go-pdf/fpdf"
	"github.com/joshvarga/svgparser"
	// Or your chosen SVG parsing library
)

var colorNames = map[string]color.RGBA{
	"black":   {0, 0, 0, 255},
	"silver":  {192, 192, 192, 255},
	"gray":    {128, 128, 128, 255},
	"white":   {255, 255, 255, 255},
	"maroon":  {128, 0, 0, 255},
	"red":     {255, 0, 0, 255},
	"purple":  {128, 0, 128, 255},
	"fuchsia": {255, 0, 255, 255},
	"green":   {0, 128, 0, 255},
	"lime":    {0, 255, 0, 255},
	"olive":   {128, 128, 0, 255},
	"yellow":  {255, 255, 0, 255},
	"navy":    {0, 0, 128, 255},
	"blue":    {0, 0, 255, 255},
	"teal":    {0, 128, 128, 255},
	"aqua":    {0, 255, 255, 255},
	// Add more color names as needed
}

func colorize(htmlColor string) (int, int, int, error) {
	c := colorNames[strings.ToLower(htmlColor)]
	if c.A != 0 { // Color name was found
		return int(c.R), int(c.G), int(c.B), nil
	}

	// if strings.HasPrefix(htmlColor, "#") {
	// 	htmlColor = htmlColor[1:] // Remove the "#" prefix
	// }
	htmlColor, _ = strings.CutPrefix(htmlColor, "#")

	switch len(htmlColor) {
	case 3: // Short form (#RGB)
		htmlColor = string(htmlColor[0]) + string(htmlColor[0]) + string(htmlColor[1]) + string(htmlColor[1]) + string(htmlColor[2]) + string(htmlColor[2])
		fallthrough // Expand and process as #RRGGBB
	case 6: // Long form (#RRGGBB)
		r, err := strconv.ParseInt(htmlColor[0:2], 16, 64)
		g, err := strconv.ParseInt(htmlColor[2:4], 16, 64)
		b, err := strconv.ParseInt(htmlColor[4:6], 16, 64)
		return int(r), int(g), int(b), err
	}

	return 0, 0, 0, fmt.Errorf("invalid HTML color: %s", htmlColor)
}

func ParseFloat(v string) (float64, error) {
	f, err := strconv.ParseFloat(v, 64)
	return f, err
}

func main() {
	pdf := fpdf.New("P", "pt", "A3", "")
	pdf.AddPage()
	pdf.SetFont("Arial", "B", 16)
	pdf.Cell(40, 10, "Hello, world")

	svgString := ""

	data, err := os.ReadFile("image-map.svg")
	if err != nil {
		log.Fatalf("Error reading SVG file: %v", err)
	}
	svgString = string(data)

	// svgString = `
	// <svg>
	// 	<rect x="50" y="120" width="150" height="80" fill="#447799" />
	// 	<text x="100" y="60" font-size="24" fill="white">Hello, SVG!</text>
	// </svg>
	// `

	reader := strings.NewReader(svgString)

	element, err := svgparser.Parse(reader, false)
	if err != nil {
		log.Fatalf("Error parsing SVG: %v", err)
	}

	rects := element.FindAll("rect")

	for _, rect := range rects {
		x, err := ParseFloat(rect.Attributes["x"])
		if err != nil {
			log.Printf("Error parsing x: %v %v", err, rect)
			continue
		}
		y, err := ParseFloat(rect.Attributes["y"])
		if err != nil {
			log.Printf("Error parsing y: %v %v", err, rect)
			continue
		}

		width, err := ParseFloat(rect.Attributes["width"])
		if err != nil {
			log.Printf("Error parsing width: %v %v", err, rect)
			continue
		}

		height, err := ParseFloat(rect.Attributes["height"])
		if err != nil {
			log.Printf("Error parsing height: %v %v", err, rect)
			continue
		}

		r, g, b, _ := colorize(rect.Attributes["fill"])
		if r == 255 && g == 255 && b == 255 {
			continue
		}
		pdf.SetFillColor(r, g, b)
		log.Printf("x: %f, y: %f, width: %f, height: %f, r: %d, g: %d, b: %d", x, y, width, height, r, g, b)
		pdf.Rect(x, y, width, height, "F")
	}

	paths := element.FindAll("path")
	for _, path := range paths {
		d := path.Attributes["d"]
		r, g, b, _ := colorize(path.Attributes["fill"])
		if r == 255 && g == 255 && b == 255 {
			continue
		}
		pdf.SetFillColor(r, g, b)
		// pdf.SetDrawColor(r, g, b)
		pdf.SetLineWidth(3)
		pdf.DrawPath(d)
	}

	// // Extract and render text
	// for _, t := range icon.Find("text") {
	// 	x, y := t.Bounds().TopLeft()
	// 	content := t.Content
	// 	fontSize, _ := strconv.ParseFloat(t.GetAttribute("font-size", "12"), 64) // Default to 12 if not specified

	// 	// Load and set font (you'll need to have the font file)
	// 	pdf.AddUTF8Font("Roboto", "", "Roboto-Regular.ttf") // Adjust as needed
	// 	pdf.SetFont("Roboto", "", fontSize)
	// 	pdf.SetTextColor(255, 255, 255) // White

	// 	pdf.Text(x, y, content)
	// }

	err = pdf.OutputFileAndClose("output.pdf")
	if err != nil {
		log.Fatalf("error creating PDF: %v", err)
	}
}
