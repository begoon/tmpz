# Async file download in JavaScript and Python

## Goals

1. Implement async file download in JavaScript and Python.
2. Compare the download speed.
3. Compare the order of downloads.
4. Compare the error handling.

## Python

```bash
poetry install
poetry shell

python main.py
```

### Python Results

```log
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
2: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
1: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
5: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
3: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
0: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
9: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
8: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
7: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
6: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
[[10485760, 0], [10485760, 1], [10485760, 2], [10485760, 3], Exception('random exception: n=4'), [10485760, 5], [10485760, 6], [10485760, 7], [10485760, 8], [10485760, 9]]
10 files downloaded in 23.77 seconds
throughput 3.79 MB/s
```

## JavaScript

```bash
deno run -A main.js
```

or

```bash
bun main.js
```

### JavaScript results

```log
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
downloading http://ipv4.download.thinkbroadband.com/10MB.zip
0: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
8: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
7: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
3: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
5: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
1: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
6: downloaded http://ipv4.download.thinkbroadband.com/10MB.zip, 10485760 bytes
[
  { status: "fulfilled", value: { n: 0, sz: 10485760 } },
  { status: "fulfilled", value: { n: 1, sz: 10485760 } },
  {
    status: "rejected",
    reason: Error: random error: n=2
    at download_file (file:///Users/...[reducted].../async-download/main.ts:9:36)
    at file:///Users/...[reducted].../async-download/main.ts:21:54
    at Array.map (<anonymous>)
    at main (file:///Users/...[reducted].../async-download/main.ts:21:40)
    at file:///Users/...[reducted].../async-download/main.ts:36:1
  },
  { status: "fulfilled", value: { n: 3, sz: 10485760 } },
  {
    status: "rejected",
    reason: Error: random error: n=4
    at download_file (file:///Users/...[reducted].../async-download/main.ts:9:36)
    at file:///Users/...[reducted].../async-download/main.ts:21:54
    at Array.map (<anonymous>)
    at main (file:///Users/...[reducted].../async-download/main.ts:21:40)
    at file:///Users/...[reducted].../async-download/main.ts:36:1
  },
  { status: "fulfilled", value: { n: 5, sz: 10485760 } },
  { status: "fulfilled", value: { n: 6, sz: 10485760 } },
  { status: "fulfilled", value: { n: 7, sz: 10485760 } },
  { status: "fulfilled", value: { n: 8, sz: 10485760 } },
  {
    status: "rejected",
    reason: Error: random error: n=9
    at download_file (file:///Users/...[reducted].../async-download/main.ts:9:36)
    at file:///Users/...[reducted].../async-download/main.ts:21:54
    at Array.map (<anonymous>)
    at main (file:///Users/...[reducted].../async-download/main.ts:21:40)
    at file:///Users/...[reducted].../async-download/main.ts:36:1
  }
]
10 files downloaded in 19 seconds
throughput: 3.78 MB/s
```

## Conclusion

1. Both Python and JavaScript download speeds are about the same.
2. As a result, the order of resolved Promises in JavaScript and Async Tasks in Python is preserved.
