function X(i) {
    console.log("X", i);
}

let f = X;

for (let i = 0; i < 10; i++) {
    const t = f;
    f = (j) => {
        console.log("lambda", j);
        t(i);
    };
}

f(100);
