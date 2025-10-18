// us-map-coloring.js

const raw = `
49

1 2    WASHINGTON
2 5

2 4    OREGON
1 3 4 5

3 3    CALIFORNIA
2 4 7

4 5    NEVADA
2 3 5 6 7

5 6   IDAHO
1 2 4 6 8 9

6 5   UTAH
4 5 7 9 10

7 4   ARIZONA
3 4 6 11

8 4   MONTANA
5 9 12 13

9 6   WYOMING
5 6 8 10 13 14

10 6   COLORADO
6 9 11 14 15 16

11 4   NEW MEXICO
7 10 16 17

12 3   NORTH DAKOTA
8 13 18

13 6   SOUTH DAKOTA
8 9 12 14 18 19

14 6   NEBRASKA
9 10 13 15 19 20

15 4   KANSAS
10 14 16 20

16 6   OKLAHOMA
10 11 15 17 20 21

17 4   TEXAS
11 16 21 22

18 4   MINNESOTA
12 13 19 23

19 6   IOWA
13 14 18 20 23 24

20 8   MISSOURI
14 15 16 19 21 24 30 31

21 6   ARKANSAS
16 17 20 22 26 31

22 3   LOUISIANA
17 21 26

23 4   WISCONSIN
18 19 24 28

24 4   ILLINOIS
19 20 23 25

25 4   INDIANA
24 28 29 30

26 4   MISSISSIPPI
21 22 27 31

27 4   ALABAMA
26 31 32 33

28 3   MICHIGAN
23 25 29

29 5   OHIO
25 28 30 34 35

30 6   KENTUCKY
20 25 29 31 35 36

31 8   TENNESSEE
20 21 26 27 30 32 36 37

32 5   GEORGIA
27 31 33 37 38

33 2   FLORIDA
27 32

34 6   PENNSYLVANIA
29 35 39 40 41 42

35 5   WEST VIRGINIA
29 30 34 36 42

36 6   VIRGINIA
30 31 35 37 42 43

37 4   NORTH CAROLINA
31 32 36 38

38 2   SOUTH CAROLINA
32 37

39 5   NEW YORK
34 40 44 45 46

40 3   NEW JERSEY
34 39 41

41 3   DELAWARE
34 40 42

42 5   MARYLAND
34 35 36 41 43

43 2   WASHINGTON DC
36 42

44 3   VERMONT
39 45 48

45 5   MASSACHUSETTS
39 44 46 48 49

46 3   CONNECTICUT
39 45 49

47 1   MAINE
48

48 3   NEW HAMPSHIRE
44 45 47

49 2   RHODE ISLAND
45 46

0
`.trim();

// ---------- Parse ----------
const lines = raw.split(/\r?\n/).filter((l) => l.trim() !== "");
const n = parseInt(lines[0], 10);
if (isNaN(n) || n !== 49) {
    throw new Error("Expected first non-empty line to be '49'.");
}

// Helpers to extract "state_number number_of_connections" from line 1 and
// all integers from line 2. We ignore everything after the second integer on line 1.
function parseHeader(line) {
    const nums = (line.match(/\d+/g) || []).map(Number);
    if (nums.length < 2) throw new Error("Bad header line: " + line);
    return { id: nums[0], count: nums[1] };
}
function parseList(line) {
    return (line.match(/\d+/g) || []).map(Number);
}

let i = 1;
const adj = Array.from({ length: n + 1 }, () => new Set());

while (i < lines.length) {
    const line1 = lines[i++]; // e.g., "1 2    WASHINGTON"
    if (!line1) break;
    const head = parseHeader(line1);
    if (head.id === 0) break; // safety
    const line2 = lines[i++]; // e.g., "2 5"
    const neighbors = parseList(line2);

    // Undirected edges
    neighbors.forEach((v) => {
        adj[head.id].add(v);
        adj[v].add(head.id);
    });

    // Stop if we hit the trailing '0'
    if (lines[i] && lines[i].trim() === "0") break;
}

// ---------- Connectivity matrix ----------
const matrix = [];
for (let r = 1; r <= n; r++) {
    let row = "";
    for (let c = 1; c <= n; c++) {
        if (r === c) row += " ";
        else row += adj[r].has(c) ? "*" : " ";
    }
    if (row.length !== n) throw new Error("Row length mismatch");
    matrix.push(row);
}

// ---------- Welsh–Powell greedy coloring ----------
const degrees = Array.from({ length: n + 1 }, (_, v) => v)
    .slice(1)
    .map((v) => [v, adj[v].size])
    .sort((a, b) => b[1] - a[1]) // desc by degree
    .map(([v]) => v);

const colorOf = Array(n + 1).fill(0);
let maxColor = 0;

for (const v of degrees) {
    const used = new Set();
    for (const u of adj[v]) {
        if (colorOf[u] > 0) used.add(colorOf[u]);
    }
    // smallest positive color not used
    let c = 1;
    while (used.has(c)) c++;
    colorOf[v] = c;
    if (c > maxColor) maxColor = c;
}

// group states by color (numbers only)
const byColor = Array.from({ length: maxColor + 1 }, () => []);
for (let v = 1; v <= n; v++) byColor[colorOf[v]].push(v);

// ---------- Output ----------
console.log("Connectivity matrix (49 x 49):");
for (const row of matrix) console.log(row);
console.log("\nMax number of colors:", maxColor);
for (let c = 1; c <= maxColor; c++) {
    console.log(`Color ${c}: ${byColor[c].sort((a, b) => a - b).join(" ")}`);
}
