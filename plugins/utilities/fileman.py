# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
FileMan v1.0 - Advanced file manager

Adds a button to settings menu.
Experimental. Read code to know more.
"""

from babase import (
    PluginSubsystem as SUB,
    Plugin,
    env
)
from bauiv1 import (
    get_virtual_screen_size as res,
    clipboard_set_text as COPY,
    get_string_height as strh,
    get_string_width as strw,
    get_special_widget as zw,
    get_replays_dir as rdir,
    containerwidget as cw,
    hscrollwidget as hsw,
    screenmessage as SM,
    buttonwidget as obw,
    scrollwidget as sw,
    SpecialChar as sc,
    imagewidget as iw,
    textwidget as tw,
    gettexture as gt,
    apptimer as teck,
    AppTimer as tuck,
    getsound as gs,
    charstr as cs,
    MainWindow,
    open_url,
    Call,
    app
)
from os.path import (
    basename,
    getmtime,
    splitext,
    dirname,
    getsize,
    exists,
    isfile,
    isdir,
    join,
    sep
)
from os import (
    listdir as ls,
    getcwd,
    rename,
    remove,
    access,
    mkdir,
    X_OK,
    R_OK
)
from shutil import (
    copytree,
    rmtree,
    copy,
    move
)
from bascenev1 import new_replay_session as REP
from http.client import HTTPSConnection as GO
from datetime import datetime as DT
from mimetypes import guess_type
from random import uniform as UF
from threading import Thread
from pathlib import Path

class FileMan(MainWindow):
    VER = '1.0'
    INS = []
    @classmethod
    def resize(c):
        c.clean()
        [_.on_resize() for _ in c.INS]
    @classmethod
    def clean(c):
        c.INS = [_ for _ in c.INS if not _.gn and _.p.exists()]
    @classmethod
    def loadc(c):
        [setattr(c,f'COL{i}',_) for i,_ in enumerate(var('col'))]
    def __del__(s):
        s.__class__.clean()
    def on_resize(s):
        [_.delete() for _ in s.killme]
        s.killme.clear()
        c = s.uploadc
        s.spyt = s.sharel = s.buf = s.uploadc = None
        if c: c.close()
        s.fresh()
    def __init__(s,src):
        s.__class__.clean()
        s.__class__.INS.append(s)
        s.wop()
        s.url = s.urlo = var('cwd')
        s.urlbln = s.dro = s.gn = s.rlyd = s.flon = False
        s.amoled = sum(s.COL5)==0
        s.pusho = s.sorti = 0
        s.pushi = -0.1
        s.sl = (None,None)
        [setattr(s,_,None) for _ in ['pushe','eno','leno','clp','gab','clpm','rlydt','buf','uploadc','cursnd','rfl','rflo']]
        [setattr(s,_,[]) for _ in ['trash','btns','secs','docs','drkids','drol','okes','fkids','ftrash','statkids','fcons','flkids','killme']]
        s.pushq = ''
        # root
        s.p = cw(
            background=False,
            toolbar_visibility='menu_minimal'
        )
        s.rect = iw(
            texture=gt('softRect'),
            opacity=[0.3,0.85][s.amoled],
            color=s.COL5,
            parent=s.p
        )
        super().__init__(
            root_widget=s.p,
            transition='in_scale',
            origin_widget=src
        )
        s.bg = iw(
            texture=gt('white'),
            parent=s.p,
            position=(-2,0),
            color=s.COL5
        )
        s.bg2 = bw(
            bg='empty',
            parent=s.p,
            oac=s.bga
        )
        # dock
        s.docs = [iw(
            color=s.COL1,
            parent=s.p,
            texture=gt('white'),
            opacity=0.5
        ) for _ in range(3)]
        # sections
        s.secs = [tw(
            parent=s.p,
            text=_,
            h_align='center',
            color=s.COL4,
            scale=0.7
        ) for _ in ['Action','Extra','New']]
        # actions
        s.gab = bw(
            parent=s.p,
            oac=s.cancel,
            size=(0,0),
            selectable=False
        )
        r = []
        for _ in range(6):
            l = ['Copy','Move','Delete','Share','Rename','Open'][_]
            r.append(bw(
                parent=s.p,
                label=l,
                oac=Call(s.act,0,_)
            ))
        s.btns.append(r)
        # extra
        r = []
        for _ in range(4):
            l = ['Star','Sort','Filter','Theme'][_]
            r.append(bw(
                parent=s.p,
                label=l,
                oac=Call(s.act,1,_)
            ))
        s.btns.append(r)
        s.fltxt = tw(
            editable=True,
            parent=s.p,
            v_align='center',
            glow_type='uniform',
            allow_clear_button=False
        )
        s.flh = tw(
            parent=s.p,
            v_align='center',
            color=s.COL0
        )
        s.gab2 = bw(
            parent=s.p,
            oac=s.unfl,
            size=(0,0),
            selectable=False
        )
        # new
        r = []
        for _ in range(2):
            l = ['File','Folder'][_]
            r.append(bw(
                parent=s.p,
                label=l,
                oac=Call(s.act,2,_)
            ))
        s.btns.append(r)
        # back
        s.bb = bw(
            parent=s.p,
            label=' '+cs(sc.BACK),
            oac=s.bye
        )
        cw(s.p,cancel_button=s.bb)
        # up
        s.ub = bw(
            parent=s.p,
            label=cs(sc.SHIFT),
            oac=s.up
        )
        # url
        s.urlbg = bw(
            parent=s.p,
            oac=s.urled
        )
        s.urlt = tw(
            color=s.COL2,
            text=s.url,
            v_align='center',
            parent=s.p
        )
        s.urla = tw(
            editable=True,
            size=(0,0),
            parent=s.p,
            text=s.url
        )
        s.trash.append(tuck(0.01,s.urlspy,repeat=True))
        s.trash.append(tuck(0.1,s.urlbl,repeat=True))
        # rf
        s.rfb = bw(
            parent=s.p,
            label=cs(sc.PLAY_BUTTON),
            oac=s.rf
        )
        # pre
        s.preb = bw(
            parent=s.p,
            label=cs(sc.LOGO_FLAT),
            oac=s.pre
        )
        # yes
        s.yesbg = iw(
            parent=s.p,
            texture=gt('white'),
            color=s.COL1,
            opacity=0.5,
            position=(20,20)
        )
        s.yesbg2 = iw(
            parent=s.p,
            texture=gt('white'),
            color=s.COL5,
            opacity=0.3,
        )
        s.yesp1 = sw(
            parent=s.p,
            border_opacity=0,
            position=(17,20)
        )
        s.yesp2 = cw(
            parent=s.yesp1,
            background=False
        )
        s.lmao = tw(
            parent=s.yesp2,
            text=''
        )
        # oke
        s.okes = [tw(
            parent=s.p,
            text=_,
            h_align='left',
            color=s.COL4,
            scale=0.7
        ) for _ in SRT()]
        # drop
        s.drbg = iw(
            texture=gt('white'),
            parent=s.p,
            opacity=0.7,
            color=s.COL5
        )
        s.drp1 = sw(
            border_opacity=0,
            parent=s.p
        )
        s.drp2 = cw(
            background=False,
            parent=s.drp1
        )
        # push
        s.pushbg2 = iw(
            color=s.COL5,
            parent=s.p,
            opacity=0,
            texture=gt('softRect')
        )
        s.pushbg = iw(
            color=s.COL1,
            parent=s.p,
            opacity=0,
            texture=gt('white')
        )
        s.pusht = tw(
            color=s.COL2,
            parent=s.p,
            h_align='center',
            v_align='center'
        )
        s.trash.append(tuck(0.01,s.fpush,repeat=True))
        # finally
        s.fresh()
        teck(0.5,lambda:s.push(f'FileMan v{s.VER} Ready!',du=1.5) if s.eno is None else 0)
    def meh(s):
        if s.sl[0] is None:
            s.btw('Select something!')
            return 1
        if s.sl[1] == '..':
            s.btw('What are you doing blud')
            return 1
    def btw(s,t,du=3):
        s.snd('block')
        s.push(t,color=s.COL3,du=du)
    def act(s,i,j,gay=False):
        if s.gn: return
        w = s.btns[i][j]
        match i:
            case 0:
                match j:
                    case 0:
                        if s.clp:
                            if s.clpm != j:
                                s.btw("You're already doing something else!")
                                return
                            c = var('cwd')
                            chk = join(c,basename(s.clp))
                            st1,st2 = splitext(chk)
                            nn = st1+'_copy'+st2 if exists(chk) else chk
                            if exists(nn):
                                s.btw('A copy of this '+['file','folder'][isdir(chk)]+' already exists!')
                                return
                            try: [copy,copytree][isdir(s.clp)](s.clp,nn)
                            except Exception as e:
                                s.btw(str(e))
                                return
                            else:
                                GUN()
                                s.push('Pasted!')
                                s.clp =  None
                                s.fresh()
                        else:
                            if s.meh(): return
                            s.clp = s.sl[1]
                            s.clpm = j
                            s.push(f'Copied! Now go to destination.')
                            GUN()
                            s.fresh(skip=True)
                    case 1:
                        if s.clp:
                            if s.clpm != j:
                                s.btw("You are already doing something else!")
                                return
                            c = var('cwd')
                            chk = join(c,basename(s.clp))
                            if exists(chk):
                                s.btw('There is a '+['file','folder'][isdir(chk)]+' with the same name here.')
                                return
                            try: move(s.clp,c)
                            except Exception as e:
                                s.btw(str(e))
                                return
                            else:
                                GUN()
                                s.push('Pasted!')
                                s.clp = None
                                s.fresh()
                        else:
                            if s.meh(): return
                            s.clp = s.sl[1]
                            s.clpm = j
                            s.push(f'Now go to destination and paste.')
                            GUN()
                            s.fresh(skip=True)
                    case 2:
                        if s.clpm:
                            s.btw("Finish what you're doing first!")
                            return
                        if s.meh(): return
                        h = s.sl[1]
                        bn = basename(h)
                        if not s.rlyd:
                            s.beep(1,0)
                            s.push(f"Really delete "+["the file '"+bn+"'","the whole '"+bn+"' folder"][isdir(h)]+" forever? Press again to confirm.",du=3,color=s.COL3)
                            s.rlydt = tuck(2.9,Call(setattr,s,'rlyd',False))
                            s.rlyd = True
                            return
                        s.rlyd = False
                        s.rlydt = None
                        f = [remove,rmtree][isdir(h)]
                        try: f(h)
                        except Exception as e:
                            s.btw(str(e))
                            return
                        else:
                            GUN()
                            s.push('Deleted!')
                            s.sl = (None,None)
                            s.fresh()
                    case 3:
                        if s.meh(): return
                        f = s.sl[1]
                        if isdir(f):
                            s.btw("You can't share a folder!")
                            return
                        s.wop()
                        o = w.get_screen_space_center()
                        xs,ys = 400,170
                        p = s.uploadp = cw(
                            parent=zw('overlay_stack'),
                            scale_origin_stack_offset=o,
                            stack_offset=o,
                            size=(xs,ys),
                            background=False,
                            transition='in_scale'
                        )
                        s.killme.append(p)
                        iw(
                            parent=p,
                            size=(xs*1.2,ys*1.2),
                            texture=gt('softRect'),
                            opacity=[0.2,0.55][s.amoled],
                            position=(-xs*0.1,-ys*0.1),
                            color=s.COL5
                        )
                        iw(
                           parent=p,
                           texture=gt('white'),
                           color=s.COL1,
                           opacity=0.7,
                           size=(xs,ys)
                        )
                        bw(
                            parent=p,
                            label='Back',
                            oac=s.cupload,
                            position=(30,15),
                            size=(xs-60,30)
                        )
                        s.cpsharelb = bw(
                            parent=p,
                            label='...',
                            oac=s.cpsharel,
                            position=(30,50),
                            size=(xs-60,30)
                        )
                        s.opsharelb = bw(
                            parent=p,
                            label='...',
                            oac=s.opsharel,
                            position=(30,85),
                            size=(xs-60,30)
                        )
                        bw(
                            parent=p,
                            label='Upload to bashupload.com',
                            oac=s.upload,
                            position=(30,120),
                            size=(xs-60,30)
                        )
                    case 4:
                        if s.meh(): return
                        t = s.fkids[s.sl[0]]
                        fp = s.sl[1]
                        if s.clp == j:
                            q = tw(query=t)
                            try:
                                if sep in q: raise ValueError("You can't use directory separator in filename!")
                                Path(q)
                            except Exception as e:
                                s.btw(str(e) or 'Invalid filename!')
                                return
                            else:
                                if (basename(fp) == q) and not gay:
                                    s.btw("Write a new name blud")
                                    return
                                chk = join(var('cwd'),q)
                                if exists(chk):
                                    s.btw(f"There is a {['file','folder'][isdir(chk)]} with this name already!")
                                    return
                                else:
                                    nfp = join(dirname(fp),q)
                                    try:
                                        rename(fp,nfp)
                                    except PermissionError:
                                        if exists(nfp): pass
                                        else:
                                            s.push('Permission denied!')
                                            return
                                    except Exception as e:
                                        s.btw(str(e))
                                        return
                                    else:
                                        s.push('Renamed!')
                                        s.clp = None
                                        GUN()
                                        s.fresh(sl=nfp)
                        else:
                            if s.clpm:
                                s.btw("You didn't paste yet blud")
                                return
                            tw(t,editable=True,color=s.COL7)
                            cw(s.yesp2,visible_child=t)
                            s.clpm = s.clp = j
                            s.push('Now edit the filename, then press Done.')
                            if s.flon and s.rfl:
                                [_.delete() for _ in s.flkids[s.sl[0]]]
                            GUN()
                            s.fresh(skip=True)
                    case 5:
                        if s.meh(): return
                        if s.clpm:
                            s.btw("Press again when you're free!")
                            return
                        h = s.sl[1]
                        bn = basename(h)
                        if isdir(h):
                            s.cd(h)
                            s.snd('deek')
                            return
                        s.stat = 1000
                        s.wop()
                        k = s.fkids[s.sl[0]] if gay else w
                        gcen = lambda: ((o:=k.get_screen_space_center()),(o[0]-s.size[0]/5,o[1]) if gay else o)[1]
                        o = gcen()
                        xs,ys = [_*0.6 for _ in s.size]
                        p = cw(
                            parent=zw('overlay_stack'),
                            scale_origin_stack_offset=o,
                            size=(xs,ys),
                            background=False,
                            transition='in_scale'
                        )
                        s.killme.append(p)
                        iw(
                            parent=p,
                            size=(xs*1.2,ys*1.2),
                            texture=gt('softRect'),
                            opacity=[0.3,0.7][s.amoled],
                            position=(-xs*0.1,-ys*0.1),
                            color=s.COL5
                        )
                        iw(
                           parent=p,
                           texture=gt('white'),
                           color=s.COL5,
                           opacity=0.7,
                           size=(xs,ys)
                        )
                        b = bw(
                            parent=p,
                            position=(20,ys-70),
                            label=' '+cs(sc.BACK),
                            size=(50,50),
                            oac=Call(s.statbye,p,gcen)
                        )
                        cw(p,cancel_button=b)
                        ix = xs-250
                        iw(
                            parent=p,
                            texture=gt('white'),
                            color=s.COL1,
                            position=(90,ys-72),
                            size=(ix,54),
                            opacity=0.5
                        )
                        tw(
                            parent=p,
                            h_align='center',
                            v_align='center',
                            position=(xs/2-60,ys-60),
                            text=basename(h),
                            maxwidth=ix-100
                        )
                        iw(
                            parent=p,
                            texture=gt('white'),
                            color=s.COL1,
                            opacity=0.5,
                            position=(20,20),
                            size=(xs-40,ys-110)
                        )
                        bw(
                            parent=p,
                            label=cs(sc.REWIND_BUTTON),
                            position=(xs-141,ys-70),
                            size=(50,50),
                            oac=Call(s.stata,-1),
                            repeat=True
                        )
                        bw(
                            parent=p,
                            label=cs(sc.FAST_FORWARD_BUTTON),
                            position=(xs-71,ys-70),
                            size=(50,50),
                            oac=Call(s.stata,1),
                            repeat=True
                        )
                        s.oops = 0
                        try:
                            with open(h,'r') as f:
                                da = f.read()
                        except Exception as ex:
                            da = ''
                            s.oops = 1
                            if isinstance(ex,PermissionError): kek = 'Permission denied!'
                            elif isinstance(ex,UnicodeDecodeError): kek = 'No preview avaiable'
                            else: kek = str(ex)
                        else:
                            if not da:
                                s.oops = 1
                                kek = 'No data'
                        if not s.oops:
                            fxs = xs-40
                            fys = ys-110
                            s.statsz = (fxs,fys)
                            p0 = s.statp0 = sw(
                                parent=p,
                                position=(20,20),
                                size=(fxs,fys),
                                border_opacity=0,
                                capture_arrows=True
                            )
                            s.statda = da
                            s.statp = 0
                            s.statl = []
                            s.itw()
                        else:
                            ty = s.gtype(h)
                            if ty == 'Replay':
                                tw(
                                    parent=p,
                                    position=(xs/2-20,ys-150),
                                    text='Press start to preview replay.\nKeep in mind that this will destroy the current FileMan session.',
                                    h_align='center',
                                    color=s.COL4,
                                    maxwidth=xs-60
                                )
                                bw(
                                    parent=p,
                                    label='Start',
                                    oac=lambda:(b.activate(),teck(0.1,s.bye),teck(0.3,Call(REP,h))),
                                    position=(xs/2-75,ys/2-135),
                                    size=(150,40)
                                )
                            elif ty == 'Texture' and bn in TEX():
                                wd = min(xs-80,ys-150)
                                tex = gt(splitext(bn)[0])
                                iw(
                                    parent=p,
                                    texture=tex,
                                    size=(wd,wd),
                                    position=(xs/2-wd/2,40)
                                )
                            elif ty == 'Audio' and bn in AUDIO():
                                tw(
                                    parent=p,
                                    position=(xs/2-20,ys-150),
                                    text=f'Sound is recognized by filename, not data.\nPress the buttons below to play/pause',
                                    h_align='center',
                                    color=s.COL4,
                                    maxwidth=xs-60
                                )
                                bw(
                                    parent=p,
                                    label=cs(sc.PLAY_BUTTON),
                                    oac=lambda:(getattr(s.cursnd,'stop',lambda:0)(),setattr(s,'cursnd',gs(splitext(bn)[0])),s.cursnd.play()),
                                    position=(xs/2-30,ys/2-135),
                                    size=(40,40)
                                )
                                bw(
                                    parent=p,
                                    label=cs(sc.PAUSE_BUTTON),
                                    oac=lambda:getattr(s.cursnd,'stop',lambda:0)(),
                                    position=(xs/2+30,ys/2-135),
                                    size=(40,40)
                                )
                            else:
                                tw(
                                    parent=p,
                                    text=kek,
                                    position=(xs/2-25,ys/2-35),
                                    h_align='center',
                                    v_align='center',
                                    maxwidth=xs-100
                                )
            case 1:
                match j:
                    case 0:
                        star = var('star')
                        c = var('cwd')
                        if c in star:
                            star.remove(c)
                            s.push('Unstarred!')
                        else:
                            star.append(c)
                            s.push('Starred! (bomb top right)')
                        var('star',star)
                        GUN()
                        s.fresh(skip=True)
                    case 1:
                        xs,ys = 200,230
                        s.wop()
                        gcen = lambda: ((o:=w.get_screen_space_center()),(o[0]-s.size[0]/5,o[1]) if gay else o)[1]
                        o = gcen()
                        p = cw(
                            parent=zw('overlay_stack'),
                            scale_origin_stack_offset=o,
                            size=(xs,ys),
                            background=False,
                            transition='in_scale',
                            stack_offset=(o[0],o[1]),
                            on_outside_click_call=lambda:(cw(p,transition='out_scale'),s.laz())
                        )
                        s.killme.append(p)
                        iw(
                            parent=p,
                            size=(xs*1.2,ys*1.2),
                            texture=gt('softRect'),
                            opacity=[0.3,0.7][s.amoled],
                            position=(-xs*0.1,-ys*0.1),
                            color=s.COL5
                        )
                        iw(
                           parent=p,
                           texture=gt('white'),
                           color=s.COL5,
                           opacity=0.7,
                           size=(xs,ys)
                        )
                        by = 40
                        srt = SRT()
                        for _ in range(4):
                            bw(
                                position=(20,ys-20-by-(by+10)*_),
                                size=(xs-40,by),
                                label=srt[_],
                                oac=Call(s.surt,_,p),
                                parent=p
                            )
                    case 2:
                        s.flon = True
                        s.snd('deek')
                        s.fresh(skip=True)
                    case 3:
                        ox, oy = s.size
                        xs = ys = min(ox / 2, oy / 2)
                        xs *= 1.3
                        s.wop()
                        s.push('FileMan uses 12 main colors. Tap on a color to edit it. Press outside to cancel.',du=6)
                        o = w.get_screen_space_center()
                        def nuke():
                            cw(p,transition='out_scale')
                            s.laz()
                            s.push('Cancelled! Nothing was saved')
                        p = cw(parent=zw('overlay_stack'), scale_origin_stack_offset=o, size=(xs, ys), stack_offset=(-100,0), background=False, transition='in_scale',on_outside_click_call=nuke)
                        bw(parent=p,size=(xs+200,ys),bg='empty')
                        s.killme.append(p)
                        iw(parent=p, size=(xs * 1.2, ys * 1.2), texture=gt('softRect'), opacity=[0.3,0.7][s.amoled], position=(-xs * 0.1, -ys * 0.1), color=s.COL5)
                        iw(parent=p, texture=gt('white'), color=s.COL5, opacity=0.7, size=(xs + 200, ys))
                        temp_colors, scl, sl = [getattr(s, f'COL{i}') for i in range(12)], [0, 0, 0, 0], 0
                        kids, nubs, grad = [], [], []
                        def save():
                            if var('col') == temp_colors:
                                s.btw('At least change a color blud')
                                return
                            var('col',temp_colors)
                            GUN()
                            cw(p,transition='out_scale')
                            s.__class__.loadc()
                            s.bye()
                            SM('Reopen FileMan to see changes!')
                        def update_previews():
                            f3()
                            f4()
                            c = temp_colors[sl]
                            obw(kids[sl], color=c, textcolor=INV(c))
                        def f3():
                            [iw(l, position=(xs + scl[k] * ps - 16, 39 + qs * 5 - (qs) * k)) for k, l in enumerate(nubs)]
                        def f4():
                            c = temp_colors[sl]
                            [obw(l, color=(c[0] * (k / 19), c[1] * (k / 19), c[2] * (k / 19))) for k, l in enumerate(grad)]
                        def f2(k, l):
                            nonlocal scl
                            scl[k] = l
                            val = l / 19.0
                            if k < 3:
                                c_list = list(temp_colors[sl])
                                c_list[k] = val
                                temp_colors[sl] = new_color = tuple(c_list)
                                scl[3] = int(max(new_color) * 19)
                            elif k == 3:
                                c = temp_colors[sl]
                                current_max = max(c)
                                if current_max > 0:
                                    scale = val / current_max
                                    temp_colors[sl] = new_color = (c[0] * scale, c[1] * scale, c[2] * scale)
                                    scl[:3] = [int(x * 19) for x in new_color]
                            update_previews()
                        def f(z, sh=0):
                            nonlocal sl, scl
                            [obw(_, label='') for _ in kids]
                            obw(kids[z], label=cs(sc.DPAD_CENTER_BUTTON))
                            sl = z
                            if not sh: s.snd('deek')
                            c = temp_colors[sl]
                            scl[:3] = [int(x * 19) for x in c]
                            scl[3] = int(max(c) * 19) if any(c) else 0
                            update_previews()
                        bs, qs, ps = (ys - 60) / 3, (ys - 60) / 6, 9
                        for k in range(4):
                            for l in range(20):
                                ah = l / 19.0
                                b = obw(
                                    parent=p, position=(xs + l * ps, 47 + qs * 5 - qs * k), size=(ps + 2, qs / 2), label='', texture=gt('white'), enable_sound=False, on_activate_call=Call(f2, k, l),
                                    color=( (ah, 0, 0) if k < 1 else (0, ah, 0) if k < 2 else (0, 0, ah) if k < 3 else (ah, ah, ah) )
                                )
                                if k == 3: grad.append(b)
                        nubs = [iw(parent=p, size=(35, 35), texture=gt('nub'), color=(10, 10, 10), opacity=0.4) for _ in range(4)]
                        for x in range(4):
                            for y in range(3):
                                z = x * 3 + y
                                c = temp_colors[z]
                                kids.append(bw(parent=p, position=(20 + (bs + 10) * x, 20 + (bs + 10) * y), size=(bs, bs), color=c, textcolor=INV(c), oac=Call(f, z)))
                        bw(parent=p, position=(xs + 5, 24 + qs), size=(172, qs - 2), label='Save', oac=save)
                        def reset():
                            mem = COL()
                            if mem == temp_colors:
                                s.btw("Reset what? It's already at default")
                                return
                            for i,m in enumerate(mem):
                                temp_colors[i] = m
                            update_previews()
                            GUN()
                            s.push('Restored default colors! now press save')
                        bw(parent=p, position=(xs + 5, 18.5), size=(172, qs - 3), label='Reset', oac=reset)
                        f(0, sh=1)
            case 2:
                match j:
                    case 0:
                        if s.clpm:
                            s.btw("You're already in the middle of something")
                            return
                        c = var('cwd')
                        n = join(c,'new_file')
                        while exists(n): n+='_again'
                        try: Path(n).touch()
                        except PermissionError:
                            s.btw('Permission denied!')
                            return
                        except Exception as ex:
                            s.btw(str(ex))
                            return
                        s.fresh(sl=n)
                        # rename
                        s.act(0,4,gay=True)
                    case 1:
                        if s.clpm:
                            s.btw("You're already in the middle of something")
                            return
                        c = var('cwd')
                        n = join(c,'new_folder')
                        while exists(n): n+='_again'
                        try: mkdir(n)
                        except PermissionError:
                            s.btw('Permission denied!')
                            return
                        except Exception as ex:
                            s.btw(str(ex))
                            return
                        s.fresh(sl=n)
                        # rename
                        s.act(0,4)
    def surt(s,_,p):
        if _ == s.sorti:
            s.btw('Already sorted by '+SRT()[_]+'!')
            return
        s.sorti = _
        GUN()
        cw(p,transition='out_scale')
        s.fresh(sl=s.sl[1])
    def statbye(s,p,gcen):
        try: cen = gcen()
        except: p.delete()
        else: cw(p,transition='out_scale',scale_origin_stack_offset=cen)
        s.laz()
        s.statda = None
        s.statl = []
        s.statp = 0
    def itw(s):
        PYTHON_KEYWORDS = {
            'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'False', 'finally', 'for', 'from',
            'global', 'if', 'import', 'in', 'is', 'lambda', 'None', 'nonlocal',
            'not', 'or', 'pass', 'raise', 'return', 'True', 'try', 'while', 'with', 'yield'
        }
        PYTHON_BUILTINS = {
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes', 'callable',
            'chr', 'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir', 'divmod',
            'enumerate', 'eval', 'exec', 'filter', 'float', 'format', 'frozenset', 'getattr',
            'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
            'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview',
            'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'print', 'property',
            'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted',
            'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'
        }
        OPERATORS = {'+', '-', '*', '/', '%', '=', '!', '<', '>', '&', '|', '^', '~'}
        BRACKETS = {'(', ')', '{', '}', '[', ']', ':', ',', '.'}

        s.COL_KEYWORD = getattr(s, 'COL_KEYWORD', (1.5, 0.9, 0.4))
        s.COL_BUILTIN = getattr(s, 'COL_BUILTIN', (0.7, 1.2, 1.8))
        s.COL_STRING = getattr(s, 'COL_STRING', (0.5, 1.5, 0.5))
        s.COL_NUMBER = getattr(s, 'COL_NUMBER', (1.2, 1.2, 0.5))
        s.COL_OPERATOR = getattr(s, 'COL_OPERATOR', (1.5, 1.5, 1.5))
        s.COL_BRACKET = getattr(s, 'COL_BRACKET', (0.9, 0.9, 0.9))
        s.COL_END_MARKER = getattr(s, 'COL_END_MARKER', (1.8, 0.6, 0.6)) # Neon Red for the marker

        da = s.statda
        end_marker = f'[End of chunk | Press {cs(sc.FAST_FORWARD_BUTTON)}]'
        if len(da) > s.stat:
            if len(da) > s.statp + int(s.stat / 2):
                da = da[s.statp:s.stat + s.statp] + end_marker
            else:
                da = da[s.statp:s.stat + s.statp]
        az = sum(s.statl)
        lines = [_.replace('\\n','\\'+"~"+"n") for _ in da.splitlines()]
        zc = len(str(az + len(lines)))
        da = '\\n'.join([f"{str(i+1+az).zfill(zc)} | {_}" for i, _ in enumerate(lines)])
        z = len(da)
        p0 = s.statp0
        fxs, fys = s.statsz
        [_.delete() for _ in s.statkids]
        s.statkids.clear()
        hh = 35
        m = max(da.replace('\\n', '') or ' ', key=GSW)
        l = GSW(str(m)) / 1.5
        l = max(15,l)
        l = min(l,20)
        das = da.split('\\n')
        mm = len(max(das, key=len) or '')
        ldas = len(das)
        s.statl.append(ldas)
        rxs = max(l * mm + 30, fxs)
        rys = max(hh * ldas, fys - 15)
        pos = (0, rys - 40)
        po = list(pos)
        q0 = cw(parent=p0, size=(fxs, rys), background=False)
        p1 = hsw(parent=q0, size=(fxs, rys), border_opacity=0)
        q1 = cw(parent=p1, background=False, size=(rxs, fys))
        s.statkids += [q0, p1, q1]

        # --- Main Rendering Loop ---
        i = 0
        nc = 0
        in_triple_comment = False
        triple_quote_char = None
        is_first_char_offset_applied = False # Flag for the critical offset
        off = zc + 3
        try:
            mud = int(da[off] == '#')
        except IndexError:
            mud = 0

        while i < z:
            # -- Priority 1: The End Marker --
            if not in_triple_comment and not mud and da.startswith(end_marker, i):
                if not is_first_char_offset_applied:
                    po[0] -= l * 1.5; is_first_char_offset_applied = True
                for c in end_marker:
                    big = nc < zc
                    po[0] += l
                    s.statkids.append(tw(text=c, position=(po[0], po[1] - (3 if big else 0)), h_align='center', v_align='top', parent=q1, big=big, color=s.COL_END_MARKER))
                    nc += 1
                i += len(end_marker)
                continue

            # -- Priority 2: Multi-line comment delimiters --
            if i + 2 < z and da[i:i+3] in ('"'*3, "'"*3):
                chunk = da[i:i+3]
                if not in_triple_comment or chunk == triple_quote_char * 3:
                    if not is_first_char_offset_applied:
                        po[0] -= l * 1.5; is_first_char_offset_applied = True
                    if not in_triple_comment:
                        in_triple_comment = True; triple_quote_char = chunk[0]
                    else:
                        in_triple_comment = False; triple_quote_char = None
                    for _ in range(3):
                        big = nc < zc; po[0] += l
                        s.statkids.append(tw(text=da[i], position=(po[0], po[1] - (3 if big else 0)), h_align='center', v_align='top', parent=q1, big=big, color=s.COL3 if big else s.COL0))
                        nc += 1; i += 1
                    continue

            # -- Priority 3: Newlines --
            if i + 1 < z and da[i:i+2] == '\\n':
                po[0] = pos[0]-l*1.5; po[1] -= hh; nc = 0
                try:
                    mud = int(da[i + 2 + off] == '#' and not in_triple_comment)
                except IndexError:
                    mud = 0
                i += 2
                continue

            # -- Priority 4: Render based on state (comment or code) --
            # Apply the critical offset before rendering the first character
            if not is_first_char_offset_applied:
                po[0] -= l * 1.5; is_first_char_offset_applied = True

            if in_triple_comment or mud:
                big = nc < zc
                color = (s.COL0 if big else s.COL3) if in_triple_comment else (s.COL10 if big else s.COL11)
                po[0] += l
                s.statkids.append(tw(text=da[i], position=(po[0], po[1] - (3 if big else 0)), h_align='center', v_align='top', parent=q1, big=big, color=color))
                nc += 1; i += 1
                continue

            # -- Priority 5: Python Syntax Highlighting --
            char = da[i]; token = char; token_color = s.COL2
            if char in ("'", '"'):
                k = i + 1
                while k < z and (da[k] != char or da[k-1] == '\\'): k += 1
                token = da[i:k+1]; token_color = s.COL_STRING
            elif char.isdigit() or (char == '.' and i + 1 < z and da[i+1].isdigit()):
                k = i
                while k < z and (da[k].isdigit() or da[k] == '.'): k += 1
                token = da[i:k]; token_color = s.COL_NUMBER
            elif char.isalpha() or char == '_':
                k = i
                while k < z and (da[k].isalnum() or da[k] == '_'): k += 1
                token = da[i:k]
                if token in PYTHON_KEYWORDS: token_color = s.COL_KEYWORD
                elif token in PYTHON_BUILTINS: token_color = s.COL_BUILTIN
            elif char in OPERATORS: token_color = s.COL_OPERATOR
            elif char in BRACKETS: token_color = s.COL_BRACKET

            for c in token:
                big = nc < zc; po[0] += l
                s.statkids.append(tw(text=c, position=(po[0], po[1] - (3 if big else 0)), h_align='center', v_align='top', parent=q1, big=big, color=token_color))
                nc += 1
            i += len(token)

        cw(q0,visible_child=tw(parent=q0, text='', position=(0,rys)))
        cw(q1,visible_child=tw(parent=q1, text='', position=(0,rys)))
    def stata(s,i):
        if not s.oops:
            n = s.statp + s.stat*i
            ok = len(s.statda)
            if ok <= n:
                s.btw('Reached EOF!',du=1)
                return
            if n < 0:
                s.btw('Already at first chunk!',du=1)
                return
            s.snd('deek')
            s.statp = n
            if i<0: [s.statl.pop(-1) for _ in [0,0]]
            s.itw()
        else:
            s.btw('No more open file buffers!')
    def cpsharel(s):
        l = s.vsharel()
        if not l: return
        COPY(str(l))
        s.ding(1,1)
        s.push(f"Copied '{l}' to clipboard!")
    def opsharel(s):
        l = s.vsharel()
        if not l: return
        s.snd('deek')
        open_url(l)
    def vsharel(s):
        l = getattr(s,'sharel',0)
        if not l:
            s.btw("Upload first!")
            return
        return l
    def cupload(s):
        c = s.uploadc
        s.spyt = s.sharel = s.buf = s.uploadc = None
        if c:
            c.close()
            s.ding(0,0)
            s.push('Cancelled!')
        else: s.laz()
        cw(s.uploadp,transition='out_scale')
    def upload(s):
        f = s.sl[1]
        s.ding(1,0)
        s.push('Uploading...')
        Thread(target=Call(s._upload,f)).start()
        s.spyt = tuck(0.2,Call(s.spy,s.on_upload),repeat=True)
    def _upload(s, l):
        try:
            c = s.uploadc = GO('bashupload.com')
            filename = basename(l)
            url_path = '/' + filename
            with open(l, 'rb') as f: body = f.read()
            headers = {'Content-Type': 'application/octet-stream'}
            c.request('POST', url_path, body=body, headers=headers)
            s.buf = c.getresponse().read().decode()
        except Exception:
            if s.uploadc: s.buf = ''
        finally:
            if s.uploadc:
                s.uploadc.close()
                s.uploadc = s.sharel = None
    def on_upload(s,t):
        if not t:
            s.btw("Couldn't upload")
            return
        s.sharel = t.splitlines()[5][5:]+'?download=1'
        s.ding(0,1)
        s.push('Success!')
        obw(s.cpsharelb,label='Copy Direct URL')
        obw(s.opsharelb,label=s.sharel)
    def ding(s,i,j):
        a = ['Small','']
        x,y = a[i],a[j]
        s.snd('ding'+x)
        teck(0.1,gs('ding'+y).play)
    def beep(s,i,j):
        s.snd(f'raceBeep{str(i+1)}')
        teck(0.1,gs(f'raceBeep{str(j+1)}').play)
    def spy(s,f):
        if s.buf is None: return
        b = s.buf
        s.buf = None
        f(b)
        s.spyt = None
    def cancel(s):
        c = s.clp
        s.clp = None
        s.push('Cancelled!')
        s.snd('deek')
        s.fresh(skip=c!=4)
    def fresh(s,skip=False,sl=None):
        if s.gn: return
        rx,ry = res()
        z = s.size = (rx*0.8,ry*0.8)
        x,y = z
        # root
        cw(s.p,size=z)
        iw(s.bg,size=z)
        obw(s.bg2,size=z)
        iw(s.rect,size=(x*1.2,y*1.2),position=(-x*0.1,-y*0.1))
        # docks, secs, btns
        h = (x-80)
        f = y-191
        v = 18
        for i in range(3):
            e = h/[2,3,6][i]
            iw(s.docs[i],size=(e,100),position=(v,f))
            tw(s.secs[i],position=(v+e/2-23,f+1))
            a = s.btns[i]; l = int(len(a)/2)
            bh = (e-[6,5,4][i]*10-(l-1)*10)/l
            for j in range(l):
                for k in [0,l]:
                    zz = bh
                    of = 20
                    ga = (
                        (i == k == 0 and s.clpm == j)
                        or
                        (i == 0 and j == 1 and k == 3 and s.clpm == 4)
                    )
                    if ga and s.clp:
                        zz -= 40
                        of -= 2
                    po = v+of+(bh+20)*j,f+60-30*bool(k)
                    ww = a[j+k]
                    obw(ww,position=po,size=(zz,25))
                    if not ga:
                        if i == 1 and j == k == 0:
                            obw(ww,label=['Star','Unstar'][var('cwd') in var('star')])
                        elif i == 1 and j == 0 and k:
                            tw(s.fltxt,position=(po[0]-2,po[1]-2))
                            tw(s.flh,position=(po[0],po[1]-2),max_height=37,maxwidth=zz-42)
                            obw(s.gab2,position=(po[0]+zz-32,po[1]))
                            if s.flon:
                                obw(ww,size=(0,0),label='')
                                tw(s.fltxt,size=(zz-38,27))
                                tw(s.flh,text='' if s.rfl else 'Write something...')
                                obw(s.gab2,size=(bh-(zz-38),25),label='X')
                                if not s.fltk:
                                    s.rflo = s.fltk = ''
                                    s.fltk = tuck(0.1,s.onfl,repeat=True)
                            else:
                                obw(ww,size=(zz,25),label='Filter')
                                tw(s.fltxt,size=(0,0),text='')
                                tw(s.flh,text='')
                                obw(s.gab2,size=(0,0),label='')
                                s.rfl = s.rflo = s.fltk = None
                        continue
                    he = bool(s.clp)
                    obw(s.gab,position=(po[0]+zz+11,po[1]),size=(bh-3-zz,25),label=['','X'][he],selectable=he)
                    obw(ww,label=[['Copy','Move',0,0,'Rename'][s.clpm],['Paste','Done'][s.clpm==4]][he])
                    if not he: s.clpm = None
            v += e+20
        # back
        f = y-70
        obw(s.bb,position=(20,f),size=(50,50))
        # up
        obw(s.ub,position=(90,f),size=(50,50))
        # url
        e = x - 398
        obw(s.urlbg,size=(e,50),position=(195,f))
        tw(s.urlt,position=(180,y-60),maxwidth=x-370)
        # rf
        obw(s.rfb,position=(251+e,f),size=(50,50))
        # pre
        obw(s.preb,position=(323+e,f),size=(50,50))
        # skip the rest
        if skip: return
        # drop
        s.droc()
        # oke
        fly = 35
        sx,sy = x-37,y-230
        h = sx/6
        v = 30
        rat = [3,1,1,1]
        for i,_ in enumerate(s.okes):
            j = rat[i]
            tw(_,position=(v+[30,0][i!=0],sy-15))
            v += h*j
        # push
        s.rpush()
        # files
        p = s.yesp2
        [_.delete() for _ in s.fkids]
        s.fkids.clear()
        [_.delete() for _ in s.ftrash]
        s.ftrash.clear()
        [_.delete() for _ in s.fcons]
        s.fcons.clear()
        [[i.delete() for i in j] for j in s.flkids]
        s.flkids.clear()
        fl = s.gfull()
        u = s.rfl
        if s.flon and s.rfl:
            fl = [_ for _ in fl if (_ == '..') or (u in basename(_))]
            cur = s.sl[1]
            if cur:
                if cur in fl: sl = cur
                else: s.sl = (None,None)
        # yes
        rsy = len(fl)*fly
        sw(s.yesp1,size=(sx,sy-40))
        cw(s.yesp2,size=(sx,rsy))
        tw(s.lmao,position=(0,rsy))
        iw(s.yesbg,size=(sx,sy))
        iw(s.yesbg2,size=(sx,40),position=(20,sy-20))
        # files
        for i,_ in enumerate(fl):
            if _ == sl:
                s.sl = (i,_)
            v = 15
            hm = s.gdata(_)
            for k in range(4):
                j = rat[k]
                e = h*j
                ee = [30,0][k!=0]
                po = (v+ee,rsy-fly-fly*i)
                t = tw(
                    parent=p,
                    size=(e-15-ee,fly),
                    position=po,
                    text=hm[k],
                    maxwidth=e-15-ee,
                    v_align='center',
                    selectable=True,
                    click_activate=True,
                    on_activate_call=Call(s._sl,i,_,fl),
                    glow_type='uniform',
                    allow_clear_button=False
                )
                if s.flon and u and not k:
                    ci = 0
                    bn = basename(_)
                    ret = []
                    while True:
                        nxt = bn.find(u,ci)
                        if nxt == -1: break
                        bf = bn[:nxt]
                        ret.append(tw(
                            parent=p,
                            text=u,
                            position=(po[0]+GSW(bf),po[1]+3),
                            v_align='center'
                        ))
                        ci = nxt + len(u)
                    s.flkids.append(ret)
                if ee:
                    s.fcons.append(iw(
                        position=(po[0]-ee-8,po[1]+1),
                        texture=s.gtex(_),
                        size=(ee+1,ee+1),
                        parent=p
                    ))
                v += e
                if k: s.ftrash.append(t)
                else: s.fkids.append(t)
            if _ == sl:
                cw(s.yesp2,visible_child=t)
        s.slco(fl)
    def onfl(s):
        s.rfl = tw(query=s.fltxt)
        if s.rfl != s.rflo:
            s.rflo = s.rfl
            s.fresh(sl=s.sl[1])
    def unfl(s):
        s.flon = False
        s.snd('deek')
        s.fresh(sl=s.sl[1])
    def gtex(s,_):
        ty = s.gtype(_)
        t = (
            'replayIcon' if _ == '..' else
            'folder' if isdir(_) else
            'tv' if ty == 'Replay' else
            'audioIcon' if ty == 'Audio' else
            'graphicsIcon' if ty == 'Texture' else
            'star' if ty == 'Mesh' else
            'achievementOutline' if ty == 'Font' else
            'file'
        )
        return gt(t)
    def slco(s,fl):
        # cancel rename
        if s.clp == 4: s.cancel()
        sli = s.sl[0]
        for i,g in enumerate(zip(fl,s.fkids,s.fcons)):
            _,w,r = g
            c = [(s.COL10,s.COL11),(s.COL8,s.COL9)][isdir(_)][sli == i]
            tw(w,color=c,editable=False)
            iw(r,color=c)
        for i,z in enumerate(s.flkids):
            for j in z:
                tw(j,color=[s.COL0,s.COL3][sli==i])
    def _sl(s,i,_,fl):
        if s.sl[0] == i:
            if isdir(_): s.cd(_)
            else: s.act(0,5,gay=True)
            return
        s.sl = (i,_)
        s.slco(fl)
    def gdata(s,_):
        b = isdir(_)
        try: mt = DT.fromtimestamp(getmtime(_)).strftime('%m/%d/%Y %I:%M %p')
        except: mt = '?'
        try: sz = FMT(getsize(_))
        except: sz = '?'
        return (
            basename(_),
            s.gtype(_),
            '' if b else mt,
            '' if b else sz
        )
    def gtype(s,_):
        if isdir(_): return ['Folder','Parent'][_=='..']
        f = 'File'
        h = guess_type(_)[0] or f
        if not '.' in _: return h.title()
        if h == f:
            return {
                'brp':'Replay',
                'bob':'Mesh',
                'cob':'Mesh',
                'ogg':'Audio',
                'ktx':'Texture',
                'fdata':'Font'
            }.get(_.split('.')[-1],f)
        else: return h.title()
    def gfull(s):
        c = var('cwd')
        h = []
        if dirname(c) != c: h = ['..']
        if not access(c, R_OK): return h
        items = [join(c,_) for _ in ls(c)]
        da = {}
        for item in items:
            name, item_type, date_modified_str, _ = s.gdata(item)
            try:
                date_sortable = DT.strptime(date_modified_str, '%m/%d/%Y %I:%M %p') if date_modified_str else DT.min
            except: date_sortable = DT.min
            try: mt = getmtime(item)
            except: mt = 0
            da[item] = (basename(item).lower(), item_type.lower(), date_sortable, mt, isdir(item))
        return h + sorted(items, key=lambda i: (
            not da[i][4],
            da[i][0] if s.sorti == 0 else
            da[i][1] if s.sorti == 1 else
            da[i][2] if s.sorti == 2 else
            da[i][3]
        ))
    def pre(s):
        s.wop()
        r = s._pre()
        xs = 200
        ys = 160
        pc = s.preb.get_screen_space_center()
        p = s.prep = cw(
            parent=zw('overlay_stack'),
            background=False,
            transition='in_scale',
            scale_origin_stack_offset=pc,
            on_outside_click_call=lambda:(cw(p,transition='out_scale'),s.laz()),
            size=(xs,ys),
            stack_offset=(pc[0]-xs/2+27,pc[1]-ys/2+27)
        )
        s.killme.append(p)
        iw(
            parent=p,
            size=(xs*1.2,ys*1.2),
            texture=gt('softRect'),
            opacity=[0.2,0.55][s.amoled],
            position=(-xs*0.1,-ys*0.1),
            color=s.COL5
        )
        iw(
            parent=p,
            size=(xs,ys),
            texture=gt('white'),
            color=s.COL1,
            opacity=0.7
        )
        p2 = sw(
            parent=p,
            size=(xs,ys)
        )
        rys = 30*len(r)
        p3 = cw(
            parent=p2,
            size=(xs,max(ys,rys)),
            background=False
        )
        for i,_ in enumerate(r):
            j,k = _
            tw(
                parent=p3,
                size=(xs,30),
                position=(0,rys-30-30*i),
                maxwidth=xs-20,
                text=j,
                click_activate=True,
                selectable=True,
                glow_type='uniform',
                on_activate_call=Call(s.pres,k)
            )
    def pres(s,k):
        GUN()
        cw(s.prep,transition='out_scale')
        s.cd(k)
    def _pre(s):
        e = app.env
        c = e.cache_directory
        d = dirname
        f = join(d(c),'ballistica_files','ba_data')
        g = cs(sc.LOGO_FLAT)+' '
        return [
            *[(cs(sc.DPAD_CENTER_BUTTON)+' '+(basename(_) or _),_) for _ in var('star')],
            (g+'Mods',e.python_directory_user),
            (g+'Replays',rdir()),
            (g+'Config',e.config_directory),
            (g+'Cache',c),
            (g+'Files',f),
            (g+'Python',join(f,'python')),
            (g+'Meshes',join(f,'meshes')),
            (g+'Audio',join(f,'audio')),
            (g+'Textures',join(f,'textures'))
        ]
    def rf(s):
        s.snd('ding')
        s.fresh()
        c = var('cwd')
        s.push('Refreshed '+(basename(c) or c))
    def up(s):
        o = var('cwd')
        n = dirname(o)
        if o == n:
            s.eno = 2
            s.nah()
            s.snd('block')
            return
        s.cd(n)
        s.snd('deek')
    def glike(s):
        c = var('cwd')
        if not access(c,R_OK):
            s.eno = not access(c,X_OK)
            s.nah()
            return []
        a = ls(c)
        f = []
        for _ in a:
            j = join(c,_)
            if isdir(j): f.append(j)
        r = [_ for _ in f if _.startswith(s.url)]
        return r
    def nah(s):
        if s.eno == s.leno: return
        s.leno = s.eno
        s.push([
            "I can't list files here! Write next folder name manually.",
            "I can't even enter there! Select another folder.",
            "Already reached root!"
        ][s.eno],color=s.enoc(),du=[3,3,2][s.eno])
    def enoc(s):
        return [
            s.COL7,
            s.COL4,
            s.COL2
        ][s.eno]
    def drop(s,i):
        if s.gn: return
        s.dro = i>0
        s.droc()
    def droc(s):
        s.drol = s.glike()
        s.rdrop()
    def rdrop(s):
        if s.gn: return
        [_.delete() for _ in s.drkids]
        s.drkids.clear()
        l = len(s.drol)
        if not s.dro or not s.drol or (l==1 and s.drol[0] == s.url):
            iw(s.drbg,size=(0,0))
            sw(s.drp1,size=(0,0))
            return
        x,y = s.size
        of = 20
        ys = 30*l+of
        fys = min(300,ys)
        yp = y-71-fys
        xs = x-325
        xp = 160
        iw(s.drbg,size=(xs,fys),position=(xp,yp))
        sw(s.drp1,size=(xs,fys),position=(xp,yp))
        cw(s.drp2,size=(xs,ys-of))
        for i,_ in enumerate(s.drol):
            p = (0,ys-30-30*i-of)
            s.drkids.append(tw(
                parent=s.drp2,
                position=p,
                text=_,
                color=s.COL9,
                selectable=True,
                click_activate=True,
                glow_type='uniform',
                on_activate_call=Call(s.cd,_),
                size=(GSW(_),30)
            ))
            s.drkids.append(tw(
                parent=s.drp2,
                position=p,
                text=s.url,
                color=s.COL4,
            ))
    def push(s,t,color=None,du=2):
        if s.gn: return
        s.rly = False
        s.rlydt = None
        tw(s.pusht,color=color or s.COL2)
        s.pushe = tuck(du,s.upush)
        s.pushi = 0.05
        s.pushq = t
        s.rpush()
    def upush(s):
        if s.gn: return
        s.pushi = -abs(s.pushi)
        s.pushq = ''
        s.rpush(1)
    def rpush(s,mode=0):
        if s.gn: return
        if mode:
            tw(s.pusht,text=s.pushq,color=s.COL2)
            return
        x = s.size[0]
        t = s.pushq
        w = GSW(t+' '*3)
        iw(s.pushbg,size=(w,30),position=(x/2-w/2,40))
        iw(s.pushbg2,size=(w*1.1,30*1.2),position=((x/2-w/2)-w*0.05,(40)-30*0.1))
        tw(s.pusht,text=t,maxwidth=w*0.95,position=(x/2-25,40))
    def fpush(s):
        if s.gn: return
        n = s.pusho + s.pushi
        if not (1 >= n >= 0): return
        s.pusho = n
        iw(s.pushbg,opacity=n)
        iw(s.pushbg2,opacity=[n*0.4,n][s.amoled])
    def urlbl(s):
        if s.gn: return
        if s.p.get_selected_child() not in [s.ub,s.drp2,s.drp1,s.urlbg]+s.drkids:
            s.urlbln = False
            if s.dro: s.drop(-1)
            return
        s.urlbln = not s.urlbln
        if not s.dro: s.drop(1)
    def urlspy(s):
        if s.gn: return
        s.url = tw(query=s.urla)
        b1 = exists(s.url)
        b2 = isdir(s.url)
        g1 = access(var('cwd'),R_OK)
        g2 = access(s.url,X_OK)
        b = b1 and b2 and g1 and g2
        av = not b1 and g1 and not g2 and s.drol
        if b or av: s.eno = None
        q = s.url != s.urlo
        if q: s.droc()
        lurl = var('cwd')
        can = b1 and b2 and s.url != lurl
        if can: s.cd(s.url); lurl = s.url
        co = (
            s.COL2 if b else
            s.COL3 if av else
            s.COL6 if not b1 else
            s.enoc()
        )
        tw(s.urlt,text=s.url+[' ','|'][s.urlbln or q],color=co)
        s.urlo = s.url
        if can or isdir(s.url): return
        # complete
        f = dirname(s.url)
        if not exists(f): return
        if f == lurl: return
        s.cd(f,dry=True)
    def cd(s,t,dry=False):
        if t == '..': t = dirname(var('cwd'))
        s.sl = (None,None)
        if s.flon and s.rfl:
            s.push("Filter is active! Press 'X' to cancel.",du=1.2,color=s.COL3)
        var('cwd',t)
        if s.eno != 1 and not access(t,X_OK):
            s.eno = 1
            s.nah()
        0 if dry else tw(s.urla,text=t)
        cw(s.yesp2,visible_child=s.lmao)
        s.fresh()
    def urled(s):
        if s.gn: return
        s.snd('deek')
        s.urla.activate()
    def wop(s):
        s.snd('powerup01')
    def laz(s):
        s.snd('laser')
    def bye(s):
        s.gn = True
        s.trash.clear()
        s.laz()
        s.main_window_back()
        s.__class__.clean()
        del s
    def snd(s,t):
        s.sn = gs(t)
        s.sn.play()
        teck(UF(0.13,0.15),s.sn.stop)
    def bga(s):
        s.urlbln = False

# Tools and Resources
# Lambda means it won't be stored in memory unless called
UI = lambda: app.ui_v1
SCL = lambda a,b,c=None: [a,b,c][UI().uiscale.value] or b
GSW = lambda t: strw(t,suppress_warning=True)
GSH = lambda t: strh(t,suppress_warning=True)
FMT = lambda size: (
    f"{size / 1024**3:.1f} GB" if size >= 1024**3 else (
    f"{size / 1024**2:.1f} MB" if size >= 1024**2 else (
    f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"))
)
GUN = lambda: gs('gunCocking').play()
BASE = lambda: join(dirname(app.env.cache_directory),'ballistica_files','ba_data')
AUDIO = lambda: ls(join(BASE(),'audio'))
TEX = lambda: ls(join(BASE(),'textures'))
SRT = lambda: ['Name','Type','Date Modifed','Size']
INV = lambda c: ((1-c[0])*2,(1-c[1])*2,(1-c[2])*2)
COL = lambda: [
    (0.5,0.5,0),
    (0.17,0.17,0.17),
    (1,1,1),
    (1,1,0),
    (0.6,0.6,0.6),
    (0,0,0),
    (1,0,0),
    (1,0,1),
    (0.5,0.25,0),
    (1,0.5,0),
    (0,0.5,0.5),
    (0,1,1)
]

# Config
def var(s,v=None):
    cfg = app.config; s = 'fm_'+s
    return cfg.get(s,v) if v is None else (cfg.__setitem__(s,v),cfg.commit())
def con(v,t):
    if var(v) is None: var(v,t)

# Default
con('cwd',getcwd())
con('star',[])
con('col',COL())

# Patches
f = SUB.on_screen_size_change; SUB.on_screen_size_change = lambda *a,**k: (FileMan.resize(),f(*a,**k))
bw = lambda *a,color=None,textcolor=None,oac=None,bg='white',label='',**k: obw(
    *a,
    on_activate_call=oac,
    texture=gt(bg),
    label=label,
    enable_sound=False,
    color=color or FileMan.COL1,
    textcolor=textcolor or FileMan.COL2,
    **k
)

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    def on_app_running(s):
        FileMan.loadc()
        teck(0.1,s.kang)
    def kang(s):
        from bauiv1lib.settings.allsettings import AllSettingsWindow as m
        i = '__init__'
        o = getattr(m,i)
        setattr(m,i,lambda z,*a,**k:(o(z,*a,**k),s.mk(z))[0])
    def fix(s,p):
        m = __import__('logging')
        i = 'exception'
        o = getattr(m,i)
        setattr(m,i,lambda *a,**k:0 if s.b == p.get_selected_child() else o(*a,**k))
    def mk(s,z):
        s.fix(z._root_widget)
        x,y = SCL((1000,800),(900,450))
        s.b = obw(
            position=(x*0.7,y*SCL(0.5,0.9)),
            parent=z._root_widget,
            icon=gt('folder'),
            size=(100,30),
            button_type='square',
            label='Man',
            enable_sound=False,
            color=FileMan.COL1,
            textcolor=FileMan.COL2,
            on_activate_call=lambda:s.run(z)
        )
    def run(s,z):
        z.main_window_replace(new_window=FileMan(s.b))
