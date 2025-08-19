import pathlib
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

KEYWORDS = {
    "PROGRAM",
    "END",
    "FUNCTION",
    "RETURN",
    "INTEGER",
    "REAL",
    "IF",
    "THEN",
    "ELSE",
    "FI",
    "WHILE",
    "FOR",
    "BY",
    "DO",
    "SELECT",
    "CASE",
    "DECLARE",
    "SET",
    "OUTPUT",
    "INPUT",
    "EXIT",
    "FIX",
    "FLOAT",
    "TRUE",
    "FALSE",
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
    "||",
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
        line, col = self.line, self.col
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
            return Token("REAL", s, line, col)
        return Token("INTEGER", s, line, col)

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
        line, col = self.line, self.col
        quote = self.current()
        self.advance()
        s = ""
        while True:
            c = self.current()
            if not c:
                raise LexerError(f"unterminated string at line {line}")
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
        return Token("STRING", s, line, col)

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
    block: "Segments"


@dataclass
class Segments:
    variables: List["VariableDeclaration"]
    procedures: List["ProcedureDeclaration"]
    statements: "Statements"


@dataclass
class VariableDeclaration:
    names: List[str]
    type: str


@dataclass
class ProcedureDeclaration:
    name: str
    parameters: List[Tuple[str, str]]
    block: Segments


@dataclass
class Statements:
    statements: List["Statement"]


class Statement:
    pass


@dataclass
class Assign(Statement):
    name: str
    expression: "Expression"


@dataclass
class If(Statement):
    cond: "Expression"
    then_branch: Statement
    else_branch: Optional[Statement]


@dataclass
class While(Statement):
    cond: "Expression"
    body: Statement


@dataclass
class Call(Statement):
    name: str
    args: List["Expression"]


@dataclass
class BlockStatement(Statement):
    compound: Statements  # for begin..end blocks


@dataclass
class Empty(Statement):
    pass


class Expression:
    pass


@dataclass
class BinaryOperation(Expression):
    operation: str
    left: Expression
    right: Expression


@dataclass
class UnaryOperation(Expression):
    operation: str
    expr: Expression


@dataclass
class Variable(Expression):
    name: str


@dataclass
class IntegerLiteral(Expression):
    value: int


@dataclass
class RealLiteral(Expression):
    value: float


@dataclass
class StringLiteral(Expression):
    value: str


@dataclass
class BoolLiteral(Expression):
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
        token = self.current()
        kinds = (kind,) if isinstance(kind, str) else kind
        if token.type in kinds or token.value in kinds:
            self.i += 1
            return token
        expected = "/".join(kinds)
        raise ParseError(
            f"expected {expected}, found {token.type}('{token.value}') "
            f"at {token.line}:{token.col}"
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
        self.eat(":")
        block = self.segments()
        self.eat(".")
        self.eat("EOF")
        return Program(name, block)

    # segments -> variables_declarations procedures_declarations compound_statement
    def segments(self) -> Segments:
        variables_declarations = self.variables_section()
        procedures_declarations = self.procedures_declarations()
        instructions = self.instructions()
        return Segments(
            variables_declarations,
            procedures_declarations,
            instructions,
        )

    # variables_section -> ('var' variable_declaration+)?
    # variable_declaration -> ident_list ':' type ';'
    def variables_section(self) -> List[VariableDeclaration]:
        out: List[VariableDeclaration] = []
        if self.accept("VAR"):
            while True:
                if self.current().type != "IDENT":
                    break
                names = [self.eat("IDENT").value]
                while self.accept(","):
                    names.append(self.eat("IDENT").value)
                self.eat(":")
                type_name = self.type_name()
                self.eat(";")
                out.append(VariableDeclaration(names, type_name))
        return out

    def type_name(self) -> str:
        token = self.current()
        if token.type in ("INTEGER", "BOOLEAN", "REAL", "STRING"):
            self.i += 1
            return token.value
        # allow IDENT types (simple aliases)
        return self.eat("IDENT").value

    # procedures_declarations -> (procedure_declaration ';')*
    def procedures_declarations(self) -> List[ProcedureDeclaration]:
        out: List[ProcedureDeclaration] = []
        while self.accept("PROCEDURE"):
            name = self.eat("IDENT").value
            parameters_list: List[Tuple[str, str]] = []
            if self.accept("("):
                if self.current().type != ")":
                    parameters_list = self.parameters_list()
                self.eat(")")
            self.eat(";")
            block = self.segments()
            out.append(ProcedureDeclaration(name, parameters_list, block))
            self.eat(";")
        return out

    # parameters_list -> parameters_group (';' parameters_group)*
    # parameters_group -> ident_list ':' type
    def parameters_list(self) -> List[Tuple[str, str]]:
        out: List[Tuple[str, str]] = []
        while True:
            names = [self.eat("IDENT").value]
            while self.accept(","):
                names.append(self.eat("IDENT").value)
            self.eat(":")
            type_name = self.type_name()
            for name in names:
                out.append((name, type_name))
            if not self.accept(";"):
                break
        return out

    # compound_statement -> 'begin' statement_list 'end'
    def instructions(self) -> Statements:
        self.eat("BEGIN")
        statement_list = self.statement_list()
        self.eat("END")
        return Statements(statement_list)

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
            return BlockStatement(self.instructions())
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
        args: List[Expression] = []
        if self.accept("("):
            if self.current().type != ")":
                args = self.arg_list()
            self.eat(")")
        return Call(name, args)

    def arg_list(self) -> List[Expression]:
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
    def expression(self) -> Expression:
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
    def simple_expression(self) -> Expression:
        node = self.term()
        while self.current().type in ("+", "-", "OR"):
            operation = self.current().type
            self.i += 1
            right = self.term()
            node = BinaryOperation(operation, node, right)
        return node

    # term -> factor (mulop factor)*
    # mulop -> '*' | '/' | 'div' | 'mod' | 'and'
    def term(self) -> Expression:
        node = self.factor()
        while self.current().type in ("*", "/", "DIV", "MOD", "AND"):
            operation = self.current().type
            self.i += 1
            right = self.factor()
            node = BinaryOperation(operation, node, right)
        return node

    # factor -> IDENT | number | string | 'not' factor | '(' expression ')'
    # | 'true' | 'false'
    def factor(self) -> Expression:
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
    if isinstance(node, Segments):
        parts = ["Block:"]
        if node.variables:
            parts.append("Variables:")
            for v in node.variables:
                parts.append(f"  {', '.join(v.names)}: {v.type}")
        if node.procedures:
            parts.append("Procedures:")
            for p in node.procedures:
                params = ", ".join(f"{n}:{t}" for n, t in p.parameters)
                parts.append(
                    indent(
                        f"procedure {p.name}({params})\n"
                        f"{dump(p.block, level)}",
                        1,
                    )
                )
        parts.append("Body:")
        parts.append(indent(dump(node.statements, level + 1), 1))
        return indent("\n".join(parts), level)
    if isinstance(node, Statements):
        return (
            "Compound:\n"
            + "\n".join(indent(dump(s, level + 1), 1) for s in node.statements)
            if node.statements
            else "Compound: (empty)"
        )
    if isinstance(node, BlockStatement):
        return "BlockStatementt:\n" + indent(dump(node.compound, level + 1), 1)
    if isinstance(node, Assign):
        return f"Assign {node.name} := {dump(node.expression, level+1)}"
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


def parse_easy(code: str) -> Program:
    lexer = Lexer(code)
    tokens = lexer.tokens()
    return Parser(tokens).program()


def parse() -> Program:
    code = pathlib.Path("era.easy").read_text()
    ast = parse_easy(code)
    return ast


if __name__ == "__main__":
    print(dump(parse()))
