package main

import (
	"bufio"
	"bytes"
	"errors"
	"fmt"
	"io"
	"os"
	"regexp"
	"strconv"
	"strings"
	"unicode"
)

type Macro struct {
	Body string
}

// GPM is a small general-purpose macro processor.
// Features:
//   - define(name, body) creates a macro NAME whose body can use $1..$9, $# (argc), $* (joined args).
//   - undef(name) removes a macro.
//   - ifelse(cond, then, else) picks then if cond is non-empty and not "0"; else otherwise.
//   - Invocation syntax: NAME(arg1, arg2, ...). Arguments may contain nested macro calls and parentheses.
//   - Recursive expansion with a depth cap to avoid runaway loops.
type GPM struct {
	macros   map[string]Macro
	maxDepth int // Max recursion depth while expanding macros
}

func NewGPM() *GPM {
	g := &GPM{
		macros:   make(map[string]Macro),
		maxDepth: 256,
	}
	// Built-ins are dispatched specially, but we reserve names to avoid user override confusion.
	g.macros["define"] = Macro{Body: ""} // handled as builtin
	g.macros["undef"] = Macro{Body: ""}  // handled as builtin
	g.macros["ifelse"] = Macro{Body: ""} // handled as builtin
	return g
}

func (g *GPM) Define(name, body string) {
	g.macros[name] = Macro{Body: body}
}

func (g *GPM) Undef(name string) {
	delete(g.macros, name)
}

func (g *GPM) Expand(input string) (string, error) {
	var prev string
	v := input
	for depth := 0; depth < g.maxDepth; depth++ {
		prev = v
		var err error
		v, err = g.expandOnePass(v)
		if err != nil {
			return "", err
		}
		if v == prev {
			return v, nil // no changes in this pass
		}
	}
	return "", errors.New("expansion exceeded max recursion depth (possible infinite recursion)")
}

// expandOnePass scans the string for NAME(args...) patterns and expands them once
func (g *GPM) expandOnePass(s string) (string, error) {
	var b strings.Builder
	i := 0
	for i < len(s) {
		// Skip to identifier start
		if !isIdentStart(rune(s[i])) {
			b.WriteByte(s[i])
			i += 1
			continue
		}
		start := i
		i += 1
		for i < len(s) && isIdentPart(rune(s[i])) {
			i += 1
		}
		name := s[start:i]

		// Optional whitespace before '('
		j := i
		for j < len(s) && isSpace(rune(s[j])) {
			j += 1
		}
		if j >= len(s) || s[j] != '(' {
			// Not a macro call, so just write the identifier.
			b.WriteString(name)
			i = j
			continue
		}

		// parse argument list
		args, nextIdx, ok := parseArgList(s, j)
		if !ok {
			// not a well-formed call, so treat as plain text
			b.WriteString(s[start:nextIdx])
			i = nextIdx
			continue
		}

		// dispatch expansion
		exp, err := g.expandCall(name, args)
		if err != nil {
			return "", err
		}
		b.WriteString(exp)
		i = nextIdx
	}
	return b.String(), nil
}

func isIdentStart(r rune) bool {
	return unicode.IsLetter(r) || r == '_'
}

func isIdentPart(r rune) bool {
	return unicode.IsLetter(r) || unicode.IsDigit(r) || r == '_' || r == '-'
}

func isSpace(r rune) bool { return unicode.IsSpace(r) }

// parseArgList parses "(...)" starting at s[idx]=='('.
// Returns args, index just after ')', and ok flag.
func parseArgList(s string, idx int) ([]string, int, bool) {
	if idx >= len(s) || s[idx] != '(' {
		return nil, idx, false
	}
	i := idx + 1
	depth := 1
	var args []string
	var cur bytes.Buffer
	inString := false
	var stringQuote rune

	for i < len(s) {
		ch := rune(s[i])

		if inString {
			cur.WriteRune(ch)
			// handle escapes inside strings
			switch ch {
			case '\\':
				i += 1
				if i < len(s) {
					cur.WriteByte(s[i])
				}
			case stringQuote:
				inString = false
			}
			i += 1
			continue
		}

		switch ch {
		case '"', '\'':
			inString = true
			stringQuote = ch
			cur.WriteRune(ch)
			i += 1
		case '(':
			depth++
			cur.WriteRune(ch)
			i += 1
		case ')':
			depth--
			if depth == 0 {
				// finalize last arg
				args = append(args, strings.TrimSpace(cur.String()))
				i += 1
				return args, i, true
			}
			cur.WriteRune(ch)
			i += 1
		case ',':
			if depth == 1 {
				args = append(args, strings.TrimSpace(cur.String()))
				cur.Reset()
				i += 1
				continue
			}
			cur.WriteRune(ch)
			i += 1
		default:
			cur.WriteRune(ch)
			i += 1
		}
	}
	// unmatched '('
	return nil, len(s), false
}

var dollarParamRe = regexp.MustCompile(`\$(\*|#|[0-9])`)

func (g *GPM) expandUserMacro(name string, body string, args []string) (string, error) {
	// Replace $* , $# , $1..$9
	return dollarParamRe.ReplaceAllStringFunc(body, func(m string) string {
		tag := m[1:]
		switch tag {
		case "*":
			return strings.Join(args, ",")
		case "#":
			return strconv.Itoa(len(args))
		default:
			// numeric
			idx := int(tag[0] - '0')
			if idx == 0 {
				return name // $0 -> macro name (nice to have)
			}
			if idx >= 1 && idx <= len(args) {
				return args[idx-1]
			}
			return "" // missing arg -> empty
		}
	}), nil
}

func truthy(s string) bool {
	t := strings.TrimSpace(s)
	return t != "" && t != "0"
}

func (g *GPM) expandCall(name string, args []string) (string, error) {
	switch name {
	case "define":
		if len(args) != 2 {
			return fmt.Sprintf("/* define expects 2 args, got %d */", len(args)), nil
		}
		mname := strings.TrimSpace(stripQuotes(args[0]))
		body := args[1]
		g.Define(mname, body)
		return "", nil
	case "undef":
		if len(args) != 1 {
			return fmt.Sprintf("/* undef expects 1 arg, got %d */", len(args)), nil
		}
		mname := strings.TrimSpace(stripQuotes(args[0]))
		g.Undef(mname)
		return "", nil
	case "ifelse":
		// ifelse(cond, then, else)
		if len(args) < 2 {
			return fmt.Sprintf("/* ifelse expects at least 2 args, got %d */", len(args)), nil
		}
		cond := args[0]
		thenPart := args[1]
		elsePart := ""
		if len(args) >= 3 {
			elsePart = args[2]
		}
		if truthy(cond) {
			return g.Expand(thenPart) // expand chosen branch
		}
		return g.Expand(elsePart)
	default:
		// user-defined macro?
		m, ok := g.macros[name]
		if !ok {
			// Unknown macro — leave as-is
			// Reconstruct original text NAME(args...)
			var rec strings.Builder
			rec.WriteString(name)
			rec.WriteByte('(')
			for i, a := range args {
				if i > 0 {
					rec.WriteByte(',')
				}
				rec.WriteString(a)
			}
			rec.WriteByte(')')
			return rec.String(), nil
		}
		// Built-in stubs should not expand here
		if name == "define" || name == "undef" || name == "ifelse" {
			return "", nil
		}
		expanded, err := g.expandUserMacro(name, m.Body, args)
		if err != nil {
			return "", err
		}
		// Recurse into the expansion
		return g.Expand(expanded)
	}
}

func stripQuotes(s string) string {
	s = strings.TrimSpace(s)
	if len(s) >= 2 {
		if (s[0] == '"' && s[len(s)-1] == '"') || (s[0] == '\'' && s[len(s)-1] == '\'') {
			return s[1 : len(s)-1]
		}
	}
	return s
}

func main() {
	gpm := NewGPM()

	// Read entire stdin
	data, err := io.ReadAll(bufio.NewReader(os.Stdin))
	if err != nil {
		fmt.Fprintln(os.Stderr, "read error:", err)
		os.Exit(1)
	}
	out, err := gpm.Expand(string(data))
	if err != nil {
		fmt.Fprintln(os.Stderr, "expand error:", err)
		os.Exit(2)
	}
	fmt.Print(out)
}
