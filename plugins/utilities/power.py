# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @GalaxyA14user

"""
Power v2.7 - With one click

Experimental. Feedback is appreciated.
Adds a dev console tab with some features I find useful.
Power is mainly focused on the multiplayer side.
Can be considered a good tool to have around.
"""

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
    get_connection_to_host_info_2 as HOST,
    disconnect_from_host as LEAVE,
    disconnect_client as DISC,
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
    charstr as cs,
    Call
)


class Power(TAB):
    def __init__(s):
        s.j = [None, None, None]
        s.ji = 1
        [setattr(s, _, None) for _ in 'cpnh']
        [setattr(s, _, {}) for _ in ['rr', 'hi']]
        [setattr(s, _, []) for _ in ['cm', 'og', 'r', 'ls']]
        [setattr(s, _, 0) for _ in ['ii', 'eii', 'ci', 're', 'ri', 'eri', 'li', 'lii']]
        teck(3, s.spy)

    def rf(s):
        try:
            s.request_refresh()
        except RuntimeError:
            pass

    def spy(s):
        _ = 0
        r = ROST()
        if r != s.r:
            s.rr = {i['display_string']: (i['client_id'], i['players']) for i in r}
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
        ng = GCM()
        if s.og != ng:
            s.og = ng
            ls = ng[-1]
            ch = s.cm[0][1] if len(s.cm) else 0
            if ch and ls == s.cm[0][0]:
                s.cm[0] = (ls, ch+1)
            else:
                s.cm.insert(0, (ls, 1))
            if s.ci:
                s.ci += 1
            _ = 1
        _ and s.rf()
        teck(0.1, s.spy)

    @override
    def refresh(s):
        sf = s.width / 1605.3
        zf = s.height / 648
        x = -s.width/2
        T, B = s.text, s.button
        if len(s.r) and s.ri >= len(s.r):
            s.ri = len(s.r) - 1
        if len(s.r) and s.eri >= len(s.r):
            s.eri = len(s.r) - 1
        if s.j[0] == 'JRejoin' and s.ji <= s.re:
            s.ji = s.re + 1
            push('Job time cannot be less than rejoin time\nwhen job is JRejoin. Updated job time to ' +
                 str(s.ji), color=(1, 1, 0))
        if s.height > 100:
            B(
                cs(sc.UP_ARROW),
                pos=(x + 10 * sf, 606*zf),
                size=(280*sf, 35*zf),
                disabled=s.eri <= 0,
                call=Call(s.mv, 'eri', -1)
            )
            B(
                cs(sc.DOWN_ARROW),
                pos=(x + 10 * sf, 290*zf),
                size=(280*sf, 35*zf),
                disabled=s.eri >= len(s.r)-7,
                call=Call(s.mv, 'eri', 1)
            )
            nt = "No roster detected\nJoin some public party"
            w = GSW(nt)
            0 if len(s.r) else T(
                nt,
                pos=(x + 150 * sf, 495*zf),
                h_align='center',
                v_align='top',
                scale=1 if w < (290*sf) else (290*sf)/w
            )
            for i, z in enumerate(s.rr.items()):
                if i < s.eri:
                    continue
                if i >= (s.eri+7):
                    break
                n, g = z
                c, p = g
                w = GSW(n)
                B(
                    n,
                    size=(280 * sf, 37*zf),
                    pos=(x + 10 * sf, (564-39*(i-s.eri))*zf),
                    style=[['blue', 'blue_bright'], ['purple', 'purple_bright']][not p][s.c == c],
                    call=Call(s.prv, c, p, n),
                    label_scale=1 if w < 280 * sf else (280 * sf)/w
                )
            B(
                '',
                size=(280 * sf, 2),
                pos=(x + 10 * sf, 280*zf),
                style='bright'
            )
            bb = s.c is None
            B(
                'Bomb' if bb else (['Client', 'Host'][s.c == -1]+f' {s.c}'),
                pos=(x + 10 * sf, 230*zf),
                size=(280 * sf, 40*zf),
                disabled=bb,
                call=Call(push, str(s.n))
            )
            B(
                'Mention',
                size=(280 * sf, 40*zf),
                pos=(x + 10 * sf, 185*zf),
                call=Call(chat, str(s.n)),
                disabled=bb
            )
            B(
                'Players',
                size=(280 * sf, 40*zf),
                pos=(x + 10 * sf, 140*zf),
                call=Call(push, '\n'.join(
                    [' '.join([f'{i}={j}' for i, j in _.items()]) for _ in s.p]) if s.p else ''),
                disabled=bb or (not s.p)
            )
            B(
                'Kick',
                size=(280 * sf, 40*zf),
                pos=(x + 10 * sf, 95*zf),
                call=Call(KICK, lambda: s.rr[s.n][0]),
                disabled=bb or (s.c == -1)
            )
            B(
                'JKick',
                size=(280 * sf, 40*zf),
                pos=(x + 10 * sf, 50*zf),
                call=Call(s.job, Call(KICK, lambda: s.rr[s.n][0]), ['JKick', s.c, s.n]),
                disabled=bb or (s.c == -1)
            )
            B(
                'Vote',
                size=(280 * sf, 40*zf),
                pos=(x + 10 * sf, 5*zf),
                call=Call(chat, '1'),
                disabled=not s.r
            )
            B(
                '',
                size=(2, 635*zf),
                pos=(x + 300 * sf, 5*zf),
                style='bright'
            )
            t = getattr(s.h, 'name', 'Not in a server')
            a = getattr(s.h, 'address', '127.0.0.1')
            p = getattr(s.h, 'port', '43210')
            w = GSW(t)
            B(
                t if t.strip() else 'Loading...',
                size=(400 * sf, 35*zf),
                pos=(x + 311 * sf, 606*zf),
                disabled=not s.h,
                label_scale=1 if w < 390 * sf else (390 * sf)/w,
                call=Call(push, f"{t}\nHosted on build {getattr(s.h, 'build_number', '0')}" if t.strip(
                ) else 'Server is still loading...\nIf it remains stuck on this\nthen either party is full, or a network issue.'),
            )
            w = GSW(a)
            B(
                a,
                size=(300 * sf, 35*zf),
                pos=(x + 311 * sf, 568*zf),
                call=Call(COPY, a),
                disabled=not s.h,
                label_scale=1 if w < 290 * sf else (290 * sf)/w
            )
            w = GSW(str(p))
            B(
                str(p),
                size=(97 * sf, 35*zf),
                pos=(x + 614 * sf, 568*zf),
                disabled=not s.h,
                call=Call(COPY, str(p)),
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
                call=Call(REJOIN, a, p, lambda: s.re),
                disabled=not s.h
            )
            B(
                'JRejoin',
                size=(197 * sf, 35*zf),
                pos=(x + 514 * sf, 492*zf),
                call=Call(s.job, Call(REJOIN, a, p, lambda: s.re), ['JRejoin', a, str(p)]),
                disabled=not s.h
            )
            B(
                '+',
                size=(131 * sf, 35*zf),
                pos=(x + 579 * sf, 454*zf),
                call=Call(s.mv, 're', 1)
            )
            B(
                str(s.re or 0.1),
                size=(131 * sf, 35*zf),
                pos=(x + 444 * sf, 454*zf),
                call=Call(
                    push, f"Rejoins after {s.re or 0.1} second{['', 's'][s.re != 1]}\nKeep this 0.1 unless server kicks fast rejoins\nLife in server = job time - rejoin time")
            )
            B(
                '-',
                size=(131 * sf, 35*zf),
                pos=(x + 311 * sf, 454*zf),
                disabled=s.re <= 0.5,
                call=Call(s.mv, 're', -1)
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
            for i, e in enumerate(s.hi.items()):
                if i < s.eii:
                    continue
                if i >= (s.eii+9):
                    break
                g, v = e
                _, a = g
                n, p = v
                w = GSW(n)
                B(
                    n,
                    size=(400 * sf, 37*zf),
                    pos=(x + 311 * sf, (358-39*(i-s.eii))*zf),
                    label_scale=1 if w < 290 * sf else (290 * sf)/w,
                    call=Call(JOIN, a, p, False),
                    disabled=n == '...'
                )
            nt = "Server join history\nServers you join are saved here"
            w = GSW(nt)
            0 if len(s.hi) else T(
                nt,
                pos=(x + 510 * sf, 265*zf),
                v_align='top',
                scale=1 if w < (380*sf) else (380*sf)/w
            )
            B(
                cs(sc.DOWN_ARROW),
                pos=(x + 311 * sf, 8*zf),
                size=(398*sf, 35*zf),
                disabled=s.eii >= len(s.hi)-9,
                call=Call(s.mv, 'eii', 1)
            )
            B(
                cs(sc.UP_ARROW),
                pos=(x + 311 * sf, 400*zf),
                size=(400*sf, 35*zf),
                disabled=s.eii <= 0,
                call=Call(s.mv, 'eii', -1)
            )
            bb = s.j[0] is None
            B(
                'No job' if bb else 'Job',
                size=(300 * sf, 35*zf),
                pos=(x + 727 * sf, 606*zf),
                call=Call(push, s.j[0]),
                disabled=bb
            )
            w = 0 if bb else GSW(str(s.j[1]))
            B(
                'Target' if bb else str(s.j[1]),
                size=(300 * sf, 35*zf),
                pos=(x + 727 * sf, 568*zf),
                call=Call(push, s.j[2]),
                disabled=bb,
                label_scale=1 if w < 110 * sf else (110 * sf)/w
            )
            B(
                'Stop',
                size=(300 * sf, 35*zf),
                pos=(x + 727 * sf, 530*zf),
                call=Call(s.job, None, [None, None, None]),
                disabled=bb
            )
            B(
                '+',
                size=(96 * sf, 35*zf),
                pos=(x + 931 * sf, 492*zf),
                call=Call(s.mv, 'ji', 1)
            )
            B(
                str(s.ji or 0.1),
                size=(100 * sf, 35*zf),
                pos=(x + 828 * sf, 492*zf),
                call=Call(push, f"Job runs every {s.ji or 0.1} second{['', 's'][s.ji != 1]}")
            )
            B(
                '-',
                size=(98 * sf, 35*zf),
                pos=(x + 727 * sf, 492*zf),
                disabled=s.ji <= 0.5,
                call=Call(s.mv, 'ji', -1)
            )
            B(
                'Power',
                size=(300 * sf, 35*zf),
                pos=(x + 727 * sf, 454*zf),
                call=Call(push, 'Power v2.5 FullUI\nCollapse dev console to switch to MinUI')
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
                'Chat is still empty.\nHurry up and fill it with nonesense',
                pos=(x+1320 * sf, 330 * zf)
            )
            for i, g in enumerate(s.cm):
                if i < s.ci:
                    continue
                if i >= s.ci+15:
                    break
                i = i - s.ci
                m, _ = g
                sn, ms = m.split(': ', 1)
                w = GSW(sn)
                w = [w, 30*sf][w < 30*sf]
                s1 = [w, 200*sf][w > 200*sf]
                B(
                    sn,
                    size=(s1, 35*zf),
                    pos=(x + 1040*sf, (48+37*i)*zf),
                    style='purple',
                    label_scale=1 if w < (s1-10*sf) else (s1-10*sf)/w,
                    call=Call(s.chk, sn)
                )
                s2 = 555*sf - s1 - 53*(_ > 1)
                B(
                    '',
                    size=(s2, 35*zf),
                    pos=(x + 1045*sf+s1, (48+37*i)*zf),
                    style='black'
                )
                w = GSW(ms)
                T(
                    ms,
                    pos=(x + s1+(1050)*sf, (48+17+37*i)*zf),
                    scale=1 if w < (s2-10*sf) else (s2-10*sf)/w,
                    h_align='left'
                )
                z = f'x{_}'
                w = GSW(z)
                _ > 1 and B(
                    z,
                    pos=(x+s1+s2+(1050)*sf, (48+37*i)*zf),
                    size=(50*sf, 35*zf),
                    label_scale=1 if w < (40*sf) else (40*sf)/w,
                    style='yellow_bright'
                )
            B(
                cs(sc.DOWN_ARROW),
                pos=(x+1042*sf, 8*zf),
                size=(555*sf, 35*zf),
                call=Call(s.mv, 'ci', -1),
                disabled=s.ci <= 0 or not s.cm
            )
            B(
                cs(sc.UP_ARROW),
                pos=(x+1042*sf, 606*zf),
                size=(555*sf, 35*zf),
                call=Call(s.mv, 'ci', 1),
                disabled=(s.ci >= len(s.cm)-15) or not s.cm
            )
            B(
                cs(sc.DOWN_ARROW),
                pos=(x+727*sf, 8*zf),
                size=(300*sf, 35*zf),
                disabled=(s.li >= len(s.ls)-16) or not s.ls,
                call=Call(s.mv, 'li', 1)
            )
            B(
                cs(sc.UP_ARROW),
                pos=(x+727*sf, 400*zf),
                size=(300*sf, 35*zf),
                disabled=s.li <= 0,
                call=Call(s.mv, 'li', -1)
            )
            0 if s.ls else T(
                'Job logs here\nLike you even care',
                pos=(x+875*sf, 232*zf)
            )
            for _, g in enumerate(s.ls):
                if _ < s.li:
                    continue
                if _ >= s.li+16:
                    break
                _ = _ - s.li
                l, t = g
                B(
                    '',
                    pos=(x+727*sf, (376-_*22)*zf),
                    size=(300*sf, 20*zf),
                    label_scale=0.7,
                    corner_radius=0,
                    style='black',
                    call=Call(push, t)
                )
                T(
                    l,
                    pos=(x+732*sf, (386-_*22)*zf),
                    scale=0.6,
                    h_align='left'
                )
        else:
            B(
                cs(sc.DOWN_ARROW),
                pos=(x + 10 * sf, 10),
                size=(30 * sf, s.height-17),
                disabled=(s.ri >= len(s.r)-3) or not s.r,
                call=Call(s.mv, 'ri', 1)
            )
            B(
                cs(sc.UP_ARROW),
                pos=(x + 250 * sf, 10),
                size=(30 * sf, s.height-17),
                disabled=(s.ri <= 0) or not s.r,
                call=Call(s.mv, 'ri', -1)
            )
            nt = "No roster\nYou're alone"
            w = GSW(nt)
            0 if len(s.r) else T(
                nt,
                pos=(x + 147 * sf, s.height-17),
                h_align='center',
                v_align='top',
                scale=1 if w < (200*sf) else (200*sf)/w
            )
            for i, z in enumerate(s.rr.items()):
                if i < s.ri:
                    continue
                if i >= (s.ri+3):
                    break
                n, g = z
                c, p = g
                w = GSW(n)
                B(
                    n,
                    size=(210 * sf, 27),
                    pos=(x + 40 * sf, s.height-35-27*(i-s.ri)),
                    style=[['blue', 'blue_bright'], ['purple', 'purple_bright']][not p][s.c == c],
                    call=Call(s.prv, c, p, n),
                    label_scale=1 if w < 200 * sf else (200 * sf)/w
                )
            bb = s.c is None
            B(
                'Bomb' if bb else (['Client', 'Host'][s.c == -1]+f' {s.c}'),
                pos=(x + 287 * sf, s.height-34),
                size=(120 * sf, 27),
                disabled=bb,
                call=Call(push, str(s.n))
            )
            B(
                'Mention',
                size=(120 * sf, 27),
                pos=(x + 287 * sf, s.height-90),
                call=Call(chat, str(s.n)),
                disabled=bb
            )
            B(
                'Players',
                size=(120 * sf, 27),
                pos=(x + 287 * sf, s.height-62),
                call=Call(push, '\n'.join(
                    [' '.join([f'{i}={j}' for i, j in _.items()]) for _ in s.p]) if s.p else ''),
                disabled=bb or (not s.p)
            )
            B(
                'Kick',
                size=(120 * sf, 27),
                pos=(x + 407 * sf, s.height-34),
                call=Call(KICK, lambda: s.rr[s.n][0]),
                disabled=bb or (s.c == -1)
            )
            B(
                'JKick',
                size=(120 * sf, 27),
                pos=(x + 407 * sf, s.height-62),
                call=Call(s.job, Call(KICK, lambda: s.rr[s.n][0]), ['JKick', s.c, s.n]),
                disabled=bb or (s.c == -1)
            )
            B(
                'Vote',
                size=(120 * sf, 27),
                pos=(x + 407 * sf, s.height-90),
                call=Call(chat, '1'),
                disabled=not s.r
            )
            B(
                '',
                size=(2, s.height-17),
                pos=(x + 535 * sf, 10),
                style='bright'
            )
            bb = s.j[0] is None
            B(
                'No job' if bb else 'Job',
                size=(120 * sf, 27),
                pos=(x + 544 * sf, s.height-34),
                call=Call(push, s.j[0]),
                disabled=bb
            )
            w = 0 if bb else GSW(str(s.j[1]))
            B(
                'Target' if bb else str(s.j[1]),
                size=(120 * sf, 27),
                pos=(x + 544 * sf, s.height-62),
                call=Call(push, s.j[2]),
                disabled=bb,
                label_scale=1 if w < 110 * sf else (110 * sf)/w
            )
            B(
                'Stop',
                size=(120 * sf, 27),
                pos=(x + 544 * sf, s.height-90),
                call=Call(s.job, None, [None, None, None]),
                disabled=bb
            )
            B(
                '+',
                size=(50 * sf, 27),
                pos=(x + 664 * sf, s.height-34),
                call=Call(s.mv, 'ji', 1)
            )
            B(
                str(s.ji or 0.1),
                size=(50 * sf, 27),
                pos=(x + 664 * sf, s.height-62),
                call=Call(push, f"Job runs every {s.ji or 0.1} second{['', 's'][s.ji != 1]}")
            )
            B(
                '-',
                size=(50 * sf, 27),
                pos=(x + 664 * sf, s.height-90),
                disabled=s.ji <= 0.5,
                call=Call(s.mv, 'ji', -1)
            )
            B(
                '',
                size=(2, s.height-17),
                pos=(x + 722 * sf, 10),
                style='bright'
            )
            t = getattr(s.h, 'name', 'Not in a server')
            a = getattr(s.h, 'address', '127.0.0.1')
            p = getattr(s.h, 'port', '43210')
            w = GSW(t)
            B(
                t if t.strip() else 'Loading...',
                size=(300 * sf, 27),
                pos=(x + 732 * sf, s.height-34),
                disabled=not s.h,
                label_scale=1 if w < 290 * sf else (290 * sf)/w,
                call=Call(push, f"{t}\nHosted on build {getattr(s.h, 'build_number', '0')}" if t.strip(
                ) else 'Server is still loading...\nIf it remains stuck on this\nthen either party is full, or a network issue.'),
            )
            w = GSW(a)
            B(
                a,
                size=(200 * sf, 27),
                pos=(x + 732 * sf, s.height-62),
                call=Call(COPY, a),
                disabled=not s.h,
                label_scale=1 if w < 190 * sf else (190 * sf)/w
            )
            w = GSW(str(p))
            B(
                str(p),
                size=(97 * sf, 27),
                pos=(x + 935 * sf, s.height-62),
                disabled=not s.h,
                call=Call(COPY, str(p)),
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
                size=(97 * sf, 27),
                pos=(x + 835 * sf, s.height-90),
                call=Call(REJOIN, a, p, lambda: s.re),
                disabled=not s.h
            )
            B(
                'JRejoin',
                size=(97 * sf, 27),
                pos=(x + 935 * sf, s.height-90),
                call=Call(s.job, Call(REJOIN, a, p, lambda: s.re), ['JRejoin', a, str(p)]),
                disabled=not s.h
            )
            B(
                '+',
                size=(50 * sf, 27),
                pos=(x + 1035 * sf, s.height-34),
                call=Call(s.mv, 're', 1)
            )
            B(
                str(s.re or 0.1),
                size=(50 * sf, 27),
                pos=(x + 1035 * sf, s.height-62),
                call=Call(
                    push, f"Rejoins after {s.re or 0.1} second{['', 's'][s.re != 1]}\nKeep this 0.1 unless server kicks fast rejoins\nLife in server = job time - rejoin time")
            )
            B(
                '-',
                size=(50 * sf, 27),
                pos=(x + 1035 * sf, s.height-90),
                disabled=s.re <= 0.5,
                call=Call(s.mv, 're', -1)
            )
            B(
                '',
                size=(2, s.height-17),
                pos=(x + 1092 * sf, 10),
                style='bright'
            )
            for i, e in enumerate(s.hi.items()):
                if i < s.ii:
                    continue
                if i >= (s.ii+3):
                    break
                g, v = e
                _, a = g
                n, p = v
                w = GSW(n)
                B(
                    n,
                    size=(300 * sf, 27),
                    pos=(x + 1134 * sf, s.height-34-28*(i-s.ii)),
                    label_scale=1 if w < 290 * sf else (290 * sf)/w,
                    call=Call(JOIN, a, p, False),
                    disabled=n == '...'
                )
            nt = "Your server join history\nwill appear here. Hi."
            w = GSW(nt)
            0 if len(s.hi) else T(
                nt,
                pos=(x + 1285 * sf, s.height-17),
                h_align='center',
                v_align='top',
                scale=1 if w < (280*sf) else (280*sf)/w
            )
            B(
                cs(sc.DOWN_ARROW),
                pos=(x + 1102 * sf, 10),
                size=(30 * sf, s.height-17),
                disabled=s.ii >= len(s.hi)-3,
                call=Call(s.mv, 'ii', 1)
            )
            B(
                cs(sc.UP_ARROW),
                pos=(x + 1436 * sf, 10),
                size=(30 * sf, s.height-17),
                disabled=s.ii <= 0,
                call=Call(s.mv, 'ii', -1)
            )
            B(
                'Force leave',
                call=FORCE,
                pos=(x + 1469 * sf, s.height-34),
                size=(130 * sf, 27),
                label_scale=0.9
            )
            B(
                'Laugh',
                call=Call(chat, 'hahaha'),
                pos=(x + 1469 * sf, s.height-62),
                size=(130 * sf, 27)
            )
            B(
                'Power',
                call=Call(push, 'Power v2.5 MinUI\nExpand dev console to switch to FullUI. thanks.'),
                pos=(x + 1469 * sf, s.height-90),
                size=(130 * sf, 27)
            )

    def log(s, t):
        s.ls.append((t, NOW()))
        if s.lii < 99:
            s.lii += 1
            if s.li == s.lii-17:
                s.li += 1
        else:
            s.ls.pop(0)
        s.rf()

    def mv(s, a, i):
        setattr(s, a, getattr(s, a)+i)
        s.rf()

    def job(s, f, j):
        s.j = j
        s.lf = f
        s.hd = j[1] if s.j[0] == 'JRejoin' else j[2]
        if f is not None:
            s._job(f)
            push('Job started', color=(1, 1, 0))
        else:
            push('Job stopped', color=(1, 1, 0))
        s.rf()

    def _job(s, f):
        if f != s.lf:
            return
        s.log(f'[{s.lii:02}] [{s.j[0]}] {s.hd}')
        f()
        teck(s.ji or 0.1, Call(s._job, f))

    def prv(s, c, p, n):
        s.c, s.p, s.n = c, p, n
        s.rf()

    def chk(s, pn):
        y = 0
        for n, g in s.rr.items():
            c, p = g
            if n == pn:
                y = 1
            else:
                for _ in p:
                    if pn in [_['name'], _['name_full']]:
                        y = 1
            if y:
                s.prv(c, p, n)
                break


HAS = app.ui_v1.has_main_window
SAVE = app.classic.save_ui_state
def KICK(f): return DISC(f())


def FORCE(): return teck(0.7 if HAS() else 0.1, lambda: 0 if HAS()
                         else app.classic.return_to_main_menu_session_gracefully())


JOIN = lambda *a: (SAVE() or 1) and CON(*a)
def GSW(s): return sw(s, suppress_warning=True)


def REJOIN(a, p, f): return ((LEAVE() if getattr(HOST(), 'name', '') else 0)
                             or 1) and teck(f() or 0.1, Call(JOIN, a, p, False))
def COPY(s): return ((CST(s) or 1) if CIS() else push(
    'Clipboard not supported!')) and push('Copied!', color=(0, 1, 0))


def NOW(): return DT.now().strftime("%H:%M:%S")

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin


class byBordd(Plugin):
    def __init__(s):
        C = Power
        N = C.__name__
        E = ENT(N, C)
        I = app.devconsole
        I.tabs = [_ for _ in I.tabs if _.name != N]+[E]
        I._tab_instances[N] = E.factory()
