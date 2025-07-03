function hex(v) {
    return v.toString(16).toUpperCase();
}

export function hex8(v) {
    return hex(v & 0xff).padStart(2, "0");
}

export function hex16(v) {
    return hex(v & 0xffff).padStart(4, "0");
}

export function hexArray(array) {
    return array.map((c) => hex8(c)).join(" ");
}

export function fromHex(v) {
    if (typeof v === "string") {
        return v.startsWith("0x") ? parseInt(v, 16) : parseInt(v);
    }
    return v;
}
