import { expect, test } from "bun:test";
import { parseNumber } from "../rk86_console.js";

test("parseNumber", () => {
    expect(parseNumber("")).toBe(NaN);
    expect(parseNumber(undefined)).toBe(NaN);

    expect(parseNumber("0x1A")).toBe(26);
    expect(parseNumber("$1A")).toBe(26);
    expect(parseNumber("1Ah")).toBe(26);
    expect(parseNumber("a")).toBe(10); // 'a-f' start hexadecimal
    expect(parseNumber("1a")).toBe(1);

    expect(parseNumber("10")).toBe(10);
    expect(parseNumber("0")).toBe(0);

    expect(parseNumber("abc")).toBe(0xabc);
    expect(parseNumber("1.5")).toBe(1);
});
