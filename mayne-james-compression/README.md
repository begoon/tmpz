# Mayne-James compression

## File format

```text
Magic   : "MJDC" (4 bytes)
u32     : dict_count (N)
repeat N times:
  u32   : entry_length
  bytes : entry
u32     : token_count (T)
repeat T times:
  u32   : token (dictionary index)
```
