export const nice = <T>(object: T) =>
    JSON.stringify(
        object,
        (k, v) => {
            if (
                typeof k === "string" &&
                Array.isArray(v) &&
                v.every((x) => typeof x === "number")
            )
                return v.length > 5
                    ? v.slice(0, 5).join(", ") + "..."
                    : v.join(", ");
            return v;
        },
        2
    );
