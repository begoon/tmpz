package main

import (
	"bytes"
	"slices"
)

type BPERule struct {
	Pair  [2]byte
	Token byte
}

func CompressBPE(input []byte, iterations int) ([]byte, []BPERule) {
	rules := []BPERule{}
	data := slices.Clone(input)

	nextToken := byte(255)

	for range iterations {
		counts := make(map[[2]byte]int)
		for j := range len(data) - 1 {
			pair := [2]byte{data[j], data[j+1]}
			counts[pair]++
		}

		var maxPair [2]byte
		maxCount := 0
		for pair, count := range counts {
			if count > maxCount {
				maxCount = count
				maxPair = pair
			}
		}

		if maxCount < 2 || nextToken < 1 {
			break
		}

		rules = append(rules, BPERule{Pair: maxPair, Token: nextToken})

		var buffer bytes.Buffer
		j := 0
		for j < len(data) {
			if j < len(data)-1 && data[j] == maxPair[0] && data[j+1] == maxPair[1] {
				buffer.WriteByte(nextToken)
				j += 2
			} else {
				buffer.WriteByte(data[j])
				j++
			}
		}
		data = buffer.Bytes()
		nextToken--
	}

	return data, rules
}

func DecompressBPE(input []byte, rules []BPERule) []byte {
	data := slices.Clone(input)
	for i := len(rules) - 1; i >= 0; i-- {
		rule := rules[i]
		var buffer bytes.Buffer
		for _, b := range data {
			if b == rule.Token {
				buffer.WriteByte(rule.Pair[0])
				buffer.WriteByte(rule.Pair[1])
			} else {
				buffer.WriteByte(b)
			}
		}
		data = buffer.Bytes()
	}
	return data
}
