import os, sys, json, datetime, threading
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict

class Lvl(Enum):
    D=0; I=1; W=2; E=3; N=4
    def ge(self, o): return self.value >= o.value
    def gt(self, o): return self.value > o.value

ESC = chr(27)
CODES = {'D': '[36m', 'I': '[32m', 'W': '[33m', 'E': '[31m'}

@dataclass
class LogE:
    ts: str = ''; lvl: str = ''; msg: str = ''; mod: str = ''
    d: Optional[Dict] = None; sid: Optional[str] = None
    sc: Optional[str] = None; act: Optional[str] = None
    def j(self):
        return json.dumps({'ts': self.ts, 'lvl': self.lvl, 'msg': self.msg, 'mod': self.mod,
                         'd': self.d, 'sid': self.sid, 'sc': self.sc, 'act': self.act},
                        ensure_ascii=False, default=str)

class Out:
    def w(self, e): pass
    def f(self): pass

class Con(Out):
    def w(self, e):
        code = CODES.get(e.lvl, '')
        col = ESC + code if code else ''
        res = ESC + '[0m' if code else ''
        d = (' ' + json.dumps(e.d, ensure_ascii=False, default=str)) if e.d else ''
        s = (' [' + e.sc + ']') if e.sc else ''
        sys.stderr.write(f'{col}{e.ts} {e.lvl:5s}{res} [{e.mod}]{s} {e.msg}{d}\n')
    def f(self): sys.stderr.flush()

class File(Out):
    def __init__(self, p):
        self.p = p
        os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
        self.f = open(p, 'a', encoding='utf-8')
        self.l = threading.Lock()
    def w(self, e):
        with self.l: self.f.write(e.j() + '\n')
    def f(self):
        with self.l: self.f.flush()
    def c(self):
        with self.l:
            if self.f:
                self.f.close()
                self.f = None

class Log:
    def __init__(self, m, lv=Lvl.I, o=None):
        self.m = m; self.lv = lv; self.o = o or [Con()]; self.l = threading.Lock()
        self.sid = None
    def ts(self):
        return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    def log(self, lv, msg, sc=None, act=None, d=None):
        if lv.ge(self.lv): return
        e = LogE(ts=self.ts(), lvl=lv.name, msg=msg, mod=self.m, d=d, sid=self.sid, sc=sc, act=act)
        with self.l:
            for o in self.o:
                try: o.w(e)
                except: pass
    def d(self, m, **k): self.log(Lvl.D, m, **k)
    def i(self, m, **k): self.log(Lvl.I, m, **k)
    def w(self, m, **k): self.log(Lvl.W, m, **k)
    def e(self, m, **k): self.log(Lvl.E, m, **k)
    def t(self, a, s, m, **d): self.i(m, sc=s, act=a, **d)

_loggers: Dict[str, Log] = {}
_gl = threading.Lock()
_go = [Con()]
_g = Lvl.I

def glog(m, lv=None) -> Log:
    with _gl:
        if m not in _loggers:
            _loggers[m] = Log(m, lv or _g, list(_go))
        return _loggers[m]

def sl(log_dir='/root/.openclaw/workspace/logs', lv=Lvl.I):
    global _g
    _g = lv
    _go.clear()
    _go.append(Con())
    os.makedirs(log_dir, exist_ok=True)
    d = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d')
    _go.append(File(os.path.join(log_dir, f'{d}.ndjson')))
