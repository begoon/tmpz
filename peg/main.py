from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class ASTNode:
    """
    AST for the INPUT being parsed by your grammar (not the grammar itself).
    """

    rule: str  # rule name that produced this node
    text: str  # matched substring
    start: int  # start offset in input
    end: int  # end offset in input
    children: List["ASTNode"]  # child nodes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule,
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "children": [c.to_dict() for c in self.children],
        }


class Expr:
    uid_counter = 0

    def __init__(self):
        self.uid = Expr.uid_counter
        Expr.uid_counter += 1


class Literal(Expr):
    def __init__(self, value: str):
        super().__init__()
        self.value = value


class Dot(Expr):
    def __init__(self):
        super().__init__()


class CharClass(Expr):
    def __init__(
        self,
        chars: Set[str],
        negate: bool = False,
        ranges: List[Tuple[str, str]] = [],
    ):
        super().__init__()
        self.chars = chars
        self.negate = negate
        self.ranges = ranges  # list of (start, end) inclusive

    def contains(self, ch: str) -> bool:
        in_set = ch in self.chars or any(a <= ch <= b for a, b in self.ranges)
        return (not in_set) if self.negate else in_set


class Ref(Expr):
    def __init__(self, name: str):
        super().__init__()
        self.name = name


class Sequence(Expr):
    def __init__(self, items: List[Expr]):
        super().__init__()
        self.items = items


class Choice(Expr):
    def __init__(self, alts: List[Expr]):
        super().__init__()
        self.alts = alts


class Not(Expr):
    def __init__(self, inner: Expr):
        super().__init__()
        self.inner = inner


class And(Expr):
    def __init__(self, inner: Expr):
        super().__init__()
        self.inner = inner


class Star(Expr):
    def __init__(self, inner: Expr):
        super().__init__()
        self.inner = inner


class Plus(Expr):
    def __init__(self, inner: Expr):
        super().__init__()
        self.inner = inner


class Opt(Expr):
    def __init__(self, inner: Expr):
        super().__init__()
        self.inner = inner


# Grammar parser (parses PEG grammar text)


class GrammarParser:
    def __init__(self, src: str):
        self.src = src
        self.n = len(src)
        self.i = 0

    def eof(self) -> bool:
        return self.i >= self.n

    def peek(self, k: int = 0) -> str:
        j = self.i + k
        return "" if j >= self.n else self.src[j]

    def advance(self, n: int = 1):
        self.i += n

    def skip_ws_and_comments(self):
        while True:
            # whitespace
            moved = False
            while not self.eof() and self.peek().isspace():
                self.advance()
                moved = True
            # comments: #..., //..., /* ... */
            if self.src.startswith("//", self.i):
                moved = True
                while not self.eof() and self.peek() not in "\r\n":
                    self.advance()
                continue
            if self.src.startswith("#", self.i):
                moved = True
                while not self.eof() and self.peek() not in "\r\n":
                    self.advance()
                continue
            if self.src.startswith("/*", self.i):
                moved = True
                self.advance(2)
                while not self.eof() and not self.src.startswith("*/", self.i):
                    self.advance()
                if self.src.startswith("*/", self.i):
                    self.advance(2)
                continue
            if not moved:
                break

    def expect(self, s: str):
        self.skip_ws_and_comments()
        if not self.src.startswith(s, self.i):
            raise SyntaxError(f"Expected '{s}' at {self.i}")
        self.advance(len(s))

    def read_identifier(self) -> str:
        self.skip_ws_and_comments()
        if self.eof() or not (self.peek().isalpha() or self.peek() == "_"):
            raise SyntaxError(f"Identifier expected at {self.i}")
        j = self.i + 1
        while j < self.n and (self.src[j].isalnum() or self.src[j] == "_"):
            j += 1
        ident = self.src[self.i : j]
        self.i = j
        return ident

    def read_string(self) -> str:
        self.skip_ws_and_comments()
        q = self.peek()
        if q not in ("'", '"'):
            raise SyntaxError(f"String literal expected at {self.i}")
        self.advance()
        out = []
        while not self.eof():
            ch = self.peek()
            if ch == "\\":
                self.advance()
                if self.eof():
                    raise SyntaxError("Bad escape at EOF")
                esc = self.peek()
                self.advance()
                mapping = {
                    "n": "\n",
                    "r": "\r",
                    "t": "\t",
                    "\\": "\\",
                    "'": "'",
                    '"': '"',
                }
                out.append(mapping.get(esc, esc))
            elif ch == q:
                self.advance()
                return "".join(out)
            else:
                out.append(ch)
                self.advance()
        raise SyntaxError("Unterminated string literal")

    def read_class(self) -> CharClass:
        self.skip_ws_and_comments()
        if self.peek() != "[":
            raise SyntaxError(f"Character class expected at {self.i}")
        self.advance()
        negate = False
        chars: Set[str] = set()
        ranges: List[Tuple[str, str]] = []
        if self.peek() == "^":
            negate = True
            self.advance()

        def read_char_in_class() -> str:
            if self.eof():
                raise SyntaxError("Unterminated character class")
            ch = self.peek()
            self.advance()
            if ch == "\\":
                if self.eof():
                    raise SyntaxError("Bad escape in class")
                esc = self.peek()
                self.advance()
                mapping = {
                    "n": "\n",
                    "r": "\r",
                    "t": "\t",
                    "\\": "\\",
                    "]": "]",
                    "-": "-",
                    "[": "[",
                    "'": "'",
                    '"': '"',
                }
                return mapping.get(esc, esc)
            return ch

        prev: Optional[str] = None
        while not self.eof() and self.peek() != "]":
            ch = read_char_in_class()
            if ch == "-" and prev is not None and self.peek() != "]":
                # range
                high = read_char_in_class()
                if ord(prev) > ord(high):
                    prev, high = high, prev
                ranges.append((prev, high))
                prev = None
            else:
                if prev is not None:
                    chars.add(prev)
                prev = ch
        if prev is not None:
            chars.add(prev)
        if self.peek() != "]":
            raise SyntaxError("Unterminated character class")
        self.advance()  # ]
        return CharClass(chars, negate, ranges)

    # grammar (meta) parsing: Expr -> Choice / Seq / Prefix / Suffix / Primary

    def parse(self) -> Tuple[str, Dict[str, Expr]]:
        rules: Dict[str, Expr] = {}
        order: List[str] = []
        while True:
            self.skip_ws_and_comments()
            if self.eof():
                break
            name = self.read_identifier()
            self.skip_ws_and_comments()
            self.expect("<-")
            expr = self.parse_expr()
            rules[name] = expr
            order.append(name)
            # optional trailing semicolon or newline; already skipped
            # in skip_ws...
        if not order:
            raise SyntaxError("No rules in grammar")
        return order[0], rules

    def parse_expr(self) -> Expr:
        # choice: Seq ('/' Seq)*
        left = self.parse_seq()
        alts = [left]
        while True:
            self.skip_ws_and_comments()
            if self.peek() == "/":
                self.advance()
                right = self.parse_seq()
                alts.append(right)
            else:
                break
        return left if len(alts) == 1 else Choice(alts)

    def parse_seq(self) -> Expr:
        # sequence: one or more Prefix; empty sequence -> empty (epsilon) not
        # allowed here; we treat absence as empty?
        items: List[Expr] = []
        while True:
            self.skip_ws_and_comments()
            # stop tokens for sequence: ) or / or rule end (lookahead
            # for identifier '<-')
            if self.eof():
                break
            if self.peek() in ")/":
                break
            # stop if next token looks like a rule name followed by '<-'
            # (simple heuristic to avoid greedily pulling next rule)
            k = self.i
            # lookahead: Identifier '<-'
            looked_rule = False
            if self.peek().isalpha() or self.peek() == "_":
                j = k + 1
                while j < self.n and (
                    self.src[j].isalnum() or self.src[j] == "_"
                ):
                    j += 1
                # skip ws/comments
                tmp = GrammarParser(self.src[j:])
                tmp.i = 0
                tmp.skip_ws_and_comments()
                if self.src.startswith("<-", j + tmp.i):
                    looked_rule = True
            if looked_rule:
                break
            item = self.parse_prefix()
            items.append(item)
        if not items:
            # Empty sequence is represented as Sequence([]). Runtime treats it
            # as epsilon.
            return Sequence([])
        return items[0] if len(items) == 1 else Sequence(items)

    def parse_prefix(self) -> Expr:
        self.skip_ws_and_comments()
        if self.peek() == "!":
            self.advance()
            return Not(self.parse_suffix())
        if self.peek() == "&":
            self.advance()
            return And(self.parse_suffix())
        return self.parse_suffix()

    def parse_suffix(self) -> Expr:
        primary = self.parse_primary()
        self.skip_ws_and_comments()
        if not self.eof():
            ch = self.peek()
            if ch in "*+?":
                self.advance()
                if ch == "*":
                    return Star(primary)
                elif ch == "+":
                    return Plus(primary)
                elif ch == "?":
                    return Opt(primary)
        return primary

    def parse_primary(self) -> Expr:
        self.skip_ws_and_comments()
        ch = self.peek()
        if ch == "(":
            self.advance()
            inner = self.parse_expr()
            self.skip_ws_and_comments()
            if self.peek() != ")":
                raise SyntaxError(f"Missing ')' at {self.i}")
            self.advance()
            return inner  # grouping doesn't need a separate node
        if ch == ".":
            self.advance()
            return Dot()
        if ch in ("'", '"'):
            s = self.read_string()
            return Literal(s)
        if ch == "[":
            return self.read_class()
        # identifier
        name = self.read_identifier()
        return Ref(name)


# Runtime PEG parser (packrat)


class PEGParser:
    def __init__(self, rules: Dict[str, Expr], start: str, text: str):
        self.rules = rules
        self.start = start
        self.text = text
        self.n = len(text)
        self.memo: Dict[
            Tuple[int, int], Optional[Tuple[Optional[ASTNode], int]]
        ] = {}
        # expr uid -> rule name (for wrapping AST nodes)
        self.rule_names: Dict[int, str] = {}
        for name, expr in rules.items():
            self._collect_rule_names(expr, name)

        self.furthest_fail = 0  # for basic error reporting

    def _collect_rule_names(self, expr: Expr, name: str):
        """
        Mark top-level expression as belonging to a rule (for AST node
        labeling).
        """
        # We only wrap at rule entry; inner nodes use structure, but we only
        # force rule-name nodes at rule boundaries.
        self.rule_names[expr.uid] = name
        # No recursion here: rule-level only.

    # ---- Public API ----

    def parse(self, require_full: bool = True) -> ASTNode:
        node, pos = self._parse_expr(self.rules[self.start], 0)
        if node is None:
            self._fail("Parse failed", self.furthest_fail)
        if require_full and pos != self.n:
            self._fail(f"Unconsumed input at {pos}", pos)
        return node

    # ---- Core evaluation with memoization ----

    def _parse_expr(
        self,
        expr: Expr,
        pos: int,
    ) -> Tuple[Optional[ASTNode], int]:
        key = (expr.uid, pos)
        if key in self.memo:
            cached = self.memo[key]
            return cached if cached is not None else (None, pos)

        fn = {
            Literal: self._eval_literal,
            Dot: self._eval_dot,
            CharClass: self._eval_class,
            Ref: self._eval_ref,
            Sequence: self._eval_sequence,
            Choice: self._eval_choice,
            Not: self._eval_not,
            And: self._eval_and,
            Star: self._eval_star,
            Plus: self._eval_plus,
            Opt: self._eval_opt,
        }[type(expr)]

        node, new_pos = fn(expr, pos)
        # store success; for failure we still memoize a marker (None)
        # to avoid rework
        self.memo[key] = (node, new_pos) if node is not None else None
        return node, new_pos

    def _eval_literal(self, e: Literal, pos: int):
        s = e.value
        if self.text.startswith(s, pos):
            end = pos + len(s)
            return (
                ASTNode(
                    rule=self._label_for(e),
                    text=self.text[pos:end],
                    start=pos,
                    end=end,
                    children=[],
                ),
                end,
            )
        self._note_fail(pos)
        return None, pos

    def _eval_dot(self, e: Dot, pos: int):
        if pos < self.n:
            end = pos + 1
            return (
                ASTNode(
                    rule=self._label_for(e),
                    text=self.text[pos:end],
                    start=pos,
                    end=end,
                    children=[],
                ),
                end,
            )
        self._note_fail(pos)
        return None, pos

    def _eval_class(self, e: CharClass, pos: int):
        if pos < self.n and e.contains(self.text[pos]):
            end = pos + 1
            return (
                ASTNode(
                    rule=self._label_for(e),
                    text=self.text[pos:end],
                    start=pos,
                    end=end,
                    children=[],
                ),
                end,
            )
        self._note_fail(pos)
        return None, pos

    def _eval_ref(self, e: Ref, pos: int):
        rule_expr = self.rules.get(e.name)
        if rule_expr is None:
            raise NameError(f"Undefined rule: {e.name}")
        node, new_pos = self._parse_expr(rule_expr, pos)
        if node is None:
            return None, pos
        # wrap as rule node to label subtree with rule name
        return (
            ASTNode(
                rule=e.name,
                text=self.text[pos:new_pos],
                start=pos,
                end=new_pos,
                children=[node] if node.rule != e.name else node.children,
            ),
            new_pos,
        )

    def _eval_sequence(self, e: Sequence, pos: int):
        nodes: List[ASTNode] = []
        cur = pos
        for item in e.items:
            node, cur2 = self._parse_expr(item, cur)
            if node is None:
                return None, pos
            nodes.append(node)
            cur = cur2
        # flatten single-child sequences
        text = self.text[pos:cur]
        label = self._label_for(e)
        if label is not None and label in self.rules:
            # sequence tied to a top-level rule (rare); wrap
            return (
                ASTNode(
                    rule=label,
                    text=text,
                    start=pos,
                    end=cur,
                    children=nodes,
                ),
                cur,
            )
        # otherwise produce a neutral container node to preserve structure
        return (
            ASTNode(
                rule=label or "_seq",
                text=text,
                start=pos,
                end=cur,
                children=nodes,
            ),
            cur,
        )

    def _eval_choice(self, e: Choice, pos: int):
        for alt in e.alts:
            node, new_pos = self._parse_expr(alt, pos)
            if node is not None:
                return node, new_pos
        self._note_fail(pos)
        return None, pos

    def _eval_not(self, e: Not, pos: int):
        node, _ = self._parse_expr(e.inner, pos)
        if node is None:
            # succeed without consuming
            return (
                ASTNode(rule="_not", text="", start=pos, end=pos, children=[]),
                pos,
            )
        self._note_fail(pos)
        return None, pos

    def _eval_and(self, e: And, pos: int):
        node, _ = self._parse_expr(e.inner, pos)
        if node is not None:
            # succeed without consuming
            return (
                ASTNode(rule="_and", text="", start=pos, end=pos, children=[]),
                pos,
            )
        self._note_fail(pos)
        return None, pos

    def _eval_star(self, e: Star, pos: int):
        nodes: List[ASTNode] = []
        cur = pos
        while True:
            node, new_pos = self._parse_expr(e.inner, cur)
            if node is None:
                break
            if new_pos == cur:
                # empty match guard to avoid infinite loops
                break
            nodes.append(node)
            cur = new_pos
        text = self.text[pos:cur]
        return (
            ASTNode(
                rule="_star",
                text=text,
                start=pos,
                end=cur,
                children=nodes,
            ),
            cur,
        )

    def _eval_plus(self, e: Plus, pos: int):
        first, cur = self._parse_expr(e.inner, pos)
        if first is None:
            return None, pos
        rest_node, endpos = self._eval_star(Star(e.inner), cur)
        nodes = [first] + rest_node.children
        text = self.text[pos:endpos]
        return (
            ASTNode(
                rule="_plus",
                text=text,
                start=pos,
                end=endpos,
                children=nodes,
            ),
            endpos,
        )

    def _eval_opt(self, e: Opt, pos: int):
        node, new_pos = self._parse_expr(e.inner, pos)
        if node is None:
            return (
                ASTNode(rule="_opt", text="", start=pos, end=pos, children=[]),
                pos,
            )
        return (
            ASTNode(
                rule="_opt",
                text=self.text[pos:new_pos],
                start=pos,
                end=new_pos,
                children=[node],
            ),
            new_pos,
        )

    def _label_for(self, e: Expr) -> Optional[str]:
        # Only top-level expressions (rule bodies) have a stable rule label.
        # Others return None.
        return self.rule_names.get(e.uid)

    def _note_fail(self, pos: int):
        if pos > self.furthest_fail:
            self.furthest_fail = pos

    def _fail(self, msg: str, pos: int):
        # Simple line/col computation
        s = self.text
        line = s.count("\n", 0, pos) + 1
        col = pos - (
            s.rfind("\n", 0, pos) if s.rfind("\n", 0, pos) != -1 else -1
        )
        raise SyntaxError(f"{msg} at {pos} (line {line}, col {col})")


def parse_with_peg(
    grammar_text: str,
    input_text: str,
    start_rule: Optional[str] = None,
    require_full: bool = True,
) -> ASTNode:
    """
    Compile PEG grammar (text) and parse input_text. Returns an ASTNode for
    the start rule.
    """
    gparser = GrammarParser(grammar_text)
    auto_start, rules = gparser.parse()
    if start_rule is None:
        start_rule = auto_start
    if start_rule not in rules:
        raise ValueError(f"Start rule '{start_rule}' not found in grammar.")
    parser = PEGParser(rules, start_rule, input_text)
    return parser.parse(require_full=require_full)


if __name__ == "__main__":
    # A small arithmetic grammar with whitespace, using standard PEG operators.
    grammar = r"""
        Expr    <- _ AddSub !.                 # require end of input via !.
        AddSub  <- MulDiv (('+' / '-') _ MulDiv)*
        MulDiv  <- Primary (('*' / '/') _ Primary)*
        Primary <- Number / '(' _ AddSub ')' _
        Number  <- [0-9]+ _

        _       <- [ \t\r\n]*                  # skip spaces
    """

    text = "12 + 3 * (4 + 5)"
    ast = parse_with_peg(grammar, text)
    # Pretty print:
    import json

    print(json.dumps(ast.to_dict(), indent=2))
    print(json.dumps(ast.to_dict(), indent=2))
    print(json.dumps(ast.to_dict(), indent=2))
