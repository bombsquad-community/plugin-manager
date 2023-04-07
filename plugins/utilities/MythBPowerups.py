import bs                   #Created By MythB # http://github.com/MythB
import random
import bsPowerup
import bsUtils
import weakref
import bsInternal
from bsPowerup import PowerupMessage, PowerupAcceptMessage, _TouchedMessage, PowerupFactory, Powerup

defaultPowerupInterval = 8000
gPowerupWearOffTime = 20000
gMythBPowerUpsWearOffTime = 12000

class NewPowerupFactory(PowerupFactory):
    def __init__(self):
        self._lastPowerupType = None

        self.model = bs.getModel("powerup")
        self.modelSimple = bs.getModel("powerupSimple")

        self.texBomb = bs.getTexture("powerupBomb")
        self.texPunch = bs.getTexture("powerupPunch")
        self.texIceBombs = bs.getTexture("powerupIceBombs")
        self.texStickyBombs = bs.getTexture("powerupStickyBombs")
        self.texShield = bs.getTexture("powerupShield")
        self.texImpactBombs = bs.getTexture("powerupImpactBombs")
        self.texHealth = bs.getTexture("powerupHealth")
        self.texLandMines = bs.getTexture("powerupLandMines")
        self.texCurse = bs.getTexture("powerupCurse")
        self.texSuperStar = bs.getTexture("levelIcon") #for superStar powerup
        self.texSpeed = bs.getTexture("powerupSpeed") #for speed powerup
        self.texIceCube = bs.getTexture("tipTopBGColor") #for iceCube powerup
        self.texSurprise = bs.getTexture("powerupHealth") #for surprise powerup
        self.texMartyrdom = bs.getTexture("achievementCrossHair") #for martyrdom
        self.healthPowerupSound = bs.getSound("healthPowerup")
        self.powerupSound = bs.getSound("powerup01")
        self.powerdownSound = bs.getSound("powerdown01")
        self.dropSound = bs.getSound("boxDrop")
        self.superStarSound = bs.getSound("ooh") #for superstar
        self.speedSound = bs.getSound("shieldUp") #for speed
        self.surpriseSound = bs.getSound("hiss") #for surprise
        self.iceCubeSound = bs.getSound("freeze") #for iceCube
        self.martyrdomSound = bs.getSound("activateBeep") #for martyrdom drop
        self.martyrdomPickSound = bs.getSound("gunCocking") #for martyrdom pick
        self.blockSound = bs.getSound('block') #for blocking
        

        # material for powerups
        self.powerupMaterial = bs.Material()

        # material for anyone wanting to accept powerups
        self.powerupAcceptMaterial = bs.Material()

        # pass a powerup-touched message to applicable stuff
        self.powerupMaterial.addActions(
            conditions=(("theyHaveMaterial",self.powerupAcceptMaterial)),
            actions=(("modifyPartCollision","collide",True),
                     ("modifyPartCollision","physical",False),
                     ("message","ourNode","atConnect",_TouchedMessage())))

        # we dont wanna be picked up
        self.powerupMaterial.addActions(
            conditions=("theyHaveMaterial",
                        bs.getSharedObject('pickupMaterial')),
            actions=( ("modifyPartCollision","collide",False)))

        self.powerupMaterial.addActions(
            conditions=("theyHaveMaterial",
                        bs.getSharedObject('footingMaterial')),
            actions=(("impactSound",self.dropSound,0.5,0.1)))

        self._powerupDist = []
        for p,freq in getDefaultPowerupDistribution():
            for i in range(int(freq)):
                self._powerupDist.append(p)

    def getRandomPowerupType(self, forceType=None, excludeTypes=None):
        if excludeTypes:
            #FIXME bsFootball.py:456
            #FIXME runaround and onslaught !
            excludeTypes.append('superStar')
            excludeTypes.append('speed')
            excludeTypes.append('iceCube')
            excludeTypes.append('surprise')
            excludeTypes.append('martyrdom')
        else:
            excludeTypes = []
        return PowerupFactory.getRandomPowerupType(self, forceType, excludeTypes)


def getDefaultPowerupDistribution():
    return (('tripleBombs',3),#3
            ('iceBombs',3),#3
            ('punch',3),#3
            ('impactBombs',3),#3
            ('landMines',2),#2
            ('stickyBombs',3),#3
            ('shield',2),#2
            ('health',1),#1
            ('curse',1),#1
            ('superStar',1),#1
            ('iceCube',2),#2
            ('surprise',1),#1
            ('martyrdom',2),#2 or 1 maybe
            ('speed',2))#2

class NewPowerup(Powerup):
    def __init__(self,position=(0,1,0),powerupType='tripleBombs',expire=True):
        """
        Create a powerup-box of the requested type at the requested position.

        see bs.Powerup.powerupType for valid type strings.
        """
        bs.Actor.__init__(self)

        factory = self.getFactory()
        self.powerupType = powerupType;
        self._powersGiven = False

        mod = factory.model
        rScl = [1.0]
        if powerupType == 'tripleBombs': tex = factory.texBomb
        elif powerupType == 'punch': tex = factory.texPunch
        elif powerupType == 'iceBombs': tex = factory.texIceBombs
        elif powerupType == 'impactBombs': tex = factory.texImpactBombs
        elif powerupType == 'landMines': tex = factory.texLandMines
        elif powerupType == 'stickyBombs': tex = factory.texStickyBombs
        elif powerupType == 'shield': tex = factory.texShield
        elif powerupType == 'health': tex = factory.texHealth
        elif powerupType == 'curse': tex = factory.texCurse
        elif powerupType == 'martyrdom': tex = factory.texMartyrdom
        elif powerupType == 'superStar':
             tex = factory.texSuperStar
             rScl = [0.1]
        elif powerupType == 'speed':tex = factory.texSpeed
        elif powerupType == 'surprise': tex = factory.texSurprise
        elif powerupType == 'iceCube':
             tex = factory.texIceCube
             rScl = [0.1]
        else: raise Exception("invalid powerupType: "+str(powerupType))

        if len(position) != 3: raise Exception("expected 3 floats for position")
        
        self.node = bs.newNode('prop',
                               delegate=self,
                               attrs={'body':'box',
                                      'position':position,
                                      'model':mod,
                                      'lightModel':factory.modelSimple,
                                      'shadowSize':0.5,
                                      'colorTexture':tex,
                                      'reflection':'powerup',
                                      'reflectionScale':rScl,
                                      'materials':(factory.powerupMaterial,
                                                   bs.getSharedObject('objectMaterial'))})

        # animate in..
        curve = bs.animate(self.node,"modelScale",{0:0,140:1.6,200:1})
        bs.gameTimer(200,curve.delete)

        if expire:
            bs.gameTimer(defaultPowerupInterval-2500,
                         bs.WeakCall(self._startFlashing))
            bs.gameTimer(defaultPowerupInterval-1000,
                         bs.WeakCall(self.handleMessage,bs.DieMessage()))
    
    def _flashBillboard(self,tex,spaz):
        spaz.node.billboardOpacity = 1.0
        spaz.node.billboardTexture = tex
        spaz.node.billboardCrossOut = False
        bs.animate(spaz.node,"billboardOpacity",{0:0.0,100:1.0,400:1.0,500:0.0})

    def _powerUpWearOffFlash(self,tex,spaz):
        if spaz.isAlive():
           spaz.node.billboardTexture = tex
           spaz.node.billboardOpacity = 1.0
           spaz.node.billboardCrossOut = True           
                
    def _startFlashing(self):
        if self.node.exists(): self.node.flashing = True       
      
    def handleMessage(self,m):
        self._handleMessageSanityCheck()

        if isinstance(m,PowerupAcceptMessage):
            factory = self.getFactory()
            if self.powerupType == 'health':
                bs.playSound(factory.healthPowerupSound,3,position=self.node.position)
            bs.playSound(factory.powerupSound,3,position=self.node.position)
            self._powersGiven = True
            self.handleMessage(bs.DieMessage())

        elif isinstance(m,_TouchedMessage):
            if not self._powersGiven:
                node = bs.getCollisionInfo("opposingNode")
                spaz = node.getDelegate()
                if spaz is not None and spaz.exists() and spaz.isAlive(): # pass deadbodies error
                    if self.powerupType == 'superStar':
                       tex = bs.Powerup.getFactory().texSuperStar
                       self._flashBillboard(tex,spaz)
                       def colorChanger():
                           if spaz.isAlive():
                              spaz.node.color = (random.random()*2,random.random()*2,random.random()*2)
                              spaz.node.highlight = (random.random()*2,random.random()*2,random.random()*2)
                       def checkStar(val):
                           self._powersGiven = True
                           if spaz.isAlive(): setattr(spaz.node,'invincible',val)
                           if val and spaz.isAlive():
                              if spaz.node.frozen:
                                 spaz.node.handleMessage(bs.ThawMessage())
                              bs.playSound(bs.Powerup.getFactory().superStarSound,position=spaz.node.position)
                              spaz.colorSet = bs.Timer(100,bs.Call(colorChanger),repeat=True)
                              if spaz._cursed:
                                 spaz._cursed = False
                                    # remove cursed material
                                 factory = spaz.getFactory()
                                 for attr in ['materials', 'rollerMaterials']:
                                     materials = getattr(spaz.node, attr)
                                     if factory.curseMaterial in materials:
                                         setattr(spaz.node, attr,
                                                 tuple(m for m in materials
                                                       if m != factory.curseMaterial))
                                 spaz.node.curseDeathTime = 0
                           if not val and spaz.isAlive():
                              spaz.node.color = spaz.getPlayer().color
                              spaz.node.highlight = spaz.getPlayer().highlight
                              spaz.colorSet = None
                              bs.playSound(bs.Powerup.getFactory().powerdownSound,position=spaz.node.position)
                              spaz.node.billboardOpacity = 0.0
                       checkStar(True)  
                       if self._powersGiven == True :                
                          spaz.node.miniBillboard1Texture = tex
                          t = bs.getGameTime()
                          spaz.node.miniBillboard1StartTime = t
                          spaz.node.miniBillboard1EndTime = t+gMythBPowerUpsWearOffTime
                          spaz._starWearOffTimer = bs.Timer(gMythBPowerUpsWearOffTime,bs.Call(checkStar,False))
                          spaz._starWearOffFlashTimer = bs.Timer(gMythBPowerUpsWearOffTime-2000,bs.WeakCall(self._powerUpWearOffFlash,tex,spaz))
                          self.handleMessage(bs.DieMessage())
                    elif self.powerupType == 'speed':
                     if bs.getActivity()._map.isHockey: #dont give speed if map is already hockey.
                        self.handleMessage(bs.DieMessage(immediate=True))
                     if not bs.getActivity()._map.isHockey:
                        spaz = node.getDelegate()
                        tex = bs.Powerup.getFactory().texSpeed
                        self._flashBillboard(tex,spaz)
                        def checkSpeed(val):
                            self._powersGiven = True
                            if spaz.isAlive(): setattr(spaz.node,'hockey',val)
                            if val and spaz.isAlive():
                               bs.playSound(bs.Powerup.getFactory().speedSound,position=spaz.node.position)
                            if not val and spaz.isAlive():
                               bs.playSound(bs.Powerup.getFactory().powerdownSound,position=spaz.node.position)
                               spaz.node.billboardOpacity = 0.0
                        checkSpeed(True)
                        if self._powersGiven == True :                
                           spaz.node.miniBillboard3Texture = tex
                           t = bs.getGameTime()
                           spaz.node.miniBillboard3StartTime = t
                           spaz.node.miniBillboard3EndTime = t+gMythBPowerUpsWearOffTime
                           spaz._speedWearOffTimer = bs.Timer(gMythBPowerUpsWearOffTime,bs.Call(checkSpeed,False))
                           spaz._speedWearOffFlashTimer = bs.Timer(gMythBPowerUpsWearOffTime-2000,bs.WeakCall(self._powerUpWearOffFlash,tex,spaz))
                           self.handleMessage(bs.DieMessage())
                    elif self.powerupType == 'iceCube':
                        spaz = node.getDelegate()
                        def checkFreezer(val):
                            self._powersGiven = True
                            if spaz.isAlive() and spaz.node.invincible:
                               bs.playSound(bs.Powerup.getFactory().blockSound,position=spaz.node.position)
                            if spaz.isAlive() and not spaz.node.invincible:
                               setattr(spaz,'frozen',val)
                            if val and spaz.isAlive() and not spaz.node.invincible:
                               spaz.node.frozen = 1
                               m = bs.newNode('math', owner=spaz, attrs={ 'input1':(0, 1.3, 0),
                                                                               'operation':'add' })
                               spaz.node.connectAttr('torsoPosition', m, 'input2')
                               opsText = bsUtils.PopupText("Oops!",color=(1,1,1),
                                                                   scale=0.9,
                                                                   offset=(0,-1,0)).autoRetain()
                               m.connectAttr('output', opsText.node, 'position')
                               bs.playSound(bs.Powerup.getFactory().iceCubeSound,position=spaz.node.position)
                            if not val and spaz.isAlive():
                               spaz.node.frozen = 0
                        checkFreezer(True)
                        if self._powersGiven == True :                
                           spaz._iceCubeWearOffTimer = bs.Timer(gMythBPowerUpsWearOffTime,bs.Call(checkFreezer,False))
                           self.handleMessage(bs.DieMessage())
                    elif self.powerupType == 'surprise':
                        self._powersGiven = True
                        spaz = node.getDelegate()
                        if spaz.isAlive():
                           bs.shakeCamera(1)
                           bsUtils.PopupText("Surprise!",color=(1,1,1),
                                                         scale=0.9,
                                                         offset=(0,-1,0),
                                                         position=(spaz.node.position[0],spaz.node.position[1]-1,spaz.node.position[2])).autoRetain()
                           bs.playSound(bs.Powerup.getFactory().surpriseSound,position=spaz.node.position)
                           bs.emitBGDynamics(position=spaz.node.position,
                                             velocity=(0,1,0),
                                             count=random.randrange(30,70),scale=0.5,chunkType='spark')
                           spaz.node.handleMessage("knockout",3000)
                           spaz.node.handleMessage("impulse",spaz.node.position[0],spaz.node.position[1],spaz.node.position[2],
                                                           -spaz.node.velocity[0],-spaz.node.velocity[1],-spaz.node.velocity[2],
                                                           400,400,0,0,-spaz.node.velocity[0],-spaz.node.velocity[1],-spaz.node.velocity[2])
                        if self._powersGiven == True :                                                           
                           self.handleMessage(bs.DieMessage())
                    elif self.powerupType == 'martyrdom':
                        spaz = node.getDelegate()
                        tex = bs.Powerup.getFactory().texMartyrdom
                        self._flashBillboard(tex,spaz)
                        def checkDead(): #FIXME
                         if spaz.hitPoints <= 0 and  ((spaz.lastPlayerHeldBy is not None
                            and spaz.lastPlayerHeldBy.exists()) or (spaz.lastPlayerAttackedBy is not None
                            and spaz.lastPlayerAttackedBy.exists() and bs.getGameTime() - spaz.lastAttackedTime < 4000)):
                            try: spaz.lastDeathPos = spaz.node.position #FIXME
                            except Exception: 
                                spaz.dropss = None
                            else: 
                               if not spaz.lastPlayerAttackedBy == spaz.getPlayer():
                                  dropBomb()
                                  spaz.dropss = None
                        def dropBomb():
                               bs.playSound(bs.Powerup.getFactory().martyrdomSound,position=spaz.lastDeathPos)
                               drop0 = bs.Bomb(position=(spaz.lastDeathPos[0]+0.43,spaz.lastDeathPos[1]+4,spaz.lastDeathPos[2]-0.25),
                                            velocity=(0,-6,0),sourcePlayer=spaz.getPlayer(),#some math for perfect triangle
                                            bombType='sticky').autoRetain()
                               drop1 = bs.Bomb(position=(spaz.lastDeathPos[0]-0.43,spaz.lastDeathPos[1]+4,spaz.lastDeathPos[2]-0.25),
                                            velocity=(0,-6,0),sourcePlayer=spaz.getPlayer(),
                                            bombType='sticky').autoRetain()
                               drop2 = bs.Bomb(position=(spaz.lastDeathPos[0],spaz.lastDeathPos[1]+4,spaz.lastDeathPos[2]+0.5),
                                            velocity=(0,-6,0),sourcePlayer=spaz.getPlayer(),
                                            bombType='sticky').autoRetain()                                       
                        def checkVal(val):
                            self._powersGiven = True
                            if val and spaz.isAlive():
                               m = bs.newNode('math', owner=spaz, attrs={ 'input1':(0, 1.3, 0),
                                                                               'operation':'add' })
                               spaz.node.connectAttr('torsoPosition', m, 'input2')
                               activatedText = bsUtils.PopupText("ACTIVATED",color=(1,1,1),
                                                                   scale=0.7,
                                                                   offset=(0,-1,0)).autoRetain()
                               m.connectAttr('output', activatedText.node, 'position')
                               bs.playSound(bs.Powerup.getFactory().martyrdomPickSound,position=spaz.node.position)
                               spaz.isDropped = True
                               spaz.dropss = bs.Timer(1,bs.Call(checkDead),repeat=True)
                        checkVal(True)
                        if self._powersGiven == True :
                           self.handleMessage(bs.DieMessage())
                    else:
                        node.handleMessage(PowerupMessage(self.powerupType,sourceNode=self.node))
                        
        elif isinstance(m,bs.DieMessage):
            if self.node.exists():
                if (m.immediate):
                    self.node.delete()
                else:
                    curve = bs.animate(self.node,"modelScale",{0:1,100:0})
                    bs.gameTimer(150,self.node.delete)

        elif isinstance(m,bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage())

        elif isinstance(m,bs.HitMessage):
            # dont die on punches (thats annoying)
            if m.hitType != 'punch':
                self.handleMessage(bs.DieMessage())
        else:
            bs.Actor.handleMessage(self,m)

bsPowerup.PowerupFactory = NewPowerupFactory
bsPowerup.Powerup = NewPowerup
