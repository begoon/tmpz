from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

KEYWORDS = {
    "program",
    "var",
    "begin",
    "end",
    "integer",
    "boolean",
    "real",
    "string",
    "procedure",
    "function",
    "if",
    "then",
    "else",
    "while",
    "do",
    "not",
    "div",
    "mod",
    "and",
    "or",
}

SYMBOLS = {
    "+",
    "-",
    "*",
    "/",
    "(",
    ")",
    "[",
    "]",
    ";",
    ",",
    ".",
    ":",
    ":=",
    "=",
    "<>",
    "<",
    "<=",
    ">",
    ">=",
}


@dataclass
class Token:
    type: str
    value: str
    line: int
    col: int


class LexerError(Exception):
    pass


class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.i = 0
        self.line = 1
        self.col = 1
        self.n = len(text)

    def peek(self, k=1) -> str:
        j = self.i + k
        return self.text[j] if j < self.n else ""

    def current(self) -> str:
        return self.text[self.i] if self.i < self.n else ""

    def advance(self, k=1):
        for _ in range(k):
            if self.i < self.n:
                ch = self.text[self.i]
                self.i += 1
                if ch == "\n":
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1

    def skip_whitespace_and_comments(self):
        while True:
            # whitespace
            while self.current() and self.current().isspace():
                self.advance()

            # comments { ... }
            if self.current() == "{":
                self.advance()
                while self.current() and self.current() != "}":
                    self.advance()
                if self.current() != "}":
                    raise LexerError(
                        f"unterminated {{ }} comment at line {self.line}"
                    )
                self.advance()
                continue

            # comments (* ... *)
            if self.current() == "(" and self.peek() == "*":
                self.advance(2)
                while self.i < self.n and not (
                    self.current() == "*" and self.peek() == ")"
                ):
                    self.advance()
                if self.i >= self.n:
                    raise LexerError(
                        f"unterminated (* *) comment at line {self.line}"
                    )
                self.advance(2)
                continue

            # comments //...
            if self.current() == "/" and self.peek() == "/":
                while self.current() and self.current() != "\n":
                    self.advance()
                continue
            break

    def number(self) -> Token:
        start_line, start_col = self.line, self.col
        s = ""
        while self.current().isdigit():
            s += self.current()
            self.advance()

        # Optional fractional part:
        # classic Pascal has reals, we will accept 123.45.
        if self.current() == "." and self.peek().isdigit():
            s += "."
            self.advance()
            while self.current().isdigit():
                s += self.current()
                self.advance()
            return Token("REAL", s, start_line, start_col)
        return Token("INTEGER", s, start_line, start_col)

    def ident_or_keyword(self) -> Token:
        line, col = self.line, self.col
        s = ""
        ch = self.current()
        if ch.isalpha() or ch == "_":
            s += ch
            self.advance()
            while self.current().isalnum() or self.current() == "_":
                s += self.current()
                self.advance()
        val = s.lower()
        if val in KEYWORDS:
            return Token(val.upper(), val, line, col)
        return Token("IDENT", s, line, col)

    def string(self) -> Token:
        start_line, start_col = self.line, self.col
        quote = self.current()
        self.advance()
        s = ""
        while True:
            c = self.current()
            if not c:
                raise LexerError(f"unterminated string at line {start_line}")
            if c == quote:
                self.advance()
                # Pascal doubles quotes for escape: 'it''s'
                if self.current() == quote:
                    s += quote
                    self.advance()
                    continue
                break
            s += c
            self.advance()
        return Token("STRING", s, start_line, start_col)

    def symbol(self) -> Token:
        start, col = self.line, self.col
        # Try 2-char symbols first
        two = self.current() + self.peek()
        if two in SYMBOLS:
            self.advance(2)
            return Token(two, two, start, col)
        one = self.current()
        if one in SYMBOLS:
            self.advance()
            return Token(one, one, start, col)
        raise LexerError(f"unknown symbol '{one}' at {start}:{col}")

    def tokens(self) -> List[Token]:
        out: List[Token] = []
        while True:
            self.skip_whitespace_and_comments()
            if self.i >= self.n:
                break
            ch = self.current()
            if ch.isdigit():
                out.append(self.number())
            elif ch.isalpha() or ch == "_":
                out.append(self.ident_or_keyword())
            elif ch in "'\"":
                out.append(self.string())
            else:
                out.append(self.symbol())
        out.append(Token("EOF", "", self.line, self.col))
        return out


@dataclass
class Program:
    name: str
    block: "Block"


@dataclass
class Block:
    variable_declarations: List["VariableDeclaration"]
    subprograms: List["ProcedureDeclaration"]
    compound: "Compound"


@dataclass
class VariableDeclaration:
    names: List[str]
    type_name: str


@dataclass
class ProcedureDeclaration:
    name: str
    params: List[Tuple[str, str]]
    block: Block


@dataclass
class Compound:
    statements: List["Statement"]


class Statement:
    pass


@dataclass
class Assign(Statement):
    name: str
    expr: "Expr"


@dataclass
class If(Statement):
    cond: "Expr"
    then_branch: Statement
    else_branch: Optional[Statement]


@dataclass
class While(Statement):
    cond: "Expr"
    body: Statement


@dataclass
class Call(Statement):
    name: str
    args: List["Expr"]


@dataclass
class BlockStatement(Statement):
    compound: Compound  # for begin..end blocks


@dataclass
class Empty(Statement):
    pass


class Expr:
    pass


@dataclass
class BinaryOperation(Expr):
    operation: str
    left: Expr
    right: Expr


@dataclass
class UnaryOperation(Expr):
    operation: str
    expr: Expr


@dataclass
class Variable(Expr):
    name: str


@dataclass
class IntegerLiteral(Expr):
    value: int


@dataclass
class RealLiteral(Expr):
    value: float


@dataclass
class StringLiteral(Expr):
    value: str


@dataclass
class BoolLiteral(Expr):
    value: bool


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def current(self) -> Token:
        return self.tokens[self.i]

    def eat(self, kind: Union[str, Tuple[str, ...]]) -> Token:
        tok = self.current()
        kinds = (kind,) if isinstance(kind, str) else kind
        if tok.type in kinds or tok.value in kinds:
            self.i += 1
            return tok
        expected = "/".join(kinds)
        raise ParseError(
            f"expected {expected}, found {tok.type}('{tok.value}') "
            f"at {tok.line}:{tok.col}"
        )

    def accept(self, kind: Union[str, Tuple[str, ...]]) -> Optional[Token]:
        token = self.current()
        kinds = (kind,) if isinstance(kind, str) else kind
        if token.type in kinds or token.value in kinds:
            self.i += 1
            return token
        return None

    # program -> 'program' IDENT ';' block '.'
    def program(self) -> Program:
        self.eat("PROGRAM")
        name = self.eat("IDENT").value
        self.eat(";")
        blk = self.block()
        self.eat(".")
        self.eat("EOF")
        return Program(name, blk)

    # block -> var_section subprogram_declarations compound_statement
    def block(self) -> Block:
        var_decls = self.var_section()
        subs = self.subprogram_declarations()
        comp = self.compound_statement()
        return Block(var_decls, subs, comp)

    # var_section -> ('var' var_decl+)?
    # var_decl -> ident_list ':' type ';'
    def var_section(self) -> List[VariableDeclaration]:
        out: List[VariableDeclaration] = []
        if self.accept("VAR"):
            while True:
                if self.current().type != "IDENT":
                    break
                names = [self.eat("IDENT").value]
                while self.accept(","):
                    names.append(self.eat("IDENT").value)
                self.eat(":")
                type_name = self.type_spec()
                self.eat(";")
                out.append(VariableDeclaration(names, type_name))
        return out

    def type_spec(self) -> str:
        tok = self.current()
        if tok.type in ("INTEGER", "BOOLEAN", "REAL", "STRING"):
            self.i += 1
            return tok.value
        # allow IDENT types (simple aliases)
        return self.eat("IDENT").value

    # subprogram_declarations -> (procedure_decl ';')*
    def subprogram_declarations(self) -> List[ProcedureDeclaration]:
        out: List[ProcedureDeclaration] = []
        while self.accept("PROCEDURE"):
            name = self.eat("IDENT").value
            params: List[Tuple[str, str]] = []
            if self.accept("("):
                if self.current().type != ")":
                    params = self.param_list()
                self.eat(")")
            self.eat(";")
            block = self.block()
            out.append(ProcedureDeclaration(name, params, block))
            self.eat(";")
        return out

    # param_list -> param_group (';' param_group)*
    # param_group -> ident_list ':' type
    def param_list(self) -> List[Tuple[str, str]]:
        out: List[Tuple[str, str]] = []
        while True:
            names = [self.eat("IDENT").value]
            while self.accept(","):
                names.append(self.eat("IDENT").value)
            self.eat(":")
            t = self.type_spec()
            for n in names:
                out.append((n, t))
            if not self.accept(";"):
                break
        return out

    # compound_statement -> 'begin' statement_list 'end'
    def compound_statement(self) -> Compound:
        self.eat("BEGIN")
        stmts = self.statement_list()
        self.eat("END")
        return Compound(stmts)

    # statement_list -> (statement (';' statement)*)?
    def statement_list(self) -> List[Statement]:
        statements: List[Statement] = []
        if self.current().type in ("IDENT", "BEGIN", "IF", "WHILE"):
            statements.append(self.statement())
            while self.accept(";"):
                # allow trailing semicolons by permitting empty statements
                if self.current().type in ("END", ".", "ELSE"):
                    break
                statements.append(self.statement())
        return statements

    # statement ->
    # assignment | procedure_statement | if | while | compound | empty
    def statement(self) -> Statement:
        token = self.current()
        if token.type == "BEGIN":
            return BlockStatement(self.compound_statement())
        if token.type == "IF":
            return self.if_statement()
        if token.type == "WHILE":
            return self.while_statement()
        if token.type == "IDENT":
            # lookahead for assignment vs call
            if self.tokens[self.i + 1].type == ":=":
                return self.assignment_statement()
            else:
                return self.procedure_statement()
        return Empty()

    def assignment_statement(self) -> Assign:
        name = self.eat("IDENT").value
        self.eat(":=")
        expr = self.expression()
        return Assign(name, expr)

    def procedure_statement(self) -> Call:
        name = self.eat("IDENT").value
        args: List[Expr] = []
        if self.accept("("):
            if self.current().type != ")":
                args = self.arg_list()
            self.eat(")")
        return Call(name, args)

    def arg_list(self) -> List[Expr]:
        args = [self.expression()]
        while self.accept(","):
            args.append(self.expression())
        return args

    def if_statement(self) -> If:
        self.eat("IF")
        cond = self.expression()
        self.eat("THEN")
        then_branch = self.statement()
        else_branch = None
        if self.accept("ELSE"):
            else_branch = self.statement()
        return If(cond, then_branch, else_branch)

    def while_statement(self) -> While:
        self.eat("WHILE")
        cond = self.expression()
        self.eat("DO")
        body = self.statement()
        return While(cond, body)

    # Expression grammar (precedence & associativity)
    # expression -> simple_expression (relop simple_expression)?
    def expression(self) -> Expr:
        left = self.simple_expression()
        token = self.current()
        if token.type in ("=", "<>", "<", "<=", ">", ">="):
            operation = token.type
            self.i += 1
            right = self.simple_expression()
            return BinaryOperation(operation, left, right)
        return left

    # simple_expression -> term (addop term)*
    # addop -> '+' | '-' | 'or'
    def simple_expression(self) -> Expr:
        node = self.term()
        while self.current().type in ("+", "-", "OR"):
            operation = self.current().type
            self.i += 1
            right = self.term()
            node = BinaryOperation(operation, node, right)
        return node

    # term -> factor (mulop factor)*
    # mulop -> '*' | '/' | 'div' | 'mod' | 'and'
    def term(self) -> Expr:
        node = self.factor()
        while self.current().type in ("*", "/", "DIV", "MOD", "AND"):
            op = self.current().type
            self.i += 1
            right = self.factor()
            node = BinaryOperation(op, node, right)
        return node

    # factor -> IDENT | number | string | 'not' factor | '(' expression ')'
    # | 'true' | 'false'
    def factor(self) -> Expr:
        token = self.current()
        if token.type == "IDENT":
            self.i += 1
            return Variable(token.value)
        if token.type == "INTEGER":
            self.i += 1
            return IntegerLiteral(int(token.value))
        if token.type == "REAL":
            self.i += 1
            return RealLiteral(float(token.value))
        if token.type == "STRING":
            self.i += 1
            return StringLiteral(token.value)
        if token.type == "NOT":
            self.i += 1
            return UnaryOperation("NOT", self.factor())
        if token.type == "+":
            self.i += 1
            return UnaryOperation("+", self.factor())
        if token.type == "-":
            self.i += 1
            return UnaryOperation("-", self.factor())
        if token.type == "(":
            self.i += 1
            e = self.expression()
            self.eat(")")
            return e
        if token.type in (
            "TRUE",
            "FALSE",
        ):
            # not lexed; handle via IDENT? We'll allow keywords via bool-like
            # identifiers
            self.i += 1
            return BoolLiteral(token.type == "TRUE")
        # Allow classic Pascal booleans as identifiers 'true'/'false'
        if token.type == "IDENT" and token.value.lower() in ("true", "false"):
            self.i += 1
            return BoolLiteral(token.value.lower() == "true")
        raise ParseError(
            f"unexpected token {token.type}('{token.value}') at "
            f"{token.line}:{token.col} in factor"
        )


def indent(s: str, n: int) -> str:
    pad = "  " * n
    return "\n".join(pad + line for line in s.splitlines())


def dump(node, level=0) -> str:
    if isinstance(node, Program):
        return indent(
            f"Program {node.name}\n{dump(node.block, level+1)}",
            level,
        )
    if isinstance(node, Block):
        parts = ["Block:"]
        if node.variable_declarations:
            parts.append("Variables:")
            for v in node.variable_declarations:
                parts.append(f"  {', '.join(v.names)}: {v.type_name}")
        if node.subprograms:
            parts.append("Procedures:")
            for p in node.subprograms:
                params = ", ".join(f"{n}:{t}" for n, t in p.params)
                parts.append(
                    indent(
                        f"procedure {p.name}({params})\n"
                        f"{dump(p.block, level)}",
                        1,
                    )
                )
        parts.append("Body:")
        parts.append(indent(dump(node.compound, level + 1), 1))
        return indent("\n".join(parts), level)
    if isinstance(node, Compound):
        return (
            "Compound:\n"
            + "\n".join(indent(dump(s, level + 1), 1) for s in node.statements)
            if node.statements
            else "Compound: (empty)"
        )
    if isinstance(node, BlockStatement):
        return "BlockStatementt:\n" + indent(dump(node.compound, level + 1), 1)
    if isinstance(node, Assign):
        return f"Assign {node.name} := {dump(node.expr, level+1)}"
    if isinstance(node, If):
        s = f"If {dump(node.cond)} then {dump(node.then_branch)}"
        if node.else_branch:
            s += f" else {dump(node.else_branch)}"
        return s
    if isinstance(node, While):
        return f"While {dump(node.cond)} do {dump(node.body)}"
    if isinstance(node, Call):
        return f"Call {node.name}({', '.join(dump(a) for a in node.args)})"
    if isinstance(node, Empty):
        return "Empty"
    if isinstance(node, BinaryOperation):
        return f"({dump(node.left)} {node.operation} {dump(node.right)})"
    if isinstance(node, UnaryOperation):
        return f"({node.operation}{dump(node.expr)})"
    if isinstance(node, Variable):
        return node.name
    if isinstance(node, IntegerLiteral):
        return str(node.value)
    if isinstance(node, RealLiteral):
        return str(node.value)
    if isinstance(node, StringLiteral):
        return repr(node.value)
    if isinstance(node, BoolLiteral):
        return "true" if node.value else "false"
    return repr(node)


def parse_pascal(code: str) -> Program:
    lexer = Lexer(code)
    tokens = lexer.tokens()
    return Parser(tokens).program()


if __name__ == "__main__":
    code = r"""
    program demo;
    var
      x, y: integer;
      msg: string;
    procedure incx(a: integer);
    begin
      x := x + a;
    end;

    begin
      x := 1;
      y := 2 * (x + 3) div 2;
      if y >= 4 then
        begin
          msg := 'hi';
          incx(y);
        end
      else
        while x < 10 do x := x + 1;
    end.
    """
    ast = parse_pascal(code)
    print(dump(ast))
