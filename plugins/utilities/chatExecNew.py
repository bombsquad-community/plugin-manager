# ba_meta require api 7

#当前支持的炸队版本 1.7.15+
#Currently supported game versions 1.7.15 +

#更新时间 2023年1月26日
# Updated January 26, 2023

#V 1.2.1 FIX

#By wsdx233
#QQ1284321744
#gitee: https://gitee.com/wsdx233/bombsquad-chat-command/

from random import randint
import ba
import _ba
import os
import sys
from bastd.ui.fileselector import FileSelectorWindow
from bastd.ui.party import *
from efro.error import CleanError
import urllib
import json
import inspect
import threading

from bastd.actor.spazbot import *
from bastd.actor.spaz import *
from bastd.actor.playerspaz import *
from bastd.actor.bomb import *
from bastd.game import *
from bastd.gameutils import SharedObjects
import bastd

if TYPE_CHECKING:
    from typing import List, Sequence, Optional, Dict, Any

#import ba._hooks

#python directories
_env = _ba.env()
pdir = _env["python_directory_user"]
adir = _env["python_directory_app"]


#chinese document
#########
_d_help_doc = {
    'main':"炸队指令MOD 简明帮助\n### 主文档 ###\n\n1.这个mod有什么用？\nA:此mod可以修改炸队的绝大部分内容，可用扩展游戏体验\n\n2.这个mod怎么用？\nA:通过查看炸队源代码和本mod源码（尤其是class D:），你将会得到答案（请先学会Python）\n\n3.请给我几个实例\nA:以下为简单的指令实例:\n#获取当前玩家血量\n/d.cfp().actor.hitpoints\n\n#修改当前玩家炸弹类型(为TNT)\n~d.cfp().actor.bomb_type = \'tnt\'\n\n#修改最大玩家数量\n~d.fs().max_players = 10000\n\n### 使用/help xxx 查看更多帮助",
    'func':"""""",
    'var':"""""",
    'file':"""""",
    'command':"""""",
    'about':"""""",
}

def _d_help(d,args = None):
    d.p("帮助:")
    if not args:
        d.p("输入以下指令查看帮助:")
        d.p("help main: 查看主帮助文档")
        
        d.p("help func: 查看函数文档")
        d.p("help var: 查看变量文档")
        d.p("help file: 查看文档")
        d.p("help command: 查看指令文档")
        d.p("help about: 查看关于文档")

        d.p("by wsdx233 qq:1284321744")
    
    action = args[0]
    d.alp(_d_help_doc[action] if (action in _d_help_doc) else "错误！没有 '%s' 文档！" % action)

#Tool for automatically networking and obtaining instruction
class AutoCommandChecker(threading.Thread):
    def run(self):
        import ba
        import urllib
        d = D =  ba.D
        c = urllib.request.urlopen("https://gitee.com/wsdx233/bombsquad-chat-command/raw/master/commands.json")
        if c.code == 200:
            b = c.read()
            info = json.loads(b)
            
            for k,v in info.items():
                d.commands[k] = v
            
            d.si("Wsdx:已从服务器获取%d条指令！" % len(info))
            
            return
        else:
            return

#网络请求工具
#Network Request Tool
class HttpGetter(threading.Thread):
    
    def __init__(self,url,event):
        super().__init__()
        self.url = url
        self.event = event
        self.context = ba.Context("ui")
        self.start()

    def run(self):
        import ba
        import urllib
        d = D =  ba.D
        c = urllib.request.urlopen(self.url)
        ba.DS.append({
            'event' : lambda d: self.event(c.code,c.read())
        })
        

#Main class for managing debugging
#and processing instructions, linking instructions, and games
class D:

    commands = {
        "help" : _d_help
    }
    
    opened = True
    fopened = False

    show_error = True
    
    #被封禁的 cid
    baned = []
    
    
    history = ['','','~d.cfp().actor','~d.g()','~d.s()']
    version_code = 3

    #Activity
    #获取当前Activity
    def a() -> ba.Activity:
        """Activity 获取当前Activity"""
        return _ba.get_foreground_host_activity()
    #AddCommand
    #新增命令
    def ac(name,handler,info = None):
        if isinstance(name,list):
            for e in name:
                D.ac(e,handler)
            return
        D.commands[name] = handler
    #Foreground Session
    #获取当前Session
    def fs():
        return _ba.get_foreground_host_session()
    #Screen Message
    #弹出屏幕消息
    def s(*s,**kwargs):
    
        #默认传输屏幕信息!
        if not "transient" in kwargs:
            kwargs["transient"] = True
        
        if not isinstance(s[0],str):
            s = list(s)
            s[0] = str(s[0])
        ba.screenmessage(*s,**kwargs)
    
    #Class
    def cls(pack,name):
        exec("from "+pack+" import "+name+" as p\nD.tempp = p")
        return D.tempp
    
    #For Do
    #循环执行
    def f(i,f,l):
        for id in range(i) :
            if l:
                f(id)
            else:
                f()
    #with Context Execute
    #在上下文环境中执行
    def ce(c):
        with ba.Context(d.a() if d.a() else "current"):
          D.te(c)
    
    #Load Function
    #加载函数到Debbuger类
    def lf(n,c):
        D.te("def MT():\n "+c.replace("\n","\n ")+"\nD."+n+"=MT")
    
    #For Execute
    #循环执行
    def fe(i,s):
        for id in range(i):
            D.alp(eval(s))
    #Print
    #在聊天框打印（输出）信息
    def p(s):
        with ba.Context('ui'):
            if isinstance(s,list):
                for i in s:
                    ba._hooks.local_chat_message(i)
                return
            ba._hooks.local_chat_message(str(s))
    
    #Lines Print
    #聊天框打印多行消息
    def lp(s):
        for ls in str(s).split('\n'):
            D.p(ls)
    
    #Auto Lines Print
    #打印自动换行消息
    def alp(s,n = 80):
    
        D.lp(D.mls(s,n))
    
    
    #Send Internet Message
    #发送信息（联网）
    def si(s):
        _ba.chatmessage(str(s))
    #Mod Method
    #（在原方法执行前）修改/MOD方法
    def mm(pack,name,old,code):
        
        INDEX = str(randint(1,100000000))
        
        exec("from "+pack+" import *\n"+
              "def NMT(self):\n"+
              "    "+code+"\n"+
              "    self.YMT"+INDEX+"()\n"+
              +name+".YMT"+INDEX+" = "+name+"."+old+"\n"+name+"."+old+" = NMT")
    #Mod Method Behind
    #在原方法执行后附加修改/MOD方法（执行顺序不同）
    def mmb(pack,name,old,code):
        INDEX = str(randint(1,100000000))
        exec("from "+pack+" import *\ndef NMT(self):\n    self.YMT"+INDEX+"()\n    "+code+"\n"+name+".YMT"+INDEX+" = "+name+"."+old+"\n"+name+"."+old+" = NMT")
    #Mod Method with Any Argument
    #任意参数修改方法（原方法前）
    def mmaa(pack,name,old,code):
        INDEX = str(randint(1,100000000))
        exec("from "+pack+" import *\ndef NMT(self,*args,**kargs):\n    "+code+"\n    self.YMT"+INDEX+"(*args,**kargs)\n"+name+".YMT"+INDEX+" = "+name+"."+old+"\n"+name+"."+old+" = NMT")
    #Set Method with Any Argument
    #任意参数修改方法（原方法前）
    def smaa(pack,name,old,code):
        INDEX = str(randint(1,100000000))
        exec("from "+pack+" import *\ndef NMT(self,*args,**kargs):\n    "+code+"\n"+name+".YMT"+INDEX+" = "+name+"."+old+"\n"+name+"."+old+" = NMT")
    #mod Behind Method with Any Argument
    #任意参数修改方法（原方法前）
    def bmaa(pack,name,old,code):
        INDEX = str(randint(1,100000000))
        exec("from "+pack+" import *\ndef NMT(self,*args,**kargs):\n"+"    self.YMT"+INDEX+"(*args,**kargs)\n    "+code+"\n"+name+".YMT"+INDEX+" = "+name+"."+old+"\n"+name+"."+old+" = NMT")
    #Set Method with Arguments
    #带参数设置方法
    def sma(pack,name,old,arg,code):
        INDEX = str(randint(1,100000000))
        exec("from "+pack+" import *\ndef NMT(self,"+arg+"):\n    "+code+"\n"+name+".YMT"+INDEX+" = "+name+"."+old+"\n"+name+"."+old+" = NMT")
    #Set Method
    #设置方法
    def sm(pack,name,old,code):
        INDEX = str(randint(1,100000000))
        exec("from "+pack+" import *\ndef NMT(self):\n    "+code+"\n"+name+".YMT"+INDEX+" = "+name+"."+old+"\n"+name+"."+old+" = NMT")
    #Set Attribute
    #设置属性
    def sa(pack,name,attr,new):
        exec("from "+pack+" import *\n"+name+"."+attr+"="+new)
    #Cast Dir To
    #输出转换Dir结果到文件
    def cdt(obj,to):
        open(to,'w').write(str(dir(obj)).replace(",","\n"))
    
    #mod
    #修改方法
    def mod(obj,name,_by):
        _old = getattr(obj,name)
        def doit(*a,**ka):
            _by(_old,*a,**ka)
        
        setattr(obj,name,doit)

    #MessageEdit
    #修改Message
    def me(msg,by):
        def initpro(*a,**ka):
            by(msg.oinit,*a,**ka)
        if not hasattr(msg,"oinit"):
            msg.oinit = msg.__init__

        msg.__init__ = initpro
    
    #MessageRecover
    #恢复Message
    def mr(msg):
        msg.__init__ = msg.oinit
    
    #log
    #输出日志
    def log(path,str):
        with open(path,"a") as f:
            f.write("\n")
            f.write(str)
    
    #Import To Debugger
    #导入类到Debugger类
    def itd(package,name):
        D.te("from "+package+" import "+name+"\nD.p"+name+"="+name)
    
    #Try Execute Code
    #尝试运行代码
    def te(code):
        try:
            exec(code)
        except BaseException as err:
            re = str(repr(err))
            D.s("运行异常："+re)
    def fr(a):
        return a
    
    #Test MOD
    #运行mod（带报错）
    def tm(p):
        try:
            exec(open(p,'r').read())
        except Exception as e:
            D.alp(D.mls(str(e)))
    
    #Mult Lines String
    #转为多行字符串
    def mls(s,n = 20):
    
        if not isinstance(s,str):
            s = str(s)
    
        r = ""
        for i in range(0,len(s)-n,n):
            r += s[i:i+n]
            r += "\n"
        r+=s[-(len(s)%n):]
        
        
        return r
    
    #Current game FirstPlayer
    #当前游戏第一个玩家
    def cfp():
        return D.a().players[0]
        
    
    #_Current game FirstPlayer(Backup)
    #当前游戏第一个玩家(备用方法)
    def _cfp():
        return D.a().players[0]
    
    #Player Node
    #玩家节点对象
    def pn():
        return D.pa().node
    
    #Player Actor
    #玩家演员对象
    def pa():
        return D.cfp().actor
    
    #Current game First Bot
    #当前游戏第一个机器人
    def cfb():
        return d.cb().get_living_bots()[0]
    
    #Current game Bots
    #当前游戏机器人
    def cb():
        return d.a()._bots if hasattr(d.a(),'_bots') else d.bots
    
    #id方法读取activity(垃圾回收器调用，已过时）
    """
    def sac(ac):
        D.acs = id(ac)
    """
    
    #已过时，使用D.a()代替
    """
    def gas():
        for obj in gc.get_objects():
            if id(obj) == D.acs:
                return obj
    """
    
    def g():
        return D.a().globalsnode
    
    #Command
    #发送指令
    def cc():
        pass
    
    #Update
    #刷新检查未处理事件
    def u():
        #如果有待处理事件
        if ("DS" in dir(ba)) and len(ba.DS) > 0:
            #D.si("加载"+len(ba.DS)+"个插件!")
            for e in ba.DS:
                if "name" in e:
                    D.si("DEBUG:关联插件启动成功:"+e["name"])
                if "event" in e:
                    try:
                        e["event"](D)
                    except Exception as ex:
                        D.s("加载异常:"+str(ex)+str(e),(1,0,0))
            ba.DS = []
    
    #Reload
    #重新加载某个模组
    def reload(mname):
        if not "." in mname:
            d.p("错误：没有包名！")
        name = mname.split(".")[0]
        cls = mname.split(".")[1]
        try:
            exec(f"import {name}\nimport importlib\nimportlib.reload({name})\nx={name}.{cls}()\nif hasattr(x,\"on_app_launch\"):\n  x.on_app_launch()")
        except Exception as e:
            d.p("加载错误："+str(e))
    
    #Save
    #保存指令列表
    def save():
        data = {}
        for k in D.commands:
            v = D.commands[k]
            
            if isinstance(v,str):
                data[k] = v
        
        con = json.dumps(data)
        
        with open(os.path.join(pdir,"chatExecConfig.json"),"w") as f:
            f.write(con)
    
    #Load
    #加载指令列表
    def load():
        if not os.path.exists(os.path.join(pdir,"chatExecConfig.json")):
            return
        
        with open(os.path.join(pdir,"chatExecConfig.json"),"r") as f:
            es = json.loads(f.read())
            for e in es:
                D.commands[e] = es[e]
    
    #内部方法 显示错误
    def _open_show_error():
      
      def print_err(*args,**kwargs):
        for a in args:
            d.si(a)
      
      import builtins
      import sys
      d.__oprint = builtins.print
      builtins.print = print_err
      
      _ba.oconsole_print = _ba.console_print
      _ba.console_print = print_err
      
      d.ostd = sys.stdout
      d.oerr = sys.stderr
      
      d.log_stream = open(os.path.join(pdir,"BSLOGS.log"),"a")
      sys.stdout = d.log_stream
      
      
      d.s("显示错误...",(0,1,1))

      d.show_error = True
    
    #内部方法 不显示错误
    def _close_show_error():

        if hasattr(d,"__oprint"):
            import builtins
            builtins.print = d.__oprint
        
        d.show_error = False
        
        sys.stdout = d.ostd
        sys.stderr = d.oerr
        d.log_stream.close()
        
        d.s("隐藏错误...",(0,1,1))
        
        _ba.console_print = _ba.oconsole_print
    

#别名
d = D


#核心方法
#发送聊天信息时识别标识符

def _send_chat_debuged(strmsg,send_error=False,mplayer=None,):
    

    re = "Done."
    
    #没有玩家对象
    if not mplayer:
        mplayer = {}
    
    #玩家名
    player = "<Unknow>"
    try:
        if "display_string" in mplayer:
            player = mplayer["display_string"]
    except Exception as e:
        print(e)
    #cid
    cid = None
    try:
        if "client_id" in mplayer:
            cid = mplayer["client_id"]
    except Exception as e:
        print(e)
    
    if (not strmsg) or len(strmsg)<1 or (not (strmsg[0] in ("~","/","%%"))):
        return False
    
    _mp = None
    
    #获取玩家对象
    d.cfp = d._cfp
    try:
        if "players" in mplayer and len(mplayer["players"]) > 0:
            _mp = d.a().players[mplayer["players"][0]["id"]]
    
        #转交cfp
        if _mp and _mp.actor and _mp.actor.node:
            d.cfp = lambda:_mp
        else:
            d.cfp = d._cfp
    except Exception as e:
        print(e)
    
    #获取共享对象
    shared = None
    try:
        with ba.Context(d.a() if d.a() else "current"):
            shared = SharedObjects.get()
    except Exception as e:
        pass
    
    if mplayer and "cfp" in strmsg:
        pass
        #D.si("#警告⚠：多人游戏建议使用d.a().players[玩家ID]代替cfp!")
        #D.si("#type /pl to show players")
        #D.si("# Warning: Multiplayer recommends using d.a().players[ID] instead of d.cfp!")
    
    if not 'history' in dir(D):
        D.history = ['','','~d.cfp().actor','~d.g()','~d.s()']
    if not (strmsg in D.history):
        D.history.append(strmsg)
    else:
        D.history.remove(strmsg)
        D.history.append(strmsg)
    
    #更新方法 &c 分割多个指令
    #Using “&c” Split Multiple commands
    if strmsg.find("&c") != -1:
        msgs = strmsg.split("&c")
        for cm in msgs:
            _send_chat_debuged(cm)
        return True
    
    if strmsg.startswith('%%'):
        try:
            if D.a():
                with ba.Context(d.a() if d.a() else "current"):
                    exec(strmsg[2:])
            else:
                exec(strmsg[2:])
        except BaseException as err:
            re = str(repr(err))
            ba._hooks.local_chat_message("运行异常：")
            D.alp(re)
            
            if send_error and player:
                d.si(player+"运行异常:"+str(re))
        else:
            ba._hooks.local_chat_message("执行成功！")
        return True
    elif strmsg.startswith('/'):
        cur_msg = strmsg.replace("&n","\n")
        cur_msg = cur_msg.replace("&q",'"')
        cur_msg = cur_msg.replace("&mq","'")
        try:
            #指令名称
            cname = ""
            #指令参数
            cargs = None
            
            
            if cur_msg.find(" ") != -1:
                cname = cur_msg[1:cur_msg.find(" ")]
                if len(cur_msg) > cur_msg.find(" ")+1:
                    cargs = cur_msg[cur_msg.find(" ")+1:].split(" ")
            else:
                cname = cur_msg[1:]
            if (cname in D.commands):
                if cargs:
                    D.commands[cname](D,cargs)
                else:
                    if isinstance(D.commands[cname],str):
                        D.cc(D.commands[cname])
                    else:
                        D.commands[cname](D)
                return True
            
            
            elif cur_msg in ("/史诗级","/史诗","/slow"):
                D.g().slow_motion = (not D.g().slow_motion)
                re = "Slow_Motion："+str(D.g().slow_motion)
            elif cur_msg in ("/护盾","/shields"):
                with ba.Context(d.a() if d.a() else "current"):
                    for p in D.a().players:
                        p.actor.equip_shields()
            elif cur_msg in ("/拳套","/boxing"):
                with ba.Context(d.a() if d.a() else "current"):
                    for p in D.a().players:
                        p.actor.equip_boxing_gloves()
            elif cur_msg in ("/玩家列表","/pl"):
                with ba.Context("ui"):
                    for e in _ba.get_game_roster():
                        wp = d.si if ("client_id" in mplayer) else d.p
                        wp(e['display_string'])
                        wp("CID:  "+str(e['client_id']))
                        wp("AID:  " + str(e['account_id']))
                        wp("PLAYERS:  " + str(e['players']))
                        wp("---------------------------")
            elif cur_msg in ("/玩家","/players"):
                with ba.Context(d.a() if d.a() else "current"):
                    d.si(str([("ID: "+str(i)," Name:"+d.a().players[i].getname(False)) for i in range(len(d.a().players))]))
            elif cur_msg in ("/复活","/生成玩家","/respawn"):
                with ba.Context(d.a() if d.a() else "current"):
                    for p in D.a().players:
                        D.a().spawn_player(p)
            elif cur_msg in ("/清屏","/全部击杀","/killall"):
                with ba.Context(d.a() if d.a() else "current"):
                    for p in D.a().players:
                        p.actor.handlemessage(ba.DieMessage())
                    
                    bot_list = ([b for b in D.a()._bots._bot_lists if b])
                    for bs in bot_list:
                        for b in bs:
                          b.handlemessage(ba.DieMessage())
            elif cur_msg in ("/杀死机器人","/killbot"):
                with ba.Context(d.a() if d.a() else "current"):
                    bot_list = ([b for b in D.a()._bots._bot_lists if b])
                    for bs in bot_list:
                        for b in bs:
                          b.handlemessage(ba.DieMessage())
            
            else:
                re = eval(cur_msg[1:])
        except BaseException as err:
            re = str(repr(err))
            ba._hooks.local_chat_message("Error：")
            
        if not (re == None) :
            if send_error and player:
                d.si(player+"@result:"+str(re))
            D.alp(str(re))
        
        return True
    elif strmsg.startswith('~'):
        cur_msg = strmsg.replace("&n","\n")
        cur_msg = cur_msg.replace("&q",'"')
        cur_msg = cur_msg.replace("&mq","'")
        re = "Done."
        try:
            if D.a():
                with ba.Context(D.a()):
                    re = exec(cur_msg[1:])
            else:
                with ba.Context("ui"):
                    re = exec(cur_msg[1:])
        except BaseException as err:
            re = str(repr(err))
            ba._hooks.local_chat_message("Error：")
        if not (re == None) :
            D.alp(str(re))
            if send_error and player:
                d.si(player+"/Error:"+str(re))
        
        return True
    
    
    
    return False

#(本地)发送消息的指令
def _send_chat_message_pro(self):
    strmsg = cast(str, ba.textwidget(query=self._text_field))
    
    if D.opened and _send_chat_debuged(strmsg):
        pass
    elif strmsg == "@u":
        ba.textwidget(edit=self._text_field, text=D.lastmsg)
        return
    else:
        if "\n" in strmsg:
            D.s("Line feed message detected, automatically escaped~")
            ba.textwidget(edit=self._text_field, text=str(
                    strmsg.replace("\n","&n")
            ))
            return
        if len(strmsg) > 90:
            D.s("The send message is too long and will be automatically fragmented...",(0,1,1))
            for s in range(0,len(strmsg),90):
                ba.textwidget(edit=self._text_field, text=str(
                    strmsg[s:s+90] + "<UNEND>"
                ))
                self._send_chat_message_sub()
            ba.textwidget(edit=self._text_field, text='')
            self._send_chat_message_sub()
        else:
            self._send_chat_message_sub()
    D.lastmsg = strmsg
    ba.textwidget(edit=self._text_field, text='')

d.mbuffer = ""

#修改聊天过滤
def debug_filter_chat_message(msg,cid = -1):
    mp = None
    
    
    #处理衔接没有结束的消息
    if len(d.mbuffer) > 0:
        msg = d.mbuffer + msg
    
    #衔接消息
    if msg.endswith("<UNEND>"):
        d.mbuffer = msg[:-7]
        return None
    else:
        d.mbuffer = ""
    
    if cid in d.baned:
        d.s("Execution failed, you do not have permission！",(1,0,0),clients=[cid])
        return None
    
    if _ba.get_game_roster():
        for p in _ba.get_game_roster():
            if "client_id" in p and p['client_id'] == cid:
                mp = p
                break
    
    if mp == None and cid != -1:
        mp = {"display_string":"<Unknow>"}
    elif mp==None and cid == -1:
        mp = {"display_string":"<HOST>"}
    
    if d.cc(msg,True,mp):
        d.s(mp["display_string"]+"Executed"+msg,(0,1,0))
        return None
    else:
        return msg

#注入activity方法
def on_begin_pro(self):
    
    #检查未处理事件
    D.u()
    
    #清除临时变量
    if "tmp" in dir(D):
        D.tmp = None
    
    
    self.on_begin_y()
    
    if "event" in dir(D):
        for e in D.event:
            try:
              D.cc(e)
            except Exception as e:
              D.s(e)
    
    if not "_bots" in dir(self):
        d.bots = SpazBotSet()
    else:
        d.bots = self._bots
    
    if not _ba.is_party_icon_visible():
        _ba.set_party_icon_always_visible(True)

handled_msg = []
#聊天检查
def chat_checker():
    D = ba.D
    d = ba.D
    
    amsg = ba.internal.get_chat_messages()
    if not len(amsg) > len(handled_msg):
        return
    
    for msg in amsg[len(handled_msg):]:
        try:
            if msg.find(":") == -1:
                handled_msg.append(msg)
                return
            player = msg[:msg.find(":")]
            command = msg[msg.find(":")+2:]
            ok = ba.D.cc(command,True,player)
            if ok:
                ba.screenmessage(player+" Executed "+command,(0,1,0),transient = True)
        except Exception as e:
            d.si("Error: "+str(e))
        finally:
            handled_msg.append(msg)

#点击指令按钮的操作
def command_func(self):
    msg = cast(str, ba.textwidget(query=self._text_field))
    if len(msg) <= 1:
        ba.textwidget(edit=self._text_field, text="/d.")
    else:
        ok = False
        try:
            
            
            value = eval(msg[1:])
            if value:
                if isinstance(value,str) or isinstance(value,int)  or isinstance(value,float) or isinstance(value,list) or isinstance(value,tuple) or isinstance(value,set):
                    d.s(value)
                else:
                    import re
                    strinfo = re.compile('__.*?__,\\s*')
                    fixing =  str(dir(value)).replace(",",",  ").replace("'","")
                    
                    fixed = re.sub(strinfo,"",fixing)
                    
                    d.p("\n")
                    d.p("------"+str(value))
                    d.alp(fixed)
            
            ok = True      
        except Exception as e:
            ok = False
        
        if not ok:
            try:
                pm = msg[1:msg.rfind(".")]
                pt = msg[msg.rfind(".")+1:]
                wmtpv = eval(pm)
                wmtpas = [mvttt for mvttt in dir(wmtpv) if mvttt.startswith(pt)]
                if len(wmtpas) == 0:
                    D.p("No matched.")
                    d.s(repr(e),(1,0,0))
                elif len(wmtpas) == 1:
                    ba.textwidget(edit=self._text_field, text=msg[0]+pm+"."+wmtpas[0])
                else:
                    D.alp("["+"   ".join(wmtpas)+"]")
            except Exception as et:
                d.s(repr(et),(1,0,0))
                d.s(repr(e),(1,0,0))

#功能按钮
def func_btn_pressed(self):
        from bastd.ui import popup
        uiscale = ba.app.ui.uiscale
        popup.PopupMenuWindow(
            position=self._func_button.get_screen_space_center(),
            scale=(2.3 if uiscale is ba.UIScale.SMALL else
                   1.65 if uiscale is ba.UIScale.MEDIUM else 1.23),
            choices=["history"+str(x) for x in range(0,5)]+["clear"],
            choices_display=[
                ba.Lstr(value=str(x) if len(x) < 15 else x[:14]+"...") for x in D.history[-1:-6:-1]
            ]+[ba.Lstr(value="clear histories")],
            current_choice="history0",
            delegate=self)
        self._popup_type = 'menu'

#运行文件
def run_file_debugger(self):
    from bastd.ui.fileselector import FileSelectorWindow
    
    from bastd.ui import popup
    uiscale = ba.app.ui.uiscale
    popup.PopupMenuWindow(
        position=self.file_button.get_screen_space_center(),
        scale=(2.3 if uiscale is ba.UIScale.SMALL else
                1.65 if uiscale is ba.UIScale.MEDIUM else 1.23),
        choices=["file_mod","file_internal","file_last"],
        choices_display=[
            ba.Lstr(value="Run User Scripts"),
            ba.Lstr(value="Get Internal Path"),
            ba.Lstr(value="Run Last File")
        ],
        current_choice="file_mod",
        delegate=self)
    self._popup_type = 'menu'
    

#修改聊天框~
def new_partywindow_init(self, origin):
        _ba.set_party_window_open(True)
        self._r = 'partyWindow'
        self._popup_type: Optional[str] = None
        self._popup_party_member_client_id: Optional[int] = None
        self._popup_party_member_is_host: Optional[bool] = None
        self._width = 500
        uiscale = ba.app.ui.uiscale
        self._height = (365 if uiscale is ba.UIScale.SMALL else
                        480 if uiscale is ba.UIScale.MEDIUM else 600)
        ba.Window.__init__(self,root_widget=ba.containerwidget(
            size=(self._width, self._height),
            transition='in_scale',
            color=(0.40, 0.55, 0.20),
            parent=_ba.get_special_widget('overlay_stack'),
            on_outside_click_call=self.close_with_sound,
            scale_origin_stack_offset=origin,
            scale=(2.0 if uiscale is ba.UIScale.SMALL else
                   1.35 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -10) if uiscale is ba.UIScale.SMALL else (
                240, 0) if uiscale is ba.UIScale.MEDIUM else (330, 20)))

        self._cancel_button = ba.buttonwidget(parent=self._root_widget,
                                              scale=0.7,
                                              position=(30, self._height - 47),
                                              size=(50, 50),
                                              label='',
                                              on_activate_call=self.close,
                                              autoselect=True,
                                              color=(0.45, 0.63, 0.15),
                                              icon=ba.gettexture('crossOut'),
                                              iconscale=1.2)
        
    
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=self._cancel_button)

        
        self.file_button = ba.buttonwidget(parent=self._root_widget,
                                              scale=0.7,
                                              position=(90, self._height - 47),
                                              size=(50, 50),
                                              label='',
                                              on_activate_call=lambda:run_file_debugger(self),
                                              autoselect=True,
                                              color=(0.45, 0.63, 0.15),
                                              icon=ba.gettexture('file'),
                                              iconscale=1.2)
        
    
        ba.containerwidget(edit=self._root_widget,
                           cancel_button=self.file_button)

        self._menu_button = ba.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(self._width - 60, self._height - 47),
            size=(50, 50),
            label='...',
            autoselect=True,
            button_type='square',
            on_activate_call=ba.WeakCall(self._on_menu_button_press),
            color=(0.55, 0.73, 0.25),
            iconscale=1.2)
        
        #添加按钮
        self._func_button = ba.buttonwidget(
            parent=self._root_widget,
            scale=0.7,
            position=(self._width - 120, self._height - 47),
            size=(50, 50),
            label='',
            autoselect=True,
            button_type='square',
            on_activate_call=lambda :func_btn_pressed(self),
            color=(0.55, 0.73, 0.25),
            iconscale=1.2)

        info = _ba.get_connection_to_host_info()
        if info.get('name', '') != '':
            title = ba.Lstr(value=info['name'])
        else:
            title = ba.Lstr(resource=self._r + '.titleText')

        self._title_text = ba.textwidget(parent=self._root_widget,
                                         scale=0.5,
                                         color=(0.5, 0.7, 0.5),
                                         text=title,
                                         size=(0, 0),
                                         position=(self._width * 0.5,
                                                   self._height - 29),
                                         maxwidth=self._width * 0.7,
                                         h_align='center',
                                         v_align='center')

        self._empty_str = ba.textwidget(parent=self._root_widget,
                                        scale=0.75,
                                        size=(0, 0),
                                        position=(self._width * 0.5,
                                                  self._height - 65),
                                        maxwidth=self._width * 0.85,
                                        h_align='center',
                                        v_align='center')

        self._scroll_width = self._width - 50
        self._scrollwidget = ba.scrollwidget(parent=self._root_widget,
                                             size=(self._scroll_width,
                                                   self._height - 200),
                                             position=(30, 80),
                                             color=(0.4, 0.6, 0.3))
        self._columnwidget = ba.columnwidget(parent=self._scrollwidget,
                                             border=2,
                                             margin=0)
        ba.widget(edit=self._menu_button, down_widget=self._columnwidget)

        self._muted_text = ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height * 0.5),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=ba.Lstr(resource='chatMutedText'))
        
        self._chat_texts: List[ba.Widget] = []

        # add all existing messages if chat is not muted
        if not ba.app.config.resolve('Chat Muted'):
            msgs = _ba.get_chat_messages()
            for msg in msgs:
                self._add_msg(msg)

        self._text_field = txt = ba.textwidget(
            parent=self._root_widget,
            editable=True,
            size=(430, 40),
            position=(118, 39),
            text='',
            maxwidth=494,
            shadow=0.3,
            flatness=1.0,
            description=ba.Lstr(resource=self._r + '.chatMessageText'),
            autoselect=True,
            v_align='center',
            corner_scale=0.7)

        ba.widget(edit=self._scrollwidget,
                  autoselect=True,
                  left_widget=self._cancel_button,
                  up_widget=self._cancel_button,
                  down_widget=self._text_field)
        ba.widget(edit=self._columnwidget,
                  autoselect=True,
                  up_widget=self._cancel_button,
                  down_widget=self._text_field)
        ba.containerwidget(edit=self._root_widget, selected_child=txt)
        btn = ba.buttonwidget(parent=self._root_widget,
                              size=(50, 35),
                              label=ba.Lstr(resource=self._r + '.sendText'),
                              button_type='square',
                              autoselect=True,
                              position=(self._width - 70, 35),
                              on_activate_call=self._send_chat_message)
        #新增按钮
        upbtn = ba.buttonwidget(parent=self._root_widget,
                              size=(30, 35),
                              label="",
                              button_type='square',
                              autoselect=True,
                              position=(22, 35),
                              on_activate_call=lambda: ba.textwidget(edit=self._text_field, text=D.lastmsg))
        downbtn = ba.buttonwidget(parent=self._root_widget,
                              size=(30, 35),
                              label="/",
                              button_type='square',
                              autoselect=True,
                              position=(65, 35),
                              on_activate_call=lambda :command_func(self))
        ba.textwidget(edit=txt, on_return_press_call=btn.activate)
        self._name_widgets: List[ba.Widget] = []
        self._roster: Optional[List[Dict[str, Any]]] = None
        self._update_timer = ba.Timer(1.0,
                                      ba.WeakCall(self._update),
                                      repeat=True,
                                      timetype=ba.TimeType.REAL)
        self._update()

#修改菜单~
def new_partywindow_menu_button_press(self):
        from bastd.ui import popup
        is_muted = ba.app.config.resolve('Chat Muted')
        uiscale = ba.app.ui.uiscale
        popup.PopupMenuWindow(
            position=self._menu_button.get_screen_space_center(),
            scale=(2.3 if uiscale is ba.UIScale.SMALL else
                   1.65 if uiscale is ba.UIScale.MEDIUM else 1.23),
            choices=['unmute' if is_muted else 'mute','fswitch','switch', 'error_switch','update','help'],
            choices_display=[
                ba.Lstr(resource='chatUnMuteText' if is_muted else 'chatMuteText'),
                
                ba.Lstr(value=("Close remote command" if D.fopened else "Open remote command")),
                
                ba.Lstr(value=("Close command" if D.opened else "Open command")),

                ba.Lstr(value=("Hide Errors" if D.show_error else "Show Errors")),
                
                ba.Lstr(value='Check for updates'),
                
                ba.Lstr(value='help')
            ],
            current_choice='unmute' if is_muted else 'mute',
            delegate=self)
        self._popup_type = 'menu'

#检查更新
def check_for_update():
    def _result(code,con):
        if code == 200:
            b = con
            
            info = json.loads(b)
        
            if int(info['version_code']) <= D.version_code:
                d.p("检查完成，已是最新版！"+"("+info["version"]+" / "+info["date"]+")")
                return
        
            d.p("发现新版本！" + "("+info["version"]+" / "+info["date"]+")")
            d.p("下载链接："+info["url"])
            d.p("输入 /更新 或 /update 下载更新")
            
            d.upurl = info["url"]
            
            def _update(d):
                d.si("正在自动更新，请等待5~10秒！")
                def _write(code,con):
                    d.si("获取到更新，正在写入！")
                    if code == 200:
                        d.si("更新成功！重启游戏生效！")
                        with open(pdir + "/chatExecNew.py","wb") as f:
                            f.write(con)
                    else:
                        d.p("更新失败，请检查网络！")
                HttpGetter(d.upurl,_write)
            
            d.commands["update"] = _update
            d.commands["更新"] = _update
            #ba.open_url(info["url"])
        else:
            d.p("无法连接服务器，请稍后再试！")
    
    HttpGetter("https://gitee.com/wsdx233/bombsquad-chat-command/raw/master/index.json",_result)

def new_popup_menu_selected_choice(self, popup_window: popup.PopupMenuWindow,choice: str) -> None:
        """Called when a choice is selected in the popup."""
        del popup_window  # unused
        if self._popup_type == 'partyMemberPress':
            if self._popup_party_member_is_host:
                ba.playsound(ba.getsound('error'))
                ba.screenmessage(
                    ba.Lstr(resource='internal.cantKickHostError'),
                    color=(1, 0, 0))
            else:
                assert self._popup_party_member_client_id is not None

                # Ban for 5 minutes.
                result = _ba.disconnect_client(
                    self._popup_party_member_client_id, ban_time=5 * 60)
                if not result:
                    ba.playsound(ba.getsound('error'))
                    ba.screenmessage(
                        ba.Lstr(resource='getTicketsWindow.unavailableText'),
                        color=(1, 0, 0))
        elif self._popup_type == 'menu':
            if len(choice) == 8 and choice[:-1] == "history":
                ba.textwidget(edit=self._text_field, text=D.history[- int(choice[-1] ) -1])
            elif choice == "clear":
                D.history = [""] * 5
            elif choice in ('mute', 'unmute'):
                cfg = ba.app.config
                cfg['Chat Muted'] = (choice == 'mute')
                cfg.apply_and_commit()
                self._update()
            elif choice == "switch":
                D.opened = not D.opened
            elif choice == "fswitch":
                D.fopened = not D.fopened
                
                if D.fopened:
                    d.s("Receiving instructions as host...",(0,1,0))
                    #d.check_timer = ba.Timer(3,chat_checker,repeat=True,timetype=ba.TimeType.REAL)
                    
                    #ba._hooks.filter_chat_message.__code__ = debug_filter_chat_message.__code__
                    #import ba._hooks
                    fcm = ba._hooks.filter_chat_message
                    d.ofilter = fcm.__code__
                    
                    fcm.__globals__["d"] = d
                    fcm.__globals__["D"] = D
                    fcm.__globals__["ba"] = ba
                    
                    nfcm = debug_filter_chat_message
                    fcm.__code__ = nfcm.__code__
                else:
                    ba._hooks.filter_chat_message.__code__ = d.ofilter
                    d.s("Stop receiving command...",(0,1,1))
                    #d.check_timer = None
                    
            elif choice == "error_switch":
                if d.show_error:
                    d._close_show_error()
                    d.s("Turn off chat error display...")
                else:
                    d._open_show_error()
                    d.s("Enable chat error display！")
            elif choice == "update":
                d.s("One moment, please....")
                check_for_update()
            elif choice == "help":
                D.cc("/help")
            elif choice == "file_mod":
                def fcall_back(path):
                    d.cc("~d.tm('%s')" % path)
                    d.last_file = path
                FileSelectorWindow(pdir,callback=fcall_back,valid_file_extensions=["py","mod"])
                self.close()
            elif choice == "file_internal":
                def fcall_back(path):
                    d.si(path)
                    d.last_file = path
                FileSelectorWindow(adir,callback=fcall_back,valid_file_extensions=["py","mod"])
                self.close()
            elif choice == "file_last":
                if not hasattr(d,"last_file"):
                    d.s("No previous file...",(1,0,0))
                    return
                d.tm(d.last_file)
                
        else:
            print(f'unhandled popup type: {self._popup_type}')

# ba_meta export plugin
class ChatFixer(ba.Plugin):
  def __init__(self):
    #始终显示聊天按钮
    _ba.set_party_icon_always_visible(True)
    #不修改聊天信息
    #PartyWindow.on_chat_message = on_chat_message_pro
    PartyWindow._send_chat_message_sub = PartyWindow._send_chat_message
    PartyWindow._send_chat_message = _send_chat_message_pro

    PartyWindow.__init__ = new_partywindow_init
    PartyWindow._on_menu_button_press = new_partywindow_menu_button_press
    PartyWindow.popup_menu_selected_choice = new_popup_menu_selected_choice

    #注入activity方法显示派对图标（聊天框图标)
    ba.Activity.on_begin_y = ba.Activity.on_begin
    ba.Activity.on_begin = on_begin_pro

    #注入聊天消息过滤（作为服务器时可用）
    #在菜单手动开启！
    #_ba.filter_chat_message = debug_filter_chat_message
    #ba._hooks.filter_chat_message = debug_filter_chat_message
    #d.filter = debug_filter_chat_message

    #控制关联插件
    if not ("DS" in dir(ba)):
        ba.DS = []

    #添加D.cc
    D.cc = _send_chat_debuged

    #注入D.s
    ba.s = D.s

    #向ba模块中添加Debugger类
    ba.D = D

    #检查未处理事件
    ba.timer(1,D.u)

    #默认打开指令
    D.opened = True

    #自动加载保存的指令
    D.load()

    #添加权限管理操作
    #simple admin system
    def _ban(d,args = None):
        if not args or len(args) < 1:
            d.p("格式错误：请输入CID")
        else:
            d.baned.append(int(args[0]))
            d.s("已封禁玩家："+args[0],(1,0,0))
            
    def _op(d,args = None):
        if not args or len(args) < 1:
            d.p("格式错误：请输入CID")
        else:
            if not (int(args[0]) in d.baned):
                d.s("已是管理员！",(1,1,0))
                return
            d.baned.remove(int(args[0]))
            d.s("已授予玩家管理员："+args[0],(0,1,0))
    
    with ba.Context("ui"):
        ba.timer(4,d.u,True)
    
    D.ac("ban",_ban)
    D.ac("op",_op)
    
    #Automatic network acquisition instruction
    try:
        _t = AutoCommandChecker()
        _t.start()
    except Exception as e:
        return

    #处理指令
    #if False:
    #  d.s("正在作为主机处理指令，编辑指令mod以关闭！",(0,1,0))
    #  d.check_timer = ba.Timer(3,chat_checker,repeat=True,timetype=ba.TimeType.REAL)

    #聊天报错
    d._open_show_error()
    
    
    try:
        from bastd.ui.v2upgrade import V2UpgradeWindow
        V2UpgradeWindow.__init__ = lambda *a,**b:None
    except ImportError as e:
        pass
