from bsUI import uiGlobals, gSmallUI, Window, gMedUI, MainMenuWindow            #Created By MythB # http://github.com/MythB
import bs, bsUtils, bsInternal, bsMainMenu, threading, time, json, urllib2, httplib

_server_status_thread_count = 0
delayChecker = False

class ServerStatusWindow(Window):

    def __init__(self):
        self.buttonChecker = False
        height = 200
        width = 360
        bs.containerWidget(edit=uiGlobals['mainMenuWindow'],transition='outLeft')
        self._rootWidget = bs.containerWidget(
            size=(width, height), transition=('inRight'),
            toolbarVisibility='MENU_MINIMAL_NOBACK',
            parent=bsInternal._getSpecialWidget('overlayStack'),
            scale=2.1 if gSmallUI else 1.5 if gMedUI else 1.3,
            color=(0.215, 0.278, 0.309))
            
        self.lt = bs.textWidget(parent=self._rootWidget,
                          position=(width/2, height/2),
                          size=(0, 0), hAlign="center", vAlign="center",shadow=1.0,
                          text=bs.Lstr(resource='loadingText'), scale=1.0,
                          maxWidth=width*0.9, maxHeight=height-75)
                          
        self.t = bs.textWidget(parent=self._rootWidget,
                          position=(width*0.5, height-5-(height-75)*0.25),shadow=1.0,
                          size=(0, 0), hAlign="center", vAlign="center",
                          text='', scale=1.0,
                          maxWidth=250, maxHeight=height-75)
                          
        self.pt = bs.textWidget(parent=self._rootWidget,
                          position=(width*0.2, height-5-(height-75)*0.8),shadow=1.0,
                          size=(0, 0), hAlign="center", vAlign="center",
                          text='', scale=1.0,
                          maxWidth=width*0.9, maxHeight=height-75)
                          
        self.pvt = bs.textWidget(parent=self._rootWidget,shadow=1.0,
                          position=(width*0.30, height-5-(height-75)*0.8),
                          size=(0, 0), hAlign="left", vAlign="center",
                          text='', scale=1.0,
                          maxWidth=width*0.9, maxHeight=height-75)
                          
        self.ts = bs.textWidget(parent=self._rootWidget,shadow=1.0,
                          position=(width*0.75, height-5-(height-75)*0.8),
                          size=(0, 0), hAlign="left", vAlign="center",
                          text='', scale=1.0,
                          maxWidth=width*0.9, maxHeight=height-75)

        self.tvs = bs.textWidget(parent=self._rootWidget,shadow=1.0,
                          position=(width*0.65, height-5-(height-75)*0.8),
                          size=(0, 0), hAlign="center", vAlign="center",
                          text='', scale=1.0,
                          maxWidth=width*0.9, maxHeight=height-75)                          
                            
        self.cb = b = bs.buttonWidget(parent=self._rootWidget, autoSelect=True,buttonType='backSmall',
                                 position=(20, 150), size=(30, 30),scale=1.0,textResScale=1.5,textColor=(0.9,0.9,0.9),
                                 label=bs.getSpecialChar('back'),color=(0.356, 0.760, 0.905),textScale=0.7,
                                 onActivateCall=self._cancel)
        bs.containerWidget(edit=self._rootWidget, cancelButton=b)
        self.Timir = bs.Timer(5000,bs.WeakCall(self._serverAddressFetchThread),repeat=True,timeType='real')
   
    def _serverAddressFetchThread(self):
        if _server_status_thread_count > 0:
            return
        class fetchThread(threading.Thread):
            def __init__(self, fetchCall):
                threading.Thread.__init__(self)
                self._fetchCall = fetchCall

            def run(self):
                global _server_status_thread_count
                _server_status_thread_count += 1
                try:
                    accessible = True
                    if hasattr(httplib, 'HTTPS'):
                       url = 'https://raw.githubusercontent.com/MythB/BombSquad-Mods/master/index.json'
                    else:
                       url = 'http://raw.githack.com/MythB/BombSquad-Mods/master/index.json'
                    try:
                        response = json.loads(urllib2.urlopen(urllib2.Request(url)).read())
                        fetchedAddress = response['Address']
                        fetchedPort = int(response['Port'])
                    except Exception:
                        fetchedAddress = None
                        fetchedPort = None
                        accessible = False
                    time.sleep(1)
                    bs.callInGameThread(bs.Call(self._fetchCall, fetchedAddress, fetchedPort if accessible else None))
                except Exception as e:
                       print (e)
                _server_status_thread_count -= 1
        fetchThread(self._serverStatusCheckThread).start()
    
    def _serverStatusCheckThread(self, fetchedAddress, fetchedPort):
        height = 200
        width = 360
        class PingThread(threading.Thread):
            def __init__(self, address, port, call):
                threading.Thread.__init__(self)
                self._address = bs.utf8(address)
                self._port = port
                self._call = call

            def run(self):
                try:                
                    import socket
                    socket_type = bsUtils._getIPAddressType(
                        self._address)
                    s = socket.socket(socket_type,
                                      socket.SOCK_DGRAM)
                    s.connect((self._address, self._port))

                    accessible = False
                    start_time = time.time()
                    s.settimeout(1)
                    for i in range(3):
                        s.send('\x0b')
                        try:
                            # 11: BS_PACKET_SIMPLE_PING
                            result = s.recv(10)
                        except Exception:
                            result = None
                        if result == '\x0c':
                            # 12: BS_PACKET_SIMPLE_PONG
                            accessible = True
                            break
                        time.sleep(1)
                    s.close()
                    ping = int((time.time()-start_time)*1000.0)
                    bs.callInGameThread(bs.Call(self._call, self._address, self._port,ping if accessible else None))
                except Exception as e:
                       print (e)
        if fetchedPort != None:
            PingThread(fetchedAddress,fetchedPort,bs.Call(self.fetchedDataCallBack)).start()
            if self._rootWidget.exists():
                fadeToBack()
        else:
            if self._rootWidget.exists():
                fadeToRed()
                if self.buttonChecker == True:
                    self.sb.delete()
                    self.ob.delete()
                    self.buttonChecker = False
                bs.textWidget(edit=self.t, text='')
                bs.textWidget(edit=self.pt, text='')
                bs.textWidget(edit=self.pvt, text='')
                bs.textWidget(edit=self.ts, text='')
                bs.textWidget(edit=self.tvs, text='')       
                bs.textWidget(edit=self.lt, text=bs.Lstr(resource='gatherWindow.addressFetchErrorText'),color=(1,1,1))
    
    def fetchedDataCallBack(self, address, port, result):
        #print (address, port, result)
        global finalFetchedAddress
        finalFetchedAddress = address
        global finalFetchedPort
        finalFetchedPort = port
        
        if result is not None:
            env = bs.getEnvironment()
            try:
                bsInternal._addTransaction(
                    {'type': 'PUBLIC_PARTY_QUERY',
                    'proto': env['protocolVersion'],
                    'lang': bs.getLanguage()},
                    callback=bs.WeakCall(self._serverSynchronizer))
                bsInternal._runTransactions()
            except Exception as e:
                print (e)
            if 1 < result < 100:
               self.pingStatusColor = (0,1,0)
            elif 100 < result < 500:
               self.pingStatusColor = (1,1,0)
            else:
               self.pingStatusColor = (1,0,0)
            if self._rootWidget.exists():
                fadeToBack()
                bs.textWidget(edit=self.lt, text='')
                bs.textWidget(edit=self.pt, text='ping:')
                bs.textWidget(edit=self.pvt,text=str(result),color=self.pingStatusColor)
                if self.buttonChecker == False:
                    self.sb = bs.buttonWidget(parent=self._rootWidget, autoSelect=True,
                                     position=(140, 125), size=(80, 20),textColor=(1.0, 1.0, 1.0),
                                     label=bs.Lstr(resource='statsText'),color=(0.356, 0.760, 0.905),
                                     onActivateCall=self._stats)
                    self.ob = bs.buttonWidget(parent=self._rootWidget, autoSelect=True,
                                position=(105, 15), size=(150, 50),color=(0.356, 0.760, 0.905),textColor=(1.0, 1.0, 1.0),
                                label=bs.Lstr(resource='gatherWindow.manualConnectText'),onActivateCall=self._connect)
                    self.buttonChecker = True
        else:
            if self._rootWidget.exists():
                fadeToRed()
                if self.buttonChecker == True:
                    self.sb.delete()
                    self.ob.delete()
                    self.buttonChecker = False
                bs.textWidget(edit=self.t, text='')
                bs.textWidget(edit=self.pt, text='')
                bs.textWidget(edit=self.pvt, text='')
                bs.textWidget(edit=self.ts, text='')
                bs.textWidget(edit=self.tvs, text='')
                bs.textWidget(edit=self.lt, text='SERVER OFFLINE', color=(1,0,0))
            
    def _serverSynchronizer(self, result):
        if result is None:
            return       
        else:
            ipAdr = result['l']
            for i in ipAdr:
                if i['a'] == finalFetchedAddress and i['p'] == finalFetchedPort:
                    if i['s'] == i['sm']:
                        self.partySizeColor = (1,0,0)
                    else:
                        self.partySizeColor = (0,1,0)
                    if self._rootWidget.exists():
                        bs.textWidget(edit=self.t, text=i['n'])
                        bs.textWidget(edit=self.tvs, text='size:')
                        bs.textWidget(edit=self.ts, text= str(i['s'])+ '/' +str(i['sm']),color = self.partySizeColor)
                        global finalFetchedStats
                        finalFetchedStats = i['sa'] if i['sa'] !='' else self.sb.delete()

    def _stats(self):
        finalFetchedStats.replace('${ACCOUNT}', bsInternal._getAccountMiscReadVal2('resolvedAccountID', 'UNKNOWN'))
        bs.openURL(finalFetchedStats)
      
    def _cancel(self):
        bs.containerWidget(edit=self._rootWidget,
                           transition=('outRight'))
        uiGlobals['mainMenuWindow'] = MainMenuWindow(transition='inLeft').getRootWidget()
        self.Timir = None
        fadeToBack()

    def _connect(self):
        if not self._rootWidget.exists():
            return
        self.Timir = None
        bsInternal._connectToParty(finalFetchedAddress, finalFetchedPort)
        #bs.playSound(bs.getSound("achievement"))
        
def fadeToRed():
    activity = bsInternal._getForegroundHostActivity()
    with bs.Context(activity):
        cExisting = bs.getSharedObject('globals').tint
        c = bs.newNode(
            "combine",
            attrs={'input0': cExisting[0],
                   'input1': cExisting[1],
                   'input2': cExisting[2],
                   'size': 3})
        bs.animate(c, 'input1', {0: cExisting[1], 2000: 0})
        bs.animate(c, 'input2', {0: cExisting[2], 2000: 0})
        c.connectAttr('output', bs.getSharedObject('globals'), 'tint')

def fadeToBack():
    activity = bsInternal._getForegroundHostActivity()
    with bs.Context(activity):
        cExisting = bs.getSharedObject('globals').tint
        c = bs.newNode(
            "combine",
            attrs={'input0': cExisting[0],
                   'input1': cExisting[1],
                   'input2': cExisting[2],
                   'size': 3})
        bs.animate(c, 'input0', {0: cExisting[0], 2000: 1.1399999856948853})
        bs.animate(c, 'input1', {0: cExisting[1], 2000: 1.100000023841858})
        bs.animate(c, 'input2', {0: cExisting[2], 2000: 1.0})
        c.connectAttr('output', bs.getSharedObject('globals'), 'tint')

def _doServerStatusWindow():
    uiGlobals['mainMenuWindow'] = ServerStatusWindow().getRootWidget()

oldMethod = MainMenuWindow._refresh

def newMethod(self, *args, **kwargs):
    oldMethod(self, *args, **kwargs)
    width = -130
    height = -22.5 if gSmallUI else -54.5 if gMedUI else -79
    size = (94.5,85) if gSmallUI else (91,81) if gMedUI else (90,80)
    global delayChecker
    if not delayChecker:
        delay = 1900
        delayChecker = True
    else:
        delay = 0

    self._inGame = not isinstance(bsInternal._getForegroundHostSession(),bsMainMenu.MainMenuSession)
    if not self._inGame:
        self._MythBServerButton = b = bs.buttonWidget(parent=self._rootWidget,
                                            position=(width,height),
                                            color=(0.356, 0.760, 0.905),
                                            size=size,
                                            transitionDelay=delay,
                                            textScale=1.0,
                                            textColor=(1,1,1),
                                            buttonType='square',
                                            texture=bs.getTexture('buttonSquare'),
                                            label='',
                                            onActivateCall=_doServerStatusWindow)
        bs.textWidget(parent=self._rootWidget,
                      position=(width+20,height+6.5),
                      scale=0.75,drawController=b,
                      transitionDelay=delay,
                      color=(0.75, 1.0, 0.7),
                      maxWidth=width*0.33,
                      text='MythB.',
                      hAlign='center', vAlign='center')
        iconSize = -width*0.38
        bs.imageWidget(parent=self._rootWidget, size=(iconSize, iconSize),
                       transitionDelay=delay,color=(1.2, 0.843, 0),
                       position=(width+20,height+27),drawController=b,
                       texture=bs.getTexture('star')) 
MainMenuWindow._refresh = newMethod
