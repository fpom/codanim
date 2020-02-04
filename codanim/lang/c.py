import re, sys, itertools
import pycparser, colorama

from .. import flow

def escape (text) :
    return text.replace("{", "{{").replace("}", "}}")

class String (str):
    def __new__(cls, content):
        self = super().__new__(cls, content)
        self._n = {0: 0}
        for n, match in enumerate(re.finditer("\n", self)) :
            self._n[n+1] = match.end()
        return self
    def last (self) :
        l = len(self._n) - 1
        return Coord(l, len(self) - self._n[l] + 1)
    def __call__ (self, coord) :
        return self._n[coord.line-1] + coord.column-1
    def __getitem__ (self, idx) :
        if isinstance(idx, Span) :
            a = self(idx.start)
            b = self(idx.stop)
            return super().__getitem__(slice(a,b))
        elif isinstance(idx, Coord) :
            return super().__getitem__(self(idx))
        elif isinstance(idx, slice) :
            if isinstance(idx.start, Coord) :
                a = self(idx.start)
            else :
                a = idx.start
            if isinstance(idx.stop, Coord) :
                b = self(idx.stop)
            else :
                b = idx.stop
            return super().__getitem__(slice(a,b))
        else :
            return super().__getitem__(idx)
    def index (self, sub, start=None, end=None) :
        if isinstance(start, Coord) :
            start = self(start)
        if isinstance(end, Coord) :
            end = self(end)
        return super().index(sub, start, end) - (start or 0)
    def rindex (self, sub, start=None, end=None) :
        if isinstance(start, Coord) :
            start = self(start)
        if isinstance(end, Coord) :
            end = self(end)
        return super().rindex(sub, start, end) - (end or 0)
    def sub (self, within, pairs) :
        parts = []
        last = within.start
        for span, text in pairs :
            parts.append(escape(self[last:span.start]))
            parts.append(text)
            last = span.stop
        parts.append(escape(self[last:within.stop]))
        return "".join(parts)

class Coord (object) :
    def __init__ (self, l, c=None) :
        if c is None :
            self.line, self.column = l.line, l.column
        else :
            self.line, self.column = l or 1, c or 1
    def __eq__ (self, other) :
        return self.line == other.line and self.column == other.column
    def __lt__ (self, other) :
        return (self.line < other.line
                or (self.line == other.line and self.column < other.column))
    def __add__ (self, other) :
        return self.__class__(self.line, self.column + other)
    def __str__ (self) :
        return f"{self.line}:{self.column}"

class Span (object) :
    def __init__ (self, start, stop) :
        self.start = Coord(start)
        self.stop = Coord(stop)
    def add (self, other) :
        if isinstance(other, Span) :
            if other.start is not None and other.start < self.start :
                self.start = other.start
            if other.stop is not None and other.stop > self.stop :
                self.stop = other.stop
        elif isinstance(other, Coord) :
            if other < self.start :
                self.start = other
            elif other > self.stop :
                self.stop = other
        elif isinstance(other, int) :
            if other > 0 :
                self.stop += other
            elif other < 0 :
                self.start += other
        else :
            raise TypeError(repr(other))
    def __str__ (self) :
        return f"{self.start}/{self.stop}"

class SpanDict (dict) :
    def __init__ (self, ast, src) :
        super().__init__()
        self.src = String(src)
        self.do(ast)
    def do (self, node) :
        self.generic_do(node)
        name = node.__class__.__name__
        handler = getattr(self, "do_" + name, None)
        if handler is not None :
            handler(node)
    def generic_do (self, node) :
        coord = getattr(node, "coord", None)
        if coord is not None :
            span = self[node] = Span(Coord(coord), Coord(coord))
        else :
            span = self[node] = Span(Coord(sys.maxsize, sys.maxsize), Coord(1, 1))
        for _, child in node.children() :
            self.do(child)
            span.add(self[child])
    def do_ID (self, node) :
        self[node].add(len(node.name))
    def do_Constant (self, node) :
        self[node].add(len(node.value))
    def do_Break (self, node) :
        self[node].add(5)
    def do_Typedef (self, node) :
        if not self.src[self[node].start:self[node].stop].startswith("typedef") :
            self[node].start += self.src.rindex("typedef", 0, self[node].start)
    def do_TypeDecl (self, node) :
        self[node].add(len(node.declname))
    def do_Struct (self, node) :
        self[node].add(self.src.index("}", self[node].stop) + 1)
    def do_ArrayRef (self, node) :
        self[node].add(self.src.index("]", self[node].stop) + 1)
    def do_FuncCall (self, node) :
        self[node].add(self.src.index(")", self[node].stop) + 1)
    def do_FuncDecl (self, node) :
        self[node].add(self.src.index(")", self[node].stop) + 1)
    def do_FuncDef (self, node) :
        self[node.body].add(self.src.index("}", self[node.body].stop) + 1)
        self[node].add(self[node.body])
        self[node.body].start = self[node.decl].stop + 1
        while self.src[self[node.body].start] in " \t" :
            self[node.body].start += 1
    def do_UnaryOp (self, node) :
        if node.op in ("p++", "p--") :
            self[node].add(self.src.index(node.op[1:], self[node].stop)
                           + len(node.op[1:]))
    def do_DoWhile (self, node) :
        self[node].add(self.src.index(")", self[node].stop) + 1)
        self[node].start += self.src.index("do", self[node].start)
        self[node.stmt].start = self[node].start + 2
        while self.src[self[node.stmt].start] in " \t" :
            self[node.stmt].start += 1
        if self.src[self[node.stmt].start] == "{" :
            self[node.stmt].add(self.src.index("}", self[node.stmt].stop) + 1)
        self[node].add(self[node.stmt])
    def do_If (self, node) :
        self[node].start += self.src.index("if", self[node].start)
        self[node.iftrue].start = (self[node.cond].stop
                                   + self.src.index(")", self[node.cond].stop) + 1)
        while self.src[self[node.iftrue].start] in " \t" :
            self[node.iftrue].start += 1
        if self.src[self[node.iftrue].start] == "{" :
            self[node.iftrue].add(self.src.index("}", self[node.iftrue].stop) + 1)
        self[node].add(self[node.iftrue])
    def do_While (self, node) :
        self[node].start += self.src.index("while", self[node].start)
        self[node.stmt].start = (self[node.cond].stop
                                 + self.src.index(")", self[node.cond].stop) + 1)
        while self.src[self[node.stmt].start] in " \t" :
            self[node.stmt].start += 1
        if self.src[self[node.stmt].start] == "{" :
            self[node.stmt].add(self.src.index("}", self[node.stmt].stop) + 1)
        self[node].add(self[node.stmt])
    def do_BinaryOp (self, node) :
        if ")" in self.src[self[node.left].stop:self[node.right].start] :
            while self.src[self[node].start] != "(" :
                self[node].start += -1
    def do_FileAST (self, node) :
        self[node] = Span(Coord(1,1), self.src.last())
    def do_Switch (self, node) :
        self[node].start += self.src.index("switch", self[node].start)
        self[node.stmt].start = (self[node.cond].stop
                                 + self.src.index(")", self[node.cond].stop) + 1)
        while self.src[self[node.stmt].start] in " \t" :
            self[node.stmt].start += 1
        if self.src[self[node.stmt].start] == "{" :
            self[node.stmt].add(self.src.index("}", self[node.stmt].stop) + 1)
        self[node].add(self[node.stmt])

class SpanTree (object) :
    def __init__ (self, ast, span) :
        self.span = span[ast]
        self._ast = ast
        self._span = span
        for name in itertools.chain(getattr(ast, "attr_names", []),
                                    ast.__slots__) :
            attr = getattr(ast, name, None)
            if isinstance(attr, (list, tuple)) :
                setattr(self, name, type(attr)(self.__class__(v, span)
                                               if isinstance(v, pycparser.c_ast.Node)
                                               else v for v in attr))
        self.nodetype = ast.__class__.__name__
    def __repr__ (self) :
        return f"<ast.{self.nodetype} at {self.span}>"
    def __getattr__ (self, name) :
        ret = getattr(self._ast, name)
        if isinstance(ret, pycparser.c_ast.Node) :
            return self.__class__(ret, self._span)
        else :
            return ret
    def children (self) :
        for name, child in self._ast.children() :
            yield name, self.__class__(child, self._span)
    def dump (self, indent="  ", source=False) :
        print(f"{colorama.Style.BRIGHT}{self.nodetype}{colorama.Style.RESET_ALL} at"
              f" {colorama.Fore.YELLOW}{self.span}{colorama.Style.RESET_ALL}")
        for name in getattr(self, "attr_names", []) :
            attr = getattr(self, name, None)
            if not attr :
                continue
            attr_type = type(attr).__name__
            print(f"{indent}{colorama.Fore.BLUE}{name}{colorama.Style.RESET_ALL}"
                  f" = {attr!r}"
                  f" {colorama.Fore.WHITE}<{attr_type}>{colorama.Style.RESET_ALL}")
        if source :
            print(f"{indent}{colorama.Fore.GREEN}source{colorama.Style.RESET_ALL}"
                  f" = {self.source!r}")
        for name, child in self.children() :
            print(f"{indent}{colorama.Fore.RED}{name}:{colorama.Style.RESET_ALL} ",
                  end="")
            child.dump(indent + "  ", source)
    @property
    def source (self) :
        return self._span.src[self.span]
    def get_source (self, start, stop) :
        return escape(self._span.src[start:stop])
    def sub_source (self, *pairs) :
        return self._span.src.sub(self.span, zip(pairs[::2], pairs[1::2]))

_skip = ["/\\*(?ms:.*?)\\*/",
         "//.*",
         "#define .*",
         "#include .*"]
_skip_re = re.compile("|".join(f"({e})" for e in _skip), re.M)
_skip_clean = re.compile("[^\n]")

def parse (source, path="<str>") :
    _src = []
    _cpp = []
    pos = 0
    for match in _skip_re.finditer(source) :
        _src.append(source[pos:match.start()])
        _cpp.append(match[0])
        pos = match.end()
    cppsrc = "".join(s + _skip_clean.sub(" ", c)
                     for s, c in zip(_src, _cpp)) + source[pos:]
    parser = pycparser.CParser()
    ast = parser.parse(cppsrc, path)
    return SpanTree(ast, SpanDict(ast, source))

class Translator (object) :
    def __init__ (self) :
        self.typedef = {}
        self.funcdef = {}
    def __call__ (self, node) :
        handler = getattr(self, "do_" + node.nodetype, self.generic_do)
        return handler(node)
    def generic_do (self, node) :
        block = flow.BLOCK()
        last = node.span.start
        for _, child in node.children() :
            if child.span.start > last :
                block.append(flow.RAW(node.get_source(last, child.span.start)))
            block.append(self(child))
            last = child.span.stop
        if last < node.span.stop :
            block.append(flow.RAW(node.get_source(last, node.span.stop)))
        return block
    def do_Typedef (self, node) :
        self.typedef[node.name] = node
        return flow.RAW(node.source)
    def do_FuncDef (self, node) :
        self.funcdef[node.decl.name] = node
        return flow.FUNC(self(node.body),
                         src=node.sub_source(node.body.span, "{body}"))
    def do_Assignment (self, node) :
        src = node.source
        return flow.STMT(f"FIXME {src}", src=src)
    def do_FuncCall (self, node) :
        src = node.source
        return flow.STMT(f"FIXME {src}", src=src)
    def do_Decl (self, node) :
        src = node.source
        if node.init :
            return flow.DECL(node.name,
                             flow.EXPR(f"FIXME {src}", src=src),
                             animate=False,
                             src=node.sub_source(node.init.span, "{init}"))
        else :
            return flow.DECL(node.name, animate=False, src=src)
    def do_If (self, node) :
        cond = node.cond.source
        if node.iffalse is None :
            return flow.IF(flow.EXPR(f"FIXME {cond}", src=cond),
                           self(node.iftrue),
                           src=node.sub_source(node.iftrue.span, "{then}"))
        else :
            return flow.IF(flow.EXPR(f"FIXME {cond}", src=cond),
                           self(node.iftrue),
                           self(node.iffalse),
                           src=node.sub_source(node.iftrue.span, "{then}",
                                               node.iffalse.span, "{otherwise}"))
    def do_For (self, node) :
        init = node.init.source
        cond = node.cond.source
        step = node.next.source
        return flow.FOR(flow.STMT(f"FIXME {init}", src=init),
                        flow.EXPR(f"FIXME {cond}", src=cond),
                        flow.STMT(f"FIXME {step}", src=step),
                        self(node.stmt),
                        src=node.sub_source(node.init.span, "{init}",
                                            node.cond.span, "{cond}",
                                            node.next.span, "{step}",
                                            node.stmt.span, "{body}"))
    def do_While (self, node) :
        cond = node.cond.source
        return flow.WHILE(flow.EXPR(f"FIXME {cond}", src=cond),
                          self(node.stmt),
                          src=node.sub_source(node.cond.span, "{cond}",
                                              node.stmt.span, "{body}"))
    def do_DoWhile (self, node) :
        cond = node.cond.source
        return flow.DO(self(node.stmt),
                       flow.EXPR(f"FIXME {cond}", src=cond),
                       src=node.sub_source(node.stmt.span, "{body}",
                                           node.cond.span, "{cond}"))
    def do_Switch (self, node) :
        cond = node.cond.source
        block = flow.BLOCK()
        last = node.stmt.span.start
        for _, child in node.stmt.children() :
            if child.span.start > last :
                block.append(flow.RAW(node.get_source(last, child.span.start)))
            block.append(self(child))
            last = child.span.stop
        if last < node.span.stop :
            block.append(flow.RAW(node.get_source(last, node.span.stop)))
        return flow.SWITCH(flow.EXPR(f"FIXME {cond}", src=cond),
                           *block.body,
                           src=node.sub_source(node.cond.span, "{cond}",
                                               node.stmt.span, "{cases}"))
    def do_Case (self, node) :
        value = node.expr.source
        block = flow.BLOCK()
        last = None
        for child in node.stmts :
            if last is not None and child.span.start > last :
                block.append(flow.RAW(node.get_source(last, child.span.start)))
            block.append(self(child))
            last = child.span.stop
        if last < node.span.stop :
            block.append(flow.RAW(node.get_source(last, node.span.stop)))
        return flow.CASE(flow.EXPR(f"FIXME {value}", src=value),
                         block,
                         src=node.sub_source(node.expr.span, "{value}",
                                             Span(node.stmts[0].span.start,
                                                  node.stmts[-1].span.stop), "{body}"))
    def do_Default (self, node) :
        default = flow.DEFAULT(src=node.sub_source(Span(node.stmts[0].span.start,
                                                        node.stmts[-1].span.stop),
                                                   "{body}"))
        last = None
        for child in node.stmts :
            if last is not None and child.span.start > last :
                default.append(flow.RAW(node.get_source(last, child.span.start)))
            default.append(self(child))
            last = child.span.stop
        if last < node.span.stop :
            default.append(flow.RAW(node.get_source(last, node.span.stop)))
        return default
    def do_Break (self, node) :
        return flow.BREAK()
