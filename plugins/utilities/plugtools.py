# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
PlugTools v1.5 - Live Plugin Action

Beta. Feedback is appreciated.
Adds a dev console tab for plugin management.

Features vary between:
- Dynamic Control: Enables immediate loading and reloading of plugins.
- Real-time Monitoring: Reports status of plugin files (new, modified, deleted).
- Plugin Overview: Displays operational state (enabled/disabled) and integrity (original/modified).
- Plugin Data: Provides file path, size, timestamps, and code structure analysis.
- Navigation: Offers controls to browse the plugin list.
- Logging: Has a built-in log display with proper indentation.
"""

from os.path import (
    splitext,
    getmtime,
    getctime,
    basename,
    getsize,
    isfile,
    exists,
    join
)
from os import (
    scandir,
    access,
    R_OK,
    stat
)
from babase import (
    PluginSpec,
    Plugin,
    Call,
    env,
    app
)
from babase._devconsole import (
    DevConsoleTabEntry as ENT,
    DevConsoleTab as TAB
)
from bauiv1 import (
    get_string_width as sw,
    SpecialChar as sc,
    charstr as cs,
    apptimer as teck,
    screenmessage as push,
    getsound as gs
)
from traceback import format_exc as ERR
from datetime import datetime
from importlib import reload
from typing import override
from sys import modules
from gc import collect
from ast import (
    FunctionDef,
    ImportFrom,
    Attribute,
    ClassDef,
    Import,
    parse,
    walk,
    Name
)

class PlugTools(TAB):
    KEY = 'PT_BY'
    def __init__(s):
        s.bys = META()
        s.bad = []
        s.logs = 'No errors'
        s.mem = {_:MT(_) for _ in s.bys}
        s.eye = look()
        s.e = False
        s.spy()
    def spy(s):
        b = 0
        for _ in s.bys.copy():
            if not exists(PAT(_)):
                s.bys.remove(_)
                push(f'Plugin {_} suddenly disappeared!\nAnd so, was removed from list.',color=(1,1,0))
                gs('block').play()
                s.eye = look()
                if s.hl() == _: s.hl(None)
                b = 1
                sp = app.plugins.plugin_specs.get(_,0)
                if not sp: continue
                p = app.plugins
                if getattr(sp,'enabled',False):
                    o = s.sp.plugin
                    if o in p.active_plugins:
                        p.active_plugins.remove(o)
                    if o in p.plugin_specs:
                        p.plugin_specs.pop(o)
                    del s.sp.plugin,o
                    collect()
                    try: reload(modules[NAM(_,0)])
                    except: pass
                continue
            if MT(_) != s.mem[_] and _ not in s.bad:
                s.bad.append(_)
                push(f'Plugin {_} was modified!\nSee if you want to take action.',color=(1,1,0))
                gs('dingSmall').play()
                b = 1
        if hasattr(s,'sp'):
            e = getattr(s.sp,'enabled',False)
            if e != s.e:
                s.e = e
                b = 1
        eye = look()
        s1 = set(s.eye)
        s2 = set(eye)
        df = list(s2-s1)
        nu = []
        if df:
            for dd in df:
                try: _ = kang(dd)
                except:
                    eye.remove(dd)
                    continue
                nu.append(_)
                s.bys.append(_)
                s.mem[_] = 0
                s.bad.append(_)
            s.eye = eye
            b = 1
        if nu:
            l = len(nu)
            push(f"Found {l} new plugin{['s',''][l==1]}:\n{', '.join(nu)}\nSee what to do with {['it','them'][l!=1]}",color=(1,1,0))
            gs('dingSmallHigh').play()
        if b:
            try: s.request_refresh()
            except RuntimeError: pass
        teck(0.1,s.spy)
    @override
    def refresh(s):
        # Preload
        by = s.hl()
        if by not in s.bys:
            by = None
            s.hl(None)
        s.by = by
        s.sp = app.plugins.plugin_specs.get(by,0) if by else 0
        s.i = getattr(s,'i',0 if by is None else s.bys.index(by)//10)
        # UI
        w = s.width
        x = -w/2
        z = x+w
        # Bools
        e = s.e = getattr(s.sp,'enabled',False)
        m = by in s.bad
        d = by is None
        # Buttons
        sx = w*0.2
        mx = sx*0.98
        z -= sx
        s.button(
            'Metadata',
            pos=(z,50),
            size=(mx,43),
            call=s.metadata,
            disabled=d
        )
        s.button(
            ['Load','Reload'][e],
            pos=(z,5),
            size=(mx,43),
            call=s._load,
            disabled=d
        )
        # Separator
        s.button(
            '',
            pos=(z-(w*0.006),5),
            size=(2,90)
        )
        # Plugin info
        sx = w*0.1
        z -= sx
        az = z+sx/2.23
        t = 'Entry' if d else by
        tw = GSW(t)
        mx = sx*0.9
        s.text(
            t,
            pos=(az,80),
            scale=1 if tw<mx else mx/tw,
        )
        t = 'State' if d else ['Disabled','Enabled'][e]
        tw = GSW(t)
        s.text(
            t,
            pos=(az,50),
            scale=1 if tw<mx else mx/tw,
        )
        t = 'Purity' if d else ['Original','Modified'][m]
        tw = GSW(t)
        s.text(
            t,
            pos=(az,20),
            scale=1 if tw<mx else mx/tw,
        )
        # Separator
        s.button(
            '',
            pos=(z-(w*0.0075),5),
            size=(2,90)
        )
        # Next
        sx = w*0.03
        mx = sx*0.6
        z -= sx
        s.button(
            cs(sc.RIGHT_ARROW),
            pos=(z,5),
            size=(mx,90),
            call=s.next,
            disabled=(s.i+1)*10 > len(s.bys)
        )
        # Plugins
        sx = w*0.645/5
        mx = sx*0.99
        zx = mx*0.9
        z -= sx*5
        for i in range(5):
            for j in range(2):
                k = j*5+i+s.i*10
                if k >= len(s.bys): break
                t = s.bys[k]
                tw = GSW(t)
                s.button(
                    t,
                    size=(mx,43),
                    pos=(z+sx*i,50-45*j),
                    label_scale=1 if tw<zx else zx/tw,
                    call=Call(s.hl,t),
                    style=[['blue','blue_bright'],['purple','purple_bright']][t in s.bad][t==by]
                )
        # Prev
        sx = w*0.03
        mx = sx*0.6
        z -= sx*0.7
        s.button(
            cs(sc.LEFT_ARROW),
            pos=(z,5),
            size=(mx,90),
            call=s.prev,
            disabled=s.i==0
        )
        if s.height <= 100: return
        # Expanded logs
        t = s.logs
        h = 25
        pos = (x+10,s.height)
        z = len(t)
        p = list(pos)
        m = max(t.replace('\\n','') or [''],key=GSW)
        l = GSW(str(m))/1.2
        ln = t.split('\\n')
        mm = max(ln,key=GSW)
        sk = 0.8
        ml = (s.height-100) * 0.04
        ww = (l*sk)*len(mm)
        sk = sk if ww<s.width else (s.width*0.98/ww)*sk
        zz = len(ln)
        sk = sk if zz<=ml else (ml/zz)*sk
        xf = 0
        for i in range(z):
            p[0] += [l*sk,0][i==0]
            if xf: xf = 0; continue
            j = t[i]
            k = t[i+1] if (i+1) < z else j
            if j == '\\' and k == 'n':
                p[0] = pos[0]-(l*1.5)*sk
                p[1] -= h*(sk*1.28)
                xf = 1
                continue
            s.text(
                j,
                pos=tuple(p),
                h_align='center',
                v_align='top',
                scale=sk
            )
    def hl(s,i=None):
        i and deek()
        c = app.config
        if i is None: return c.get(s.KEY,None)
        c[s.KEY] = i
        c.commit()
        s.request_refresh()
    def _load(s):
        h = ['load','reload'][s.e]
        ex,er = s.load()
        if ex:
            k = f': {ex}' if str(ex).strip() else ''
            j = f'Error {h}ing {s.by}'
            push(f'{j}{k}\nExpand dev console to see more.\nTraceback dumped to terminal too.',color=(1,0,0))
            gs('error').play()
            m = j+':\n'+er
            print('[PlugTools] '+m)
            s.logs = m.replace('\n','\\n')
            s.request_refresh()
            return
        s.logs = 'No errors'
        if ex is False: return
        push(h.title()+'ed '+s.by,color=(0,1,0))
        gs('gunCocking').play()
        s.request_refresh()
    def load(s):
        _ = s.by
        if _ in s.bad:
            s.bad.remove(_)
            s.mem[_] = MT(_)
        p = app.plugins
        if s.e:
            if hasattr(s.sp,'plugin'):
                o = s.sp.plugin
                if o in p.active_plugins:
                    p.active_plugins.remove(o)
                del s.sp.plugin
            collect()
            try: m = reload(modules[NAM(_,0)])
            except KeyError:
                gs('block').play()
                push(f"{s.by} is malformed!\nAre you sure there's no errors?",color=(1,1,0))
                return (False,0)
            except Exception as ex: return (ex,ERR())
        else: m = __import__(NAM(_,0))
        try: cls = getattr(m,_.split('.',1)[1])
        except Exception as ex: return (ex,ERR())
        try: ins = cls()
        except Exception as ex: return (ex,ERR())
        try: ins.on_app_running()
        except Exception as ex: return (ex,ERR())
        s.sp = PluginSpec(class_path=_,loadable=True)
        s.sp.enabled = True
        s.sp.plugin = ins
        p.plugin_specs[_] = s.sp
        p.active_plugins.append(ins)
        return (0,0)
    def metadata(s):
        f = PAT(s.sp.class_path)
        info = []
        if exists(f):
            info.append(f'File Path: {f}')
            info.append("File Exists: Yes")
            info.append(f"File Size: {getsize(f)} bytes")
            try:
                with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                    lines = file.readlines()
                    content = "".join(lines) # Read entire content for AST parsing and char count
                    line_count = len(lines)
                    char_count = len(content)

                    info.append(f"Line Count: {line_count}")
                    info.append(f"Character Count: {char_count}")

                    # Python specific programmatic analysis
                    function_count = 0
                    class_count = 0
                    import_statement_count = 0
                    comment_lines = 0
                    blank_lines = 0

                    try:
                        tree = parse(content) # Use parse directly
                        for node in walk(tree): # Use walk directly
                            if isinstance(node, FunctionDef): # Use FunctionDef directly
                                function_count += 1
                            elif isinstance(node, ClassDef): # Use ClassDef directly
                                class_count += 1
                            elif isinstance(node, (Import, ImportFrom)): # Use Import, ImportFrom directly
                                import_statement_count += 1
                        # Iterate through physical lines for comments and blank lines
                        for line in lines:
                            stripped_line = line.strip()
                            if not stripped_line:
                                blank_lines += 1
                            elif stripped_line.startswith('#'):
                                comment_lines += 1
                        info.append(f"Function Definitions: {function_count}")
                        info.append(f"Class Definitions: {class_count}")
                        info.append(f"Import Statements: {import_statement_count}")
                        info.append(f"Comment Lines: {comment_lines}")
                        info.append(f"Blank Lines: {blank_lines}")

                    except SyntaxError as se:
                        info.append(f"Python Syntax Error: {se}")
                    except Exception as ast_e:
                        info.append(f"Error analyzing Python file structure: {ast_e}")

            except Exception as e:
                info.append(f"Could not read file content for analysis: {e}")

            creation_time = datetime.fromtimestamp(getctime(f))
            info.append(f"Creation Time: {creation_time}")

            mod_time = datetime.fromtimestamp(getmtime(f))
            info.append(f"Last Modified: {mod_time}")
        else:
            info.append(f'File Path: {f}')
            info.append("File Exists: No")
        push('\n'.join(info))
        gs('powerup01').play()
    def next(s):
        deek()
        s.i += 1
        s.request_refresh()
    def prev(s):
        deek()
        s.i -= 1
        s.request_refresh()

MT = lambda _: stat(PAT(_))
GSW = lambda s: sw(s,suppress_warning=True)
NAM = lambda _,py=1: _.split('.',1)[0]+['','.py'][py]
PAT = lambda _: join(ROOT,NAM(_))
ROOT = env()['python_directory_user']
META = lambda: app.meta.scanresults.exports_by_name('babase.Plugin')
def look():
    python_files = []
    try:
        with scandir(ROOT) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.endswith(".py"):
                    if access(entry.path, R_OK):
                        python_files.append(entry.path)
    except FileNotFoundError:
        pass
    except PermissionError:
        pass
    return python_files
def kang(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    tree = parse(source_code)
    lines = source_code.splitlines()
    export_line_num = -1
    for i, line in enumerate(lines):
        if line.strip() == '# ba_meta export babase.Plugin':
            export_line_num = i + 1
            break
    if export_line_num == -1:
        return None

    filename_without_ext = splitext(basename(file_path))[0]
    for node in tree.body:
        if isinstance(node, ClassDef):
            if node.lineno > export_line_num:
                for base in node.bases:
                    if (isinstance(base, Name) and base.id == 'Plugin') or \
                       (isinstance(base, Attribute) and base.attr == 'Plugin' and isinstance(base.value, Name) and base.value.id == 'babase'):
                        return f"{filename_without_ext}.{node.name}"
    return None
deek = lambda: gs('deek').play()

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    def __init__(s):
        C = PlugTools
        N = C.__name__
        E = ENT(N,C)
        I = app.devconsole
        I.tabs = [_ for _ in I.tabs if _.name != N]+[E]
        I._tab_instances[N] = E.factory()
