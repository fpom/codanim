from inspect import Signature, Parameter

from . import CAni, autorepr
from .highlight import pygmentize

class _CODE (CAni) :
    _fields = []
    _options = []
    @autorepr
    def __init__ (self, *l, **k) :
        params = []
        for i, name in enumerate(self._fields) :
            if name[0] == "*" :
                self._fields = self._fields[:]
                self._fields[i] = name[1:]
                params.append(Parameter(name[1:], Parameter.VAR_POSITIONAL))
            else :
                params.append(Parameter(name, Parameter.POSITIONAL_OR_KEYWORD))
        for name in self._options :
            params.append(Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, default=None))
        params.append(Parameter("src", Parameter.KEYWORD_ONLY, default=None))
        sig = Signature(params)
        args = self._args = sig.bind(*l, **k)
        args.apply_defaults()
        for key, val in args.arguments.items() :
            setattr(self, key, val)
        self._at = set()
    def __str__ (self) :
        content = []
        for key, val in self.items() :
            if isinstance(val, _CODE) :
                content.append((key, str(val)))
            else :
                content.append((key, repr(val)))
        return "%s(%s)" % (self.__class__.__name__,
                           ", ".join("%s=%r" % item for item in content))
    def items (self) :
        for field in self._fields :
            yield field, getattr(self, field)
        for field in self._options :
            member = getattr(self, field, None)
            if member is not None :
                yield field, member
    def source (self) :
        sub = {}
        for key, val in self.items() :
            if isinstance(val, _CODE) :
                sub[key] = val.source()
            else :
                sub[key] = val
        return self.src.format(**sub)
    def tex (self) :
        sub = self.src.format(**{key : "$" for key, val in self.items()}).split("$")
        parts = [pygmentize(sub[0])]
        for (key, val), txt in zip(self.items(), sub[1:]) :
            if isinstance(val, _CODE) :
                parts.append(val.tex())
            else :
                parts.append(pygmentize(str(val)))
            parts.append(pygmentize(txt))
        tex = "".join(parts)
        if self._at :
            return r"\onlyhl{%s}{" % ",".join(str(i) for i in self._at) + tex + "}"
        else :
            return tex

class BLOCK (_CODE) :
    _fields = ["*body"]
    def __call__ (self) :
        self._at.add(self.IP)
        for code in self.body :
            code()
    def source (self) :
        return "".join(b.source() for b in self.body)
    def tex (self) :
        return "".join(b.tex() for b in self.body)

class STMT (_CODE) :
    _fields = ["*steps"]
    def __call__ (self) :
        for s in self.steps :
            self._at.add(self.IP)
            self.exec(s)
            self.IP += 1

class EXPR (_CODE) :
    _fields = ["expr"]
    @autorepr
    def __init__ (self, *l, **k) :
        super().__init__(*l, **k)
        if self.src is None :
            self.src = self.expr
    def __call__ (self) :
        self._at.add(self.IP)
        self.eval(self.expr)
        self.IP += 1

class PY (_CODE) :
    _fields = ["py"]
    def __call__ (self) :
        self.exec(self.py)
    def tex (self) :
        return ""
    def source (self) :
        return ""

class ENV (_CODE) :
    _fields = ["name", "value"]
    def __call__ (self) :
        self._env[self.name] = self.value
    def tex (self) :
        return ""
    def source (self) :
        return ""

class WS (_CODE) :
    _fields = []
    @autorepr
    def __init__ (self, src) :
        super().__init__(src=src)
    def __call__ (self) :
        pass
    def tex (self) :
        return self.src

class RAW (_CODE) :
    _fields = []
    @autorepr
    def __init__ (self, src) :
        super().__init__(src=src)
    def __call__ (self) :
        pass

class XDECL (_CODE) :
    _fields = ["*names"]
    def __call__ (self) :
        for name in self.names :
            self._env[name] = None
        self._at.add(self.IP)
        self.IP += 1

class DECL (_CODE) :
    _fields = ["name"]
    _options = ["init", "animate"]
    def __call__ (self) :
        if self.init is not None :
            self.init()
            self._env[self.name] = self.RET
        else :
            self._env[self.name] = None
        self._at.add(self.IP)
        self.IP += 1
    def tex (self) :
        src = super().tex()
        if self.animate is None :
            return src
        else :
            return src + "  " + "".join(self._tex())
    def _tex (self) :
        tail = r"\PY{{c+c1}}{{/* {value} */}}"
        for value, start, stop in self._env.get(self.name)._h :
            if value is not None :
                yield (r"\onlyshow{{{start}-{stop}}}{{{value}}}"
                       r"").format(start=start or 1,
                                   stop=stop or "",
                                   value=tail.format(value=value))

class BreakLoop (Exception) :
    pass

class BREAK (_CODE) :
    def __call__ (self) :
        self._at.add(self.IP)
        self.IP += 1
        raise BreakLoop()

class FunctionReturn (Exception) :
    def __init__ (self, RET) :
        super().__init__()
        self.RET = RET

class RETURN (_CODE) :
    _options = ["value"]
    def __call__ (self) :
        if self.value is not None :
            self.value()
        self._at.add(self.IP)
        self.IP += 1
        raise FunctionReturn(self.RET)

class IF (_CODE) :
    _fields = ["cond", "then"]
    _options = ["otherwise"]
    def __call__ (self) :
        self.cond()
        if self.RET :
            self.then()
        elif self.otherwise is not None :
            self.otherwise()

class WHILE (_CODE) :
    _fields = ["cond", "body"]
    def __call__ (self) :
        try :
            while True :
                self.cond()
                if not self.RET :
                    break
                self.body()
        except BreakLoop :
            return

class DO (_CODE) :
    _fields = ["body", "cond"]
    def __call__ (self) :
        try :
            while True :
                self.body()
                self.cond()
                if not self.RET :
                    break
        except BreakLoop :
            pass

class FOR (_CODE) :
    _fields = ["init", "cond", "step", "body"]
    def __call__ (self) :
        self.init()
        try :
            while True :
                self.cond()
                if not self.RET :
                    break
                self.body()
                self.step()
        except BreakLoop :
            pass

class FUNC (_CODE) :
    _fields = ["body"]
    def __call__ (self) :
        try :
            self.body()
        except FunctionReturn as exc :
            self._env["RET"] = exc.RET
