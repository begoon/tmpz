package main

import (
	"testing"
)

func runGPM(t *testing.T, in string) string {
	t.Helper()
	g := NewGPM()
	v, err := g.Expand(in)
	if err != nil {
		t.Fatalf("expand error: %v", err)
	}
	return v
}

func TestExamples(t *testing.T) {
	tests := []struct {
		name string
		in   string
		want string
	}{
		{
			name: "greet",
			in:   `define(GREET, "hello, $1!")GREET(GPM)`,
			want: `"hello, GPM!"`,
		},
		{
			name: "arithmetic templating with nesting",
			in:   `define(ADD, "($1)+($2)")define(MUL, "($1)*($2)")ADD(2, MUL(3, 4))`,
			want: `"(2)+("(3)*(4)")"`,
		},
		{
			name: "dollar star and count",
			in:   `define(INFO, "args=$#, all=[$*]")INFO(a, b, c)`,
			want: `"args=3, all=[a,b,c]"`,
		},
		{
			name: "conditionals ifelse",
			in:   `define(CHOICE, "ifelse($1, 'YES', 'NO')")CHOICE(1)CHOICE(0)CHOICE(   )`,
			want: `"'YES'""'NO'""'NO'"`,
		},
		{
			name: "macro generates another macro",
			in:   `define(MAKE_PAIR, "define(PAIR, '($1,$2)')")MAKE_PAIR(x, y)PAIR(a, b)`,
			want: `""'(x,y)'`,
		},
		{
			name: "undef macro",
			in:   `define(VERSION, "1.2.3")VERSION()undef(VERSION)VERSION()`,
			want: `"1.2.3"VERSION()`,
		},
	}

	for _, tc := range tests {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			got := runGPM(t, tc.in)
			if got != tc.want {
				t.Fatalf("unexpected output.\n--- got ---\n%q\n--- want ---\n%q", got, tc.want)
			}
		})
	}
}
