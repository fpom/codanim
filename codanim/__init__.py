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
