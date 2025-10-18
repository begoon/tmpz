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

// ======= UTILITIES (Pascal-ish) =======
function splitLines(text) {
    // no chaining
    var tmp = text.split("\n");
    var out = [];
    var i;
    for (i = 0; i < tmp.length; i++) {
        out.push(tmp[i]);
    }
    return out;
}

function isDigit(ch) {
    return ch >= "0" && ch <= "9";
}

// read up to maxCount integers from a line (if maxCount <= 0 => read all)
function readInts(line, maxCount) {
    var nums = [];
    var i = 0;
    var n = line.length;
    while (i < n) {
        while (i < n && !isDigit(line[i])) i++;
        if (i >= n) break;
        var j = i;
        while (j < n && isDigit(line[j])) j++;
        var val = parseInt(line.substring(i, j), 10);
        nums.push(val);
        if (maxCount > 0 && nums.length === maxCount) break;
        i = j;
    }
    return nums;
}

function trim(s) {
    var i = 0,
        j = s.length - 1;
    while (i <= j && (s[i] === " " || s[i] === "\t" || s[i] === "\r")) i++;
    while (j >= i && (s[j] === " " || s[j] === "\t" || s[j] === "\r")) j--;
    return s.substring(i, j + 1);
}

// ======= PARSE INPUT =======
var lines = splitLines(raw);
var idx = 0;

// skip leading empties
while (idx < lines.length && trim(lines[idx]) === "") idx++;
var n = parseInt(trim(lines[idx]), 10);
idx++;

// adjacency lists: adj[1..n] each is array of neighbors
var adj = [];
var v;
for (v = 0; v <= n; v++) adj.push([]);

while (idx < lines.length) {
    while (idx < lines.length && trim(lines[idx]) === "") idx++;
    if (idx >= lines.length) break;

    var headLine = lines[idx];
    idx++;
    var headNums = readInts(headLine, 2);
    if (headNums.length === 0) break;
    if (headNums[0] === 0) break; // trailing 0
    var u = headNums[0];
    // count is headNums[1], but we don't strictly need to trust it

    while (idx < lines.length && trim(lines[idx]) === "") idx++;
    if (idx >= lines.length) break;
    var listLine = lines[idx];
    idx++;

    var neigh = readInts(listLine, 0);

    // add undirected edges using arrays only; avoid duplicates manually
    var k, w;

    for (k = 0; k < neigh.length; k++) {
        w = neigh[k];
        // add w to adj[u] if not present
        var found = false,
            t;
        for (t = 0; t < adj[u].length; t++)
            if (adj[u][t] === w) {
                found = true;
                break;
            }
        if (!found) adj[u].push(w);

        // add u to adj[w] if not present
        if (w >= 1 && w <= n) {
            found = false;
            for (t = 0; t < adj[w].length; t++)
                if (adj[w][t] === u) {
                    found = true;
                    break;
                }
            if (!found) adj[w].push(u);
        }
    }
    // stop if a single line "0" follows (already handled by next loop start)
}

// ======= CONNECTIVITY MATRIX (49 x 49) =======
var matrix = []; // array of strings, each length n
var r, c;
for (r = 1; r <= n; r++) {
    var rowChars = [];
    for (c = 1; c <= n; c++) {
        if (r === c) rowChars.push(" ");
        else {
            var connected = false;
            var p;
            for (p = 0; p < adj[r].length; p++) {
                if (adj[r][p] === c) {
                    connected = true;
                    break;
                }
            }
            rowChars.push(connected ? "*" : " ");
        }
    }
    matrix.push(rowChars.join(""));
}

// ======= WELSH–POWELL GREEDY COLORING =======
var deg = [];
deg.push(0); // 0-th unused
for (v = 1; v <= n; v++) deg.push(adj[v].length);

// order vertices by degree descending (bubble sort to avoid callbacks)
var order = [];
for (v = 1; v <= n; v++) order.push(v);
var i, j, tmp;
for (i = 0; i < n - 1; i++) {
    for (j = 0; j < n - 1 - i; j++) {
        if (deg[order[j]] < deg[order[j + 1]]) {
            tmp = order[j];
            order[j] = order[j + 1];
            order[j + 1] = tmp;
        }
    }
}

var color = [];
for (v = 0; v <= n; v++) color.push(0);

var maxColor = 0;
for (i = 0; i < order.length; i++) {
    v = order[i];

    // usedColors[1..maxColor] boolean
    var usedColors = [];
    for (j = 0; j <= n; j++) usedColors.push(false);

    // mark colors of neighbors
    for (j = 0; j < adj[v].length; j++) {
        var nb = adj[v][j];
        var col = color[nb];
        if (col > 0) usedColors[col] = true;
    }

    // find smallest positive color not used
    var ctry = 1;
    while (ctry <= n && usedColors[ctry]) ctry++;
    color[v] = ctry;
    if (ctry > maxColor) maxColor = ctry;
}

// group states by color (arrays only)
var byColor = [];
for (i = 0; i <= maxColor; i++) byColor.push([]);
for (v = 1; v <= n; v++) {
    byColor[color[v]].push(v);
}

// sort each color group ascending (simple insertion sort)
function insertionSort(arr) {
    var a, b, key;
    for (a = 1; a < arr.length; a++) {
        key = arr[a];
        b = a - 1;
        while (b >= 0 && arr[b] > key) {
            arr[b + 1] = arr[b];
            b = b - 1;
        }
        arr[b + 1] = key;
    }
}

for (i = 1; i <= maxColor; i++) insertionSort(byColor[i]);

// ======= OUTPUT =======
console.log("Connectivity matrix (49 x 49):");
for (i = 0; i < matrix.length; i++) console.log(matrix[i]);

console.log("\nMax number of colors: " + maxColor);
for (i = 1; i <= maxColor; i++) {
    var line = "Color " + i + ":";
    for (j = 0; j < byColor[i].length; j++) line += (j === 0 ? " " : " ") + byColor[i][j];
    console.log(line);
}
