# Notes & extensions

- Standard features included: grouping `()`, ordered choice `/`, concatenation,
  `*` `+` `?`, predicates `!` and `&`, literals `'...'`/`"..."`, `[...]`
  character classes (with ranges, escapes, and `^` negation), wildcard `.`.

- EOI: Use `!.` (negative lookahead for any char) to assert end-of-input,
  as shown in `Expr <- _ AddSub !.`.

- AST shape:

  - Every rule application returns an ASTNode labeled with that rule name.
  - Structural operators (seq, choice, *, etc.) are represented with small
    helper labels like `seq`, `star` when needed to preserve structure.
    You can post-process to prune/reshape as you like.

- Performance: The runtime is packrat (memoized) and safe for typical PEGs
  (no left recursion support). Avoid left-recursive grammars, or transform them.

- Empty-match guard: `*` breaks if the inner expression matches the empty
  string to avoid infinite loops.
