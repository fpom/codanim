import inspect
from functools import wraps
from yapf.yapflib.yapf_api import FormatCode

class ExecEnv (dict) :
    _ValueClass = None
    def __init__ (self, *l, **k) :
        super().__init__(*l, **k)
    def __setitem__ (self, key, val) :
        old = self.get(key, None)
        try :
            old.set(val)
        except :
            if not isinstance(val, self._ValueClass) :
                val = self._ValueClass(val)
            super().__setitem__(key, val)
    def __getitem__ (self, key) :
        old = self.get(key, None)
        try :
            return old.get()
        except :
            return super().__getitem__(key)
    def exec (self, code) :
        exec(code, self)
    def eval (self, code) :
        return eval(code, self)

def _repr (obj) :
    if inspect.isclass(obj) :
        return obj.__name__
    elif inspect.isfunction(obj) :
        return obj.__name__
    else :
        return repr(obj)

class CAni (object) :
    _env = ExecEnv()
    @property
    def IP (self) :
        return self._env.get("IP", 1)
    @IP.setter
    def IP (self, val) :
        dict.__setitem__(self._env, "IP", val)
    @property
    def RET (self) :
        return self._env.get("RET", None)
    @RET.setter
    def RET (self, val) :
        dict.__setitem__(self._env, "RET", val)
    def exec (self, code) :
        self._env.exec(code)
    def eval (self, code) :
        RET = self.RET = self._env.eval(code)
        return RET
    _init_args = (None, None)
    def __repr__ (self) :
        largs, kargs = self._init_args
        if largs and kargs :
            r = "{}({}, {})".format(self.__class__.__name__,
                                    ", ".join(_repr(l) for l in largs),
                                    ", ".join("{}={}".format(k, _repr(v))
                                              for k, v in kargs.items()))
        elif largs :
            r = "{}({})".format(self.__class__.__name__,
                                ", ".join(_repr(l) for l in largs))
        elif kargs :
            r = "{}({})".format(self.__class__.__name__,
                                ", ".join("{}={}".format(k, _repr(v))
                                          for k, v in kargs.items()))
        else :
            r = "{}()".format(self.__class__.__name__)
        return FormatCode(r)[0]

def autorepr (method) :
    @wraps(method)
    def wrapper (self, *l, **k) :
        self.__dict__["_init_args"] = (l, k)
        return method(self, *l, **k)
    return wrapper

