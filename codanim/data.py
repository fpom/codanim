from itertools import chain
from inspect import cleandoc
from collections import defaultdict
from . import CAni, ExecEnv, autorepr

class dopt (dict) :
    def __str__ (self) :
        return ",".join("%s=%s" % (k, v) if v is not None else k
                        for (k, v) in self.items())

_opposite = {"north": "south",
             "east": "west",
             "south": "north",
             "west": "east"}

opp = _opposite.get

class TikZ (object) :
    _defaults = {"tikzpicture": {},
                 "pos": {},
                 "value": {"minimum size": "1cm",
                           "transform shape": None,
                           "draw": None,
                           "inner sep": "0pt",
                           "outer sep": "0pt"},
                 "valuescope": {},
                 "aggregatescope": {},
                 "arrayscope": {},
                 "structscope": {},
                 "heapscope": {},
                 "boxscope": {},
                 "valueread" : {"very thick": None,
                                "draw": "blue!50!black",
                                "fill": "blue!20"},
                 "valuewrite": {"very thick": None,
                                "draw": "red!50!black",
                                "fill": "red!20"},
                 "valuereadwrite": {"very thick": None,
                                    "draw": "purple!50!black",
                                    "fill": "purple!20"},
                 "pointer": {"thick": None,
                             "|-{Stealth[round]}": None},
                 "aggregate": {"grow": "east",
                               "ticks": "south"},
                 "heap": {"grow": "left",
                          "distance": "15mm"},
                 "group": {"opacity": 0,
                           "draw": "yellow",
                           "very thick": None,
                           "inner sep": "0pt",
                           "outer sep": "0pt"},
                 "alloc": {},
                 "index": {"scale": ".9"},
                 "ticks": {"gray": None,
                           "scale": ".7"}}
    def __init__ (self, options, **default) :
        self._keys = []
        for key, val in chain(self._defaults.items(), default.items(), options.items()) :
            self.__dict__.setdefault(key, dopt()).update(val)
            self._keys.append(key)
    def __add__ (self, options) :
        return self.__class__(options, **self.dict())
    def __truediv__ (self, key) :
        new = __class__(self)
        setattr(new, key, dopt())
        return new
    def items (self) :
        for key in self._keys :
            yield key, getattr(self, key)
    def dict (self) :
        return dict(self.items())

class CAniTikZ (CAni) :
    _nodeid = defaultdict(int)
    _defaults = {}
    def __init__ (self, tikz) :
        self.nodeid = tikz.pop("nodeid", None)
        if self.nodeid is None :
            char = self.__class__.__name__[0].lower()
            num = self._nodeid[char]
            self.nodeid = f"{char}{num}"
            self._nodeid[char] = num + 1
        self._o = TikZ(tikz, **self._defaults)
    def __matmul__ (self, key) :
        if key == None :
            return self
        else :
            raise ValueError("invalid index %r for %s object"
                             % (key, self.__class__.__name__))
    def ptr (self) :
        return Pointer(self)
    def tex (self, head=None, tail=None, **tikz) :
        opt = TikZ(tikz)
        return cleandoc(r"""\begin{{tikzpicture}}[{opt.tikzpicture}]
          {head}{code}{tail}
        \end{{tikzpicture}}
        """).format(opt=opt,
                    head=(head.strip("\n") + "\n") if head else "",
                    tail=("\n" + tail.strip("\n")) if tail else "",
                    code="\n  ".join(self.tikz(**tikz).splitlines()))

class Pointer (CAniTikZ) :
    @autorepr
    def __init__ (self, data) :
        self.__dict__.update(_d=data, nodeid=None)
    def val (self) :
        return self._d
    def __tikz__ (self, src, opt) :
        if self._d is None :
            return ""
        else :
            tgt = (self._d@None).nodeid
            return fr"\draw[{opt.pointer}] ({src}) -- ({tgt});"
    def __getitem__ (self, key) :
        return self._d[key]
    def __setitem__ (self, key, val) :
        self._d[key] = val
    def __getattr__ (self, key) :
        return getattr(self._d, key)
    def __setattr__ (self, key, val) :
        setattr(self._d, key, val)

class Value (CAniTikZ) :
    @autorepr
    def __init__ (self, init=None, **tikz) :
        super().__init__(tikz)
        self._h = [[init, self.IP, None]]
        self._r = set()
        self._w = set()
    def get (self) :
        self._r.add(self.IP)
        return self._h[-1][0]
    def set (self, val) :
        self._w.add(self.IP)
        if self._h[-1][0] == val :
            pass
        elif self.IP == self._h[-1][1] :
            self._h[-1][0] = val
        else :
            self._h[-1][2] = self.IP - 1
            self._h.append([val, self.IP, None])
    def stop (self) :
        if self.IP == self._h[-1][1] :
            self._h[-1][2] = self.IP
        else :
            self._h[-1][2] = self.IP - 1
    def tikz (self, **tikz) :
        tpl = r"""%% {classname} {nodeid}
        \begin{{scope}}[{opt.valuescope}]
          {node}
          {highlight}
          {states}
        \end{{scope}}
        %% /{classname} {nodeid}
        """
        opt = TikZ(tikz) + self._o
        self.stop()
        return cleandoc(tpl).format(classname=self.__class__.__name__,
                                    opt=opt,
                                    node=(self._node(opt)
                                          or "% skipped node"),
                                    nodeid=self.nodeid,
                                    highlight=("\n  ".join(self._highlight(opt))
                                               or "% skipped reads/writes"),
                                    states=("\n  ".join(self._states(opt))
                                            or "%s skipped states"))
    def _highlight (self, opt) :
        nodeid = self.nodeid
        for cat, steps in zip([opt.valueread, opt.valuewrite, opt.valuereadwrite],
                              [self._r-self._w, self._w-self._r, self._w&self._r]) :
            if steps :
                when = ",".join(str(s) for s in sorted(steps))
                yield cleandoc(fr"""\only<{when}>{{
                  \draw[{cat}] ({nodeid}.south west) rectangle ({nodeid}.north east);
                }}
                """)
    def _node (self, opt) :
        return fr"\node[{opt.value},{opt.pos}] ({self.nodeid}) {{}};"
    def _states (self, opt) :
        for value, start, stop in self._h :
            if value is not None :
                yield (r"\only<{start}-{stop}>{{ {state} }}"
                       r"").format(start=start or 1,
                                   stop=stop or "",
                                   state=self._state(value, opt))
    def _state (self, value, opt) :
        try :
            return value.__tikz__(f"{self.nodeid}.center", opt)
        except :
            return f"\node at ({self.nodeid}) {{{value}\strut}};"

ExecEnv._ValueClass = Value

class Aggregate (CAniTikZ) :
    @autorepr
    def __init__ (self, init, **tikz) :
        super().__init__(tikz)
        if isinstance(init, int) :
            self._d = {k: Value(None, nodeid=f"{self.nodeid}/{k}", **tikz)
                       for k in range(init)}
        elif isinstance(init, list) :
            self._d = {}
            for k, v in enumerate(init) :
                if isinstance(v, Value) :
                    self._d[k] = v
                else :
                    self._d[k] = Value(v, nodeid=f"{self.nodeid}/{k}", **tikz)
        elif isinstance(init, dict) :
            self._d = {}
            for k, v in init.items() :
                if isinstance(v, Value) :
                    self._d[k] = v
                else :
                    self._d[k] = Value(v, nodeid=f"{self.nodeid}/{k}", **tikz)
        items = list(self._d.values())
        self._first = items[0]
        self._last = items[-1]
    def __matmul__ (self, key) :
        if key in self._d :
            return self._d[key]
        elif key == None :
            return self._first
        else :
            raise ValueError("invalid index %r for %s object"
                             % (key, self.__class__.__name__))
    def __getitem__ (self, key) :
        return self._d[key].get()
    def __setitem__ (self, key, val) :
        self._d[key].set(val)
    def __len__ (self) :
        return len(self._d)
    def stop (self) :
        for v in self._d.values() :
            v.stop()
    def tikz (self, **tikz) :
        tpl = r"""%% {classname} {nodeid}
        \begin{{scope}}[{opt.aggregatescope}]
          {nodes}
          {ticks}
          {highlight}
          {states}
        \end{{scope}}
        %% /{classname} {nodeid}
        """
        opt = TikZ(tikz) + self._o
        self.stop()
        return cleandoc(tpl).format(classname=self.__class__.__name__,
                                    nodeid=self.nodeid,
                                    opt=opt,
                                    nodes="\n  ".join(self._nodes(opt)),
                                    ticks=("\n  ".join(self._ticks(opt))
                                           or "% skipped ticks"),
                                    highlight=("\n  ".join(self._highlight(opt))
                                               or "% skipped reads/writes"),
                                    states=("\n  ".join(self._states(opt))
                                            or "% skipped states"))
    def _nodes (self, opt) :
        grow = opt.aggregate["grow"]
        anchor = opp(grow)
        for key, val in self._d.items() :
            yield val._node(opt)
            opt = (opt / "pos") + {"value": {"anchor": anchor},
                                   "pos": {"at": f"({val.nodeid}.{grow})"}}
        first, last = self._first.nodeid, self._last.nodeid
        yield fr"\node[{opt.group},fit=({first}) ({last})] ({self.nodeid}) {{}};"
    def _ticks (self, opt) :
        side = opt.aggregate.get("ticks", None)
        if not side :
            return
        anchor = opp(side)
        for key, val in self._d.items() :
            tick = self._tick(key, opt)
            nodeid = val.nodeid
            yield fr"\node[{opt.ticks},anchor={anchor}] at ({nodeid}.{side}) {{{tick}}};"
    def _tick (self, key, opt) :
        return fr"{key}\strut"
    def _highlight (self, opt) :
        for access, steps in zip([opt.valueread, opt.valuewrite, opt.valuereadwrite],
                                 [lambda v: v._r - v._w,
                                  lambda v: v._w - v._r,
                                  lambda v: v._w & v._r]) :
            anim = defaultdict(list)
            for key, val in self._d.items() :
                for s in steps(val) :
                    anim[s].append(key)
            mina = defaultdict(set)
            for step, keys in anim.items() :
                mina[tuple(sorted(keys))].add(step)
            def minstep (item) :
                return tuple(sorted(item[1]))
            for info, steps in sorted(mina.items(), key=minstep) :
                when = ",".join(str(s) for s in sorted(steps))
                yield fr"\only<{when}>{{"
                for key in info :
                    nodeid = (self@key).nodeid
                    yield (fr"\draw[{access}] ({nodeid}.south west) rectangle"
                           fr" ({nodeid}.north east);")
                yield "}"
    def _states (self, opt) :
        anim = defaultdict(list)
        for key, val in self._d.items() :
            for value, start, stop in val._h :
                anim[start,stop].append((key, value))
        def firstlargest (item) :
            return (item[0][0], -item[0][1])
        for (start, stop), info in sorted(anim.items(), key=firstlargest) :
            if all(v is None for _, v in info) :
                continue
            yield fr"\only<{start}-{stop}>{{"
            for key, val in info :
                if val is not None :
                    nodeid = (self@key).nodeid
                    try :
                        yield "  " + val.__tikz__(f"{nodeid}.center", opt)
                    except :
                        yield fr"  \node at ({nodeid}) {{{val}}};"
            yield "}"

class Array (Aggregate) :
    _defaults = {"aggregate": {"index": "north"}}
    @autorepr
    def __init__ (self, init, index=[], **tikz) :
        super().__init__(init, **tikz)
        self._o.aggregatescope = self._o.arrayscope
        self._i = {}
        for i in index :
            self.index(i)
    def index (self, name, init=None) :
        self._i[name] = self._env[name] = Value(init)
    def _ticks (self, opt) :
        for t in super()._ticks(opt) :
            yield t
        side = opt.aggregate.get("index", None)
        if not side :
            return
        anchor = opp(side)
        anim = defaultdict(list)
        for name, value in self._i.items() :
            value.stop()
            for val, start, stop in value._h :
                for step in range(start, stop+1) :
                    anim[step].append((name, val))
        mina = defaultdict(set)
        for step, keys in anim.items() :
            mina[tuple(sorted(keys))].add(step)
        def minstep (item) :
            return tuple(sorted(item[1]))
        for info, steps in sorted(mina.items(), key=minstep) :
            xpos = defaultdict(list)
            for name, value in info :
                if value is not None :
                    xpos[value].append(name)
            if not xpos :
                continue
            when = ",".join(str(s) for s in sorted(steps))
            yield fr"\uncover<{when}>{{"
            for value, names in xpos.items() :
                label = self._index(names, opt)
                try :
                    cell = (self@value).nodeid
                except ValueError :
                    continue
                yield (fr"  \node[{opt.index},anchor={anchor},at=({cell}.{side})]"
                       fr" {{{label}}};")
            yield "}"
    def _index (self, names, opt) :
        label = ",".join(sorted(names))
        return fr"{label}\strut"

class Struct (Aggregate) :
    _defaults = {"aggregate": {"grow": "south",
                               "ticks": "west"}}
    @autorepr
    def __init__ (self, init, **tikz) :
        self.__dict__.update(_d={}, _o=None, _first=None, _last=None, nodeid=None)
        super().__init__(init, **tikz)
        self._o.aggregatescope = self._o.structscope
    def _tick (self, key, opt) :
        return fr".{key}\strut"
    def __getattr__ (self, name) :
        return self[name]
    def __setattr__ (self, name, value) :
        if name in self._d :
            self[name] = value
        else :
            self.__dict__[name] = value

class Heap (CAniTikZ) :
    _defaults = {"group": {"inner sep": "5mm"}}
    @autorepr
    def __init__ (self, **tikz) :
        super().__init__(tikz)
        self._alloc = {}
        self._freed = {}
    def new (self, data) :
        self._alloc[data.nodeid] = [data, self.IP, ""]
        return Pointer(data)
    def free (self, ptr) :
        data = ptr.get()
        l = self._freed[data.nodeid] = self._alloc.pop(data.nodeid)
        l[-1] = self.IP
        ptr.set(None)
    def tikz (self, **tikz) :
        opt = TikZ(tikz) + self._o
        classname = self.__class__.__name__
        nodeid = self.nodeid
        return (f"%% {classname} {nodeid}\n"
                + "\n".join(self._tikz(opt))
                + f"\n%% /{classname} {nodeid}")
    def _tikz (self, opt) :
        fit = []
        yield fr"\begin{{scope}}[{opt.heapscope}]"
        for data, start, stop in chain(self._alloc.values(), self._freed.values()) :
            fit.append(data.nodeid)
            yield fr"  \uncover<{start}-{stop}>{{"
            yield fr"    %% allocated data"
            yield fr"    \begin{{scope}}[{opt.alloc}]"
            for line in data.tikz(**opt.dict()).splitlines() :
                yield "      " + line
            yield r"    \end{scope}"
            yield r"  }"
            opt = opt + {"pos": {opt.heap["grow"]:
                                 "{dist} of {prev}".format(dist=opt.heap["distance"],
                                                           prev=(data@None).nodeid)}}
        children = " ".join(f"({nid})" for nid in fit)
        yield fr"  \node[{opt.group},fit={children}] ({self.nodeid}) {{}};"
        yield r"\end{scope}"

_flip = {"right": "below",
         "below": "right",
         "left": "above",
         "above": "left"}

class Box (CAniTikZ) :
    @autorepr
    def __init__ (self, *content, grow="right", distance="15mm", parent=None, **tikz) :
        super().__init__(tikz)
        self._grow = grow
        self._dist = distance
        self._parent = parent
        self._data = tuple(self._init(content))
    def _init (self, content) :
        for obj in content :
            if isinstance(obj, CAniTikZ) :
                yield obj
            elif isinstance(obj, list) :
                yield self.__class__(*obj,
                                     grow=(_flip.get(self._grow) if self._parent is None
                                           else self._parent._grow),
                                     distance=self._dist,
                                     parent=self,
                                     **self._o.dict())
            else :
                raise ValueError("invalid %s content: %r"
                                 % (self.__class__.__name__, obj))
    def tikz (self, **tikz) :
        opt = TikZ(tikz) + self._o
        classname = self.__class__.__name__
        nodeid = self.nodeid
        return (f"%% {classname} {nodeid} ({self._grow})\n"
                + "\n".join(self._tikz(opt))
                + f"\n%% /{classname} {nodeid}")
    def _tikz (self, opt) :
        fit = []
        yield fr"\begin{{scope}}[{opt.boxscope}]"
        for data in self._data :
            fit.append(data.nodeid)
            yield fr"  %% box {self.nodeid} content"
            for line in data.tikz(**opt.dict()).splitlines() :
                yield "    " + line
            opt = opt + {"pos": {self._grow:
                                 "{dist} of {prev}".format(dist=self._dist,
                                                           prev=(data@None).nodeid)}}
        children = " ".join(f"({nid})" for nid in fit)
        yield fr"  \node[{opt.group},fit={children}] ({self.nodeid}) {{}};"
        yield r"\end{scope}"
