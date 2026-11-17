# Copyright 2026 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Discord >> @BrotherBoard

"""
Power v3.0.0 - With one click

Adds a dev console tab with some features I find useful.
Power is mainly focused on the multiplayer side.
Can be considered a good tool to have around.
"""

plugman = dict(
    plugin_name="power",
    description=(
        "Adds a dev console tab with some features I find useful. "
        "Power is mainly focused on the multiplayer side. "
        "Can be considered a good tool to have around."
    ),
    external_url="https://BroBordd.github.io/byBordd",
    authors=[
        {
            "name": "BrotherBoard",
            "email": "brobordd@gmail.com",
            "discord": "BrotherBoard",
            "github": "BroBordd"
        },
    ],
    version='3.0.0',
)

from datetime import datetime as DT
from typing import override
from babase import (
    clipboard_is_supported as CIS,
    clipboard_set_text as CST,
    Plugin,
    app
)
from babase._devconsole import (
    DevConsoleTabEntry as ENT,
    DevConsoleTab as TAB
)
from bascenev1 import (
    disconnect_client as DISC,
    get_connection_to_host_info_2 as HOST,
    disconnect_from_host as LEAVE,
    broadcastmessage as push,
    get_chat_messages as GCM,
    connect_to_party as CON,
    get_game_roster as ROST,
    chatmessage as chat
)
from bauiv1 import (
    get_string_width as sw,
    SpecialChar as sc,
    apptimer as teck,
    CallPartial
)

class Power(TAB):
    def __init__(s):
        s.j = [None,None,None]; s.ji = 1
        [setattr(s,_,None) for _ in 'cpnh']
        [setattr(s,_,{}) for _ in ['rr','hi']]
        [setattr(s,_,[]) for _ in ['cm','og','r','ls']]
        [setattr(s,_,0) for _ in ['ii','eii','ci','re','ri','eri','li','lii']]
        s.dk = set(); s.sp = 0; s.vt = None
        s.ld()
        teck(3,s.spy)
    def ld(s):
        c = app.config
        try:
            s.ls = [(str(a),str(b)) for a,b in c.get('pw_logs',[])][-99:]
            s.lii = len(s.ls)
            s.cm = [(str(a),int(b)) for a,b in c.get('pw_chat',[])]
            s.hi = {(str(a),str(b)):(str(a),d) for a,b,d in c.get('pw_servers',[])}
        except Exception:
            s.ls,s.cm,s.hi,s.lii = [],[],{},0
        if s.cm:
            try: s.og = GCM()
            except Exception: pass
    def sv(s,k):
        s.dk.add(k)
        if s.sp: return
        s.sp = 1
        teck(2,s._sv)
    def _sv(s):
        s.sp = 0
        c = app.config
        for k in s.dk:
            if k == 'ls': c['pw_logs'] = [list(_) for _ in s.ls]
            elif k == 'cm': c['pw_chat'] = [list(_) for _ in s.cm[:500]]
            elif k == 'hi': c['pw_servers'] = [[a,b,d] for (a,b),(_,d) in s.hi.items()]
        s.dk.clear()
        try: c.commit()
        except Exception: pass
    def clr(s,k):
        if k == 'ls': s.ls = []; s.li = s.lii = 0
        elif k == 'cm': s.cm = []; s.ci = 0
        elif k == 'hi': s.hi = {}; s.ii = s.eii = 0
        s.sv(k)
        push({'ls':'Logs','cm':'Chat','hi':'Servers'}[k]+' cleared',color=(1,1,0))
        s.rf()
    def rf(s):
        try: s.request_refresh()
        except RuntimeError: pass
    def spy(s):
        _ = 0
        r = ROST()
        if r != s.r:
            s.rr = {i['display_string']:(i['client_id'],i['players']) for i in r}
            s.r = r
            _ = 1
        h = HOST()
        if h != s.h:
            s.ri = 0
            s.h = h
            _ = 1
            t = getattr(s.h, 'name', 'Not in a server')
            a = getattr(s.h, 'address', '127.0.0.1')
            p = getattr(s.h, 'port', '43210')
            if s.h:
                tt = t if t.strip() else '...'
                if t.strip() or not any(key[1] == a for key in s.hi):
                    s.hi[(tt, a)] = (tt, p)
                if tt != '...':
                    if ('...', a) in s.hi:
                        del s.hi[('...', a)]
                s.sv('hi')
        ng = GCM()
        if s.og != ng:
            s.og = ng
            ls = ng[-1]
            ch = s.cm[0][1] if len(s.cm) else 0
            if ch and ls == s.cm[0][0]: s.cm[0] = (ls,ch+1)
            else: s.cm.insert(0,(ls,1))
            if s.ci: s.ci += 1
            s.sv('cm')
            _ = 1
        v = VTARGET()
        if v != s.vt:
            s.vt = v
            _ = 1
        _ and s.rf()
        teck(0.1,s.spy)
    @override
    def refresh(s):
        sf = s.width / 1605.3
        zf = s.height / 648
        x = -s.width/2
        T,B = s.text,s.button
        if len(s.r) and s.ri >= len(s.r): s.ri = len(s.r) - 1
        if len(s.r) and s.eri >= len(s.r): s.eri = len(s.r) - 1
        if s.j[0] == 'JRejoin' and s.ji <= s.re:
            s.ji = s.re + 1
            push('Job time cannot be less than rejoin time\nwhen job is JRejoin. Updated job time to '+str(s.ji),color=(1,1,0))
        if s.height > 100:
            RN = 5
            ay = 546-58.5*(RN-1)-3-35
            sy = ay-10
            gt = sy-10
            gh = (gt-8-20)/5
            gy = lambda j: (gt-gh-j*(gh+5))*zf
            gz = gh*zf
            B(
                sc.UP_ARROW.value,
                pos=(x + 10 * sf, 606*zf),
                size=(280*sf,35*zf),
                disabled=s.eri <= 0,
                call=CallPartial(s.mv,'eri',-1)
            )
            B(
                sc.DOWN_ARROW.value,
                pos=(x + 10 * sf, ay*zf),
                size=(280*sf,35*zf),
                disabled=s.eri >= len(s.r)-RN,
                call=CallPartial(s.mv,'eri',1)
            )
            nt = "No roster detected\nJoin some public party"
            w = GSW(nt)
            0 if len(s.r) else T(
                nt,
                pos=(x + 150 * sf, 495*zf),
                h_align='center',
                v_align='top',
                scale=1 if w<(290*sf) else (290*sf)/w
            )
            for i,z in enumerate(s.rr.items()):
                if i < s.eri: continue
                if i>=(s.eri+RN): break
                n,g = z
                c,p = g
                ry = (546-58.5*(i-s.eri))*zf
                rh = 55.5*zf
                big = ', '.join(str(_['name']) for _ in p) if p else n
                B(
                    '',
                    size=(280 * sf, rh),
                    pos=(x + 10 * sf, ry),
                    style=[['blue','blue_bright'],['purple','purple_bright']][not p][s.c==c],
                    call=CallPartial(s.sel,c,p,n)
                )
                T(
                    big,
                    pos=(x + 150 * sf, ry + rh*(0.65 if p else 0.5)),
                    scale=FIT(big,260*sf)
                )
                p and T(
                    n,
                    pos=(x + 150 * sf, ry + rh*0.27),
                    scale=FIT(n,260*sf,0.55)
                )
            B(
                '',
                size=(280 * sf, 2),
                pos=(x + 10 * sf, sy*zf),
                style='bright'
            )
            bb = s.c is None
            B(
                'Bomb' if bb else (['Client','Host'][s.c==-1]+f' {s.c}'),
                pos=(x + 10 * sf, gy(0)),
                size=(140 * sf, gz),
                disabled=bb,
                call=CallPartial(push,str(s.n))
            )
            B(
                'Mention',
                size=(140 * sf, gz),
                pos=(x + 150 * sf, gy(0)),
                call=CallPartial(chat,str(s.n)),
                disabled=bb
            )
            B(
                'Players',
                size=(140 * sf, gz),
                pos=(x + 10 * sf, gy(1)),
                call=CallPartial(push,'\n'.join([' '.join([f'{i}={j}' for i,j in _.items()]) for _ in s.p]) if s.p else ''),
                disabled=bb or (not s.p)
            )
            B(
                'Kick',
                size=(140 * sf, gz),
                pos=(x + 150 * sf, gy(1)),
                call=CallPartial(KICK,lambda:s.rr[s.n][0]),
                disabled=bb or (s.c==-1)
            )
            B(
                'JKick',
                size=(140 * sf, gz),
                pos=(x + 10 * sf, gy(2)),
                call=CallPartial(s.job,CallPartial(KICK,lambda:s.rr[s.n][0]),['JKick',s.c,s.n]),
                disabled=bb or (s.c==-1) or bool(s.h)
            )
            for _l,_k,_d,_x,_y in [
                ('Clear logs','ls',s.ls,10,gy(3)),
                ('Clear chat','cm',s.cm,150,gy(3)),
                ('Clear servers','hi',s.hi,150,gy(2))
            ]:
                w = GSW(_l)
                B(
                    _l,
                    size=(140 * sf, gz),
                    pos=(x + _x * sf, _y),
                    call=CallPartial(s.clr,_k),
                    disabled=not _d,
                    label_scale=1 if w < 130 * sf else (130 * sf)/w
                )
            vl = VL(s)
            w = GSW(vl)
            B(
                vl,
                size=(280 * sf, gz),
                pos=(x + 10 * sf, gy(4)),
                call=VOTE,
                disabled=not s.h or not s.r,
                label_scale=1 if w < 270 * sf else (270 * sf)/w
            )
            B(
                '',
                size=(2, 635*zf),
                pos=(x + 300 * sf, 5*zf),
                style='bright'
            )
            t = getattr(s.h,'name','Not in a server')
            a = getattr(s.h,'address','127.0.0.1')
            p = getattr(s.h,'port','43210')
            w = GSW(t)
            B(
                t if t.strip() else 'Loading...',
                size=(400 * sf, 35*zf),
                pos=(x + 311 * sf, 606*zf),
                disabled=not s.h,
                label_scale=1 if w < 390 * sf else (390 * sf)/w,
                call=CallPartial(push,f"{t}\nHosted on build {getattr(s.h,'build_number','0')}" if t.strip() else 'Server is still loading...\nIf it remains stuck on this\nthen either party is full, or a network issue.'),
            )
            w = GSW(a)
            B(
                a,
                size=(300 * sf, 35*zf),
                pos=(x + 311 * sf, 568*zf),
                call=CallPartial(COPY,a),
                disabled=not s.h,
                label_scale=1 if w < 290 * sf else (290 * sf)/w
            )
            w = GSW(str(p))
            B(
                str(p),
                size=(97 * sf, 35*zf),
                pos=(x + 614 * sf, 568*zf),
                disabled=not s.h,
                call=CallPartial(COPY,str(p)),
                label_scale=1 if w < 90 * sf else (90 * sf)/w
            )
            B(
                'Leave',
                size=(400 * sf, 35*zf),
                pos=(x + 311 * sf, 530*zf),
                call=LEAVE,
                disabled=not s.h
            )
            B(
                'Rejoin',
                size=(200 * sf, 35*zf),
                pos=(x + 311 * sf, 492*zf),
                call=CallPartial(REJOIN,a,p,lambda:s.re),
                disabled=not s.h
            )
            B(
                'JRejoin',
                size=(197 * sf, 35*zf),
                pos=(x + 514 * sf, 492*zf),
                call=CallPartial(s.job,CallPartial(REJOIN,a,p,lambda:s.re),['JRejoin',a,str(p)]),
                disabled=not s.h
            )
            B(
                '+',
                size=(131 * sf, 35*zf),
                pos=(x + 579 * sf, 454*zf),
                call=CallPartial(s.mv,'re',1)
            )
            B(
                str(s.re or 0.1),
                size=(131 * sf, 35*zf),
                pos=(x + 444 * sf, 454*zf),
                call=CallPartial(push,f"Rejoins after {s.re or 0.1} second{['','s'][s.re!=1]}\nKeep this 0.1 unless server kicks fast rejoins\nLife in server = job time - rejoin time")
            )
            B(
                '-',
                size=(131 * sf, 35*zf),
                pos=(x + 311 * sf, 454*zf),
                disabled=s.re<=0.5,
                call=CallPartial(s.mv,'re',-1)
            )
            B(
                '',
                size=(2, 635*zf),
                pos=(x + 720 * sf, 5*zf),
                style='bright'
            )
            B(
                '',
                size=(400 * sf, 2),
                pos=(x + 311 * sf, 445*zf),
                style='bright'
            )
            for i,e in enumerate(s.hi.items()):
                if i < s.eii: continue
                if i >= (s.eii+9): break
                g,v = e
                _,a = g
                n,p = v
                w = GSW(n)
                B(
                    n,
                    size=(400 * sf, 37*zf),
                    pos=(x + 311 * sf, (358-39*(i-s.eii))*zf),
                    label_scale=1 if w < 290 * sf else (290 * sf)/w,
                    call=CallPartial(JOIN,a,p,False),
                    disabled=n == '...'
                )
            nt = "Server join history\nServers you join are saved here"
            w = GSW(nt)
            0 if len(s.hi) else T(
                nt,
                pos=(x + 510 * sf, 265*zf),
                v_align='top',
                scale=1 if w<(380*sf) else (380*sf)/w
            )
            B(
                sc.DOWN_ARROW.value,
                pos=(x + 311 * sf, 8*zf),
                size=(398*sf, 35*zf),
                disabled=s.eii >= len(s.hi)-9,
                call=CallPartial(s.mv,'eii',1)
            )
            B(
                sc.UP_ARROW.value,
                pos=(x + 311 * sf, 400*zf),
                size=(400*sf, 35*zf),
                disabled=s.eii <= 0,
                call=CallPartial(s.mv,'eii',-1)
            )
            bb = s.j[0] is None
            B(
                'No job' if bb else 'Job',
                size=(300 * sf, 35*zf),
                pos=(x + 727 * sf, 606*zf),
                call=CallPartial(push,s.j[0]),
                disabled=bb
            )
            w = 0 if bb else GSW(str(s.j[1]))
            B(
                'Target' if bb else str(s.j[1]),
                size=(300 * sf, 35*zf),
                pos=(x + 727 * sf, 568*zf),
                call=CallPartial(push,s.j[2]),
                disabled=bb,
                label_scale=1 if w<110 * sf else (110 * sf)/w
            )
            B(
                'Stop',
                size=(300 * sf, 35*zf),
                pos=(x + 727 * sf, 530*zf),
                call=CallPartial(s.job,None,[None,None,None]),
                disabled=bb
            )
            B(
                '+',
                size=(96 * sf, 35*zf),
                pos=(x + 931 * sf, 492*zf),
                call=CallPartial(s.mv,'ji',1)
            )
            B(
                str(s.ji or 0.1),
                size=(100 * sf, 35*zf),
                pos=(x + 828 * sf, 492*zf),
                call=CallPartial(push,f"Job runs every {s.ji or 0.1} second{['','s'][s.ji!=1]}")
            )
            B(
                '-',
                size=(98 * sf, 35*zf),
                pos=(x + 727 * sf, 492*zf),
                disabled=s.ji<=0.5,
                call=CallPartial(s.mv,'ji',-1)
            )
            B(
                'Power',
                size=(300 * sf, 35*zf),
                pos=(x + 727 * sf, 454*zf),
                call=CallPartial(push,'Power v2.5 FullUI\nCollapse dev console to switch to MinUI')
            )
            B(
                '',
                size=(300 * sf, 2),
                pos=(x + 727 * sf, 445*zf),
                style='bright'
            )
            B(
                '',
                size=(2, 635*zf),
                pos=(x + 1034 * sf, 5*zf),
                style='bright'
            )
            0 if len(s.cm) else T(
                'Chat is still empty\nHurry up and fill it with nonesense',
                pos=(x+1320 * sf, 330 * zf)
            )
            for i,g in enumerate(s.cm):
                if i < s.ci: continue
                if i >= s.ci+15: break
                i = i - s.ci
                m,_ = g
                sn,ms = m.split(': ',1)
                w = GSW(sn)
                w = [w,30*sf][w<30*sf]
                s1 = [w,200*sf][w>200*sf]
                B(
                    sn,
                    size=(s1,35*zf),
                    pos=(x + 1040*sf, (48+37*i)*zf),
                    style='purple',
                    label_scale=1 if w<(s1-10*sf) else (s1-10*sf)/w,
                    call=CallPartial(s.chk,sn)
                )
                s2 = 555*sf - s1 - 53*(_>1)
                B(
                    '',
                    size=(s2,35*zf),
                    pos=(x + 1045*sf+s1, (48+37*i)*zf),
                    style='black'
                )
                w = GSW(ms)
                T(
                    ms,
                    pos=(x + s1+(1050)*sf, (48+17+37*i)*zf),
                    scale=1 if w<(s2-10*sf) else (s2-10*sf)/w,
                    h_align='left'
                )
                z = f'x{_}'
                w = GSW(z)
                _>1 and B(
                    z,
                    pos=(x+s1+s2+(1050)*sf,(48+37*i)*zf),
                    size=(50*sf,35*zf),
                    label_scale=1 if w<(40*sf) else (40*sf)/w,
                    style='yellow_bright'
                )
            B(
                sc.DOWN_ARROW.value,
                pos=(x+1042*sf,8*zf),
                size=(555*sf,35*zf),
                call=CallPartial(s.mv,'ci',-1),
                disabled=s.ci <= 0 or not s.cm
            )
            B(
                sc.UP_ARROW.value,
                pos=(x+1042*sf,606*zf),
                size=(555*sf,35*zf),
                call=CallPartial(s.mv,'ci',1),
                disabled=(s.ci >= len(s.cm)-15) or not s.cm
            )
            B(
                sc.DOWN_ARROW.value,
                pos=(x+727*sf,8*zf),
                size=(300*sf,35*zf),
                disabled=(s.li >= len(s.ls)-16) or not s.ls,
                call=CallPartial(s.mv,'li',1)
            )
            B(
                sc.UP_ARROW.value,
                pos=(x+727*sf,400*zf),
                size=(300*sf,35*zf),
                disabled=s.li<=0,
                call=CallPartial(s.mv,'li',-1)
            )
            0 if s.ls else T(
                'Job logs here\nLike you even care',
                pos=(x+875*sf,232*zf)
            )
            for _,g in enumerate(s.ls):
                if _ < s.li: continue
                if _ >= s.li+16: break
                _ = _ - s.li
                l,t = g
                B(
                    '',
                    pos=(x+727*sf,(376-_*22)*zf),
                    size=(300*sf,20*zf),
                    label_scale=0.7,
                    corner_radius=0,
                    style='black',
                    call=CallPartial(push,t)
                )
                T(
                    l,
                    pos=(x+732*sf,(386-_*22)*zf),
                    scale=0.6,
                    h_align='left'
                )
        else:
            B(
                sc.DOWN_ARROW.value,
                pos=(x + 10 * sf, 10),
                size=(30 * sf, s.height-17),
                disabled=(s.ri >= len(s.r)-3) or not s.r,
                call=CallPartial(s.mv,'ri',1)
            )
            B(
                sc.UP_ARROW.value,
                pos=(x + 250 * sf, 10),
                size=(30 * sf, s.height-17),
                disabled=(s.ri <= 0) or not s.r,
                call=CallPartial(s.mv,'ri',-1)
            )
            nt = "No roster\nYou're alone"
            w = GSW(nt)
            0 if len(s.r) else T(
                nt,
                pos=(x + 147 * sf, s.height-17),
                h_align='center',
                v_align='top',
                scale=1 if w<(200*sf) else (200*sf)/w
            )
            for i,z in enumerate(s.rr.items()):
                if i < s.ri: continue
                if i>=(s.ri+3): break
                n,g = z
                c,p = g
                w = GSW(n)
                B(
                    n,
                    size=(210 * sf, 27),
                    pos=(x + 40 * sf, s.height-35-27*(i-s.ri)),
                    style=[['blue','blue_bright'],['purple','purple_bright']][not p][s.c==c],
                    call=CallPartial(s.sel,c,p,n),
                    label_scale=1 if w < 200 * sf else (200 * sf)/w
                )
            bb = s.c is None
            B(
                'Bomb' if bb else (['Client','Host'][s.c==-1]+f' {s.c}'),
                pos=(x + 287 * sf, s.height-34),
                size=(217 * sf, 27),
                disabled=bb,
                call=CallPartial(push,str(s.n))
            )
            B(
                'Kick',
                size=(217 * sf, 27),
                pos=(x + 505 * sf, s.height-34),
                call=CallPartial(KICK,lambda:s.rr[s.n][0]),
                disabled=bb or (s.c==-1)
            )
            B(
                'Mention',
                size=(217 * sf, 27),
                pos=(x + 287 * sf, s.height-62),
                call=CallPartial(chat,str(s.n)),
                disabled=bb
            )
            B(
                'Players',
                size=(217 * sf, 27),
                pos=(x + 505 * sf, s.height-62),
                call=CallPartial(push,'\n'.join([' '.join([f'{i}={j}' for i,j in _.items()]) for _ in s.p]) if s.p else ''),
                disabled=bb or (not s.p)
            )
            vl = VL(s)
            w = GSW(vl)
            B(
                vl,
                size=(435 * sf, 27),
                pos=(x + 287 * sf, s.height-90),
                call=VOTE,
                disabled=not s.h or not s.r,
                label_scale=1 if w < 425 * sf else (425 * sf)/w
            )
            B(
                '',
                size=(2, s.height-17),
                pos=(x + 722 * sf, 10),
                style='bright'
            )
            t = getattr(s.h,'name','Not in a server')
            a = getattr(s.h,'address','127.0.0.1')
            p = getattr(s.h,'port','43210')
            w = GSW(t)
            B(
                t if t.strip() else 'Loading...',
                size=(300 * sf, 27),
                pos=(x + 732 * sf, s.height-34),
                disabled=not s.h,
                label_scale=1 if w < 290 * sf else (290 * sf)/w,
                call=CallPartial(push,f"{t}\nHosted on build {getattr(s.h,'build_number','0')}" if t.strip() else 'Server is still loading...\nIf it remains stuck on this\nthen either party is full, or a network issue.'),
            )
            w = GSW(a)
            B(
                a,
                size=(200 * sf, 27),
                pos=(x + 732 * sf, s.height-62),
                call=CallPartial(COPY,a),
                disabled=not s.h,
                label_scale=1 if w < 190 * sf else (190 * sf)/w
            )
            w = GSW(str(p))
            B(
                str(p),
                size=(97 * sf, 27),
                pos=(x + 935 * sf, s.height-62),
                disabled=not s.h,
                call=CallPartial(COPY,str(p)),
                label_scale=1 if w < 90 * sf else (90 * sf)/w
            )
            B(
                'Leave',
                size=(100 * sf, 27),
                pos=(x + 732 * sf, s.height-90),
                call=LEAVE,
                disabled=not s.h
            )
            B(
                'Rejoin',
                size=(197 * sf, 27),
                pos=(x + 835 * sf, s.height-90),
                call=CallPartial(REJOIN,a,p,lambda:s.re),
                disabled=not s.h
            )
            B(
                '+',
                size=(50 * sf, 27),
                pos=(x + 1035 * sf, s.height-34),
                call=CallPartial(s.mv,'re',1)
            )
            B(
                str(s.re or 0.1),
                size=(50 * sf, 27),
                pos=(x + 1035 * sf, s.height-62),
                call=CallPartial(push,f"Rejoins after {s.re or 0.1} second{['','s'][s.re!=1]}\nKeep this 0.1 unless server kicks fast rejoins\nLife in server = job time - rejoin time")
            )
            B(
                '-',
                size=(50 * sf, 27),
                pos=(x + 1035 * sf, s.height-90),
                disabled=s.re<=0.5,
                call=CallPartial(s.mv,'re',-1)
            )
            B(
                '',
                size=(2, s.height-17),
                pos=(x + 1092 * sf, 10),
                style='bright'
            )
            for i,e in enumerate(s.hi.items()):
                if i < s.ii: continue
                if i >= (s.ii+3): break
                g,v = e
                _,a = g
                n,p = v
                w = GSW(n)
                B(
                    n,
                    size=(300 * sf, 27),
                    pos=(x + 1134 * sf, s.height-34-28*(i-s.ii)),
                    label_scale=1 if w < 290 * sf else (290 * sf)/w,
                    call=CallPartial(JOIN,a,p,False),
                    disabled=n == '...'
                )
            nt = "Your server join history\nwill appear here"
            w = GSW(nt)
            0 if len(s.hi) else T(
                nt,
                pos=(x + 1285 * sf, s.height-17),
                h_align='center',
                v_align='top',
                scale=1 if w<(280*sf) else (280*sf)/w
            )
            B(
                sc.DOWN_ARROW.value,
                pos=(x + 1102 * sf, 10),
                size=(30 * sf, s.height-17),
                disabled=s.ii >= len(s.hi)-3,
                call=CallPartial(s.mv,'ii',1)
            )
            B(
                sc.UP_ARROW.value,
                pos=(x + 1436 * sf, 10),
                size=(30 * sf, s.height-17),
                disabled=s.ii <= 0,
                call=CallPartial(s.mv,'ii',-1)
            )
            B(
                'Force leave',
                call=FORCE,
                pos=(x + 1469 * sf, s.height-34),
                size=(130 * sf, 27),
                label_scale=0.9
            )
            B(
                'gg',
                call=CallPartial(chat,'gg'),
                pos=(x + 1469 * sf, s.height-62),
                size=(130 * sf, 27)
            )
            B(
                'Power',
                call=CallPartial(push,'Power v2.5 MinUI\nExpand dev console to switch to FullUI. thanks.'),
                pos=(x + 1469 * sf, s.height-90),
                size=(130 * sf, 27)
            )
    def log(s,t):
        s.ls.append((t,NOW()))
        if s.lii < 99:
            s.lii += 1
            if s.li == s.lii-17: s.li += 1
        else: s.ls.pop(0)
        s.sv('ls')
        s.rf()
    def mv(s,a,i):
        setattr(s,a,getattr(s,a)+i)
        s.rf()
    def job(s,f,j):
        s.j = j
        s.lf = f
        s.hd = j[1] if s.j[0] == 'JRejoin' else j[2]
        if f is not None:
            s._job(f)
            push('Job started',color=(1,1,0))
        else: push('Job stopped',color=(1,1,0))
        s.rf()
    def _job(s,f):
        if f != s.lf: return
        s.log(f'[{s.lii:02}] [{s.j[0]}] {s.hd}')
        f(); teck(s.ji or 0.1,CallPartial(s._job,f))
    def prv(s,c,p,n):
        s.c,s.p,s.n = c,p,n
        s.rf()
    def sel(s,c,p,n):
        if s.c == c: s.prv(None,None,None)
        else: s.prv(c,p,n)
    def chk(s,pn):
        y = 0
        for n,g in s.rr.items():
            c,p = g
            if n == pn: y = 1
            else:
                for _ in p:
                    if pn in [_['name'],_['name_full']]: y = 1
            if y: s.prv(c,p,n); break

HAS = app.ui_v1.has_main_window
SAVE = app.classic.save_ui_state
VBUILD = 23067
def VOTE():
    if (getattr(HOST(),'build_number',0) or 0) < VBUILD:
        chat('1')
        return
    import bacommon.docui.routes.classichost as hroutes
    from concurrent.futures import Future
    app.classic.host_ui.submit_request(hroutes.KickVoteCast(yes=True).request(),Future())

VL = lambda s: 'Vote'+(f' {s.vt}' if s.vt else '')

def VTARGET():
    h = HOST()
    if h is None or (getattr(h,'build_number',0) or 0) < VBUILD: return None
    try:
        import bacommon.docui.routes.classichost as hroutes
        from bacommon.hostui import ButtonPlacement as BP
        u = app.classic.host_ui
        k = hroutes.KickVote().request().path
        if not any(b.request.path == k for b in u.get_shown_buttons(BP.PARTY_MENU)): return None
        v = u._shown.notice.subs
        return next((i for i in (v.values() if isinstance(v,dict) else v) if isinstance(i,str)),None)
    except Exception: return None

def KICK(f):
    try: c = f()
    except KeyError: return
    u = app.classic.host_ui
    h = HOST()
    if h is None:
        u.kick_votes.kick(c)
        return
    r = u.get_kick_request(c) if (getattr(h,'build_number',0) or 0) >= VBUILD else None
    if r is None:
        DISC(c,ban_time=300) or push('Kick not available',color=(1,0,0))
        return
    from bauiv1lib.hostdocui import show_host_docui_window
    from bacommon.langstr import LangStrSpecValue
    import bacommon.hostui as hui
    import bacommon.docui.v2 as dui2
    import bacommon.docui.routes.classichost as hroutes
    from concurrent.futures import Future
    show_host_docui_window(hui.Button(
        label=LangStrSpecValue.literal(''),
        placement=hui.ButtonPlacement.PARTY_MENU,
        request=r,
        layout=dui2.WindowLayout.WIDE
    ))
    if r.path == hroutes.KickVote().request().path:
        teck(0.3,lambda: u.submit_request(hroutes.KickVoteStart(client_id=c).request(),Future()))

FORCE = lambda: teck(0.7 if HAS() else 0.1,lambda: 0 if HAS() else app.classic.return_to_main_menu_session_gracefully())
JOIN = lambda *a: (SAVE() or 1) and CON(*a)
def GSW(s):
    try: return sw(s,suppress_warning=True,suppress_logic_thread_warning=True)
    except TypeError: return sw(s,suppress_warning=True)
def FIT(t,lim,mx=1.0):
    w = GSW(t)
    return mx if w*mx <= lim else lim/w
REJOIN = lambda a,p,f: ((LEAVE() if getattr(HOST(),'name','') else 0) or 1) and teck(f() or 0.1,CallPartial(JOIN,a,p,False))
COPY = lambda s: ((CST(s) or 1) if CIS() else push('Clipboard not supported!')) and push('Copied!',color=(0,1,0))
NOW = lambda: DT.now().strftime("%H:%M:%S")

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    def __init__(s):
        C = Power
        N = C.__name__
        E = ENT(N,C)
        I = app.devconsole
        I.tabs = [_ for _ in I.tabs if _.name != N]+[E]
        I._tab_instances[N] = E.factory()
