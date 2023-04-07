# -*- coding: utf-8 -*-
import bs                           #Created By MythB # http://github.com/MythB
from bsSpaz import *
import bsSpaz
import bsUtils
import random
import bsInternal
import MythBAdminList as mbal

class PermissionEffect(object):
    def __init__(self,position = (0,1,0),owner = None,prefix = '',posPrefix = (0, 1.8, 0),isAdmin = False,prefixAnimate = False,particles = False):
        self.position = position
        self.owner = owner
        
        def a():
            self.emit()
             
        if particles:
            self.timer = bs.Timer(10,bs.Call(a),repeat = True)

        m = bs.newNode('math', owner=self.owner, attrs={'input1': posPrefix, 'operation': 'add'})
        self.owner.connectAttr('position', m, 'input2')

        self._Text = bs.newNode('text',
                                      owner=self.owner,
                                      attrs={'text':prefix,
                                             'inWorld':True,
                                             'shadow':1.2,
                                             'flatness':1.0,
                                             'scale':0.0,
                                             'vAlign':'center',
                                             'hAlign':'center'})
                                             
        m.connectAttr('output', self._Text, 'position')
        
        if not isAdmin:
            bs.animate(self._Text, 'scale', {0: 0.0, 1000: 0.01})
        if prefixAnimate:
            bs.animate(self._Text, 'opacity', {0: 0.0, 500: 1.0,1000: 1.0, 1500: 0},loop=True)
        if isAdmin: #glow effect for  admins
            bs.animate(self._Text, 'scale', {0: 0.0, 1000: 0.0165})
            self._Adminlight = bs.newNode('light',
                                      owner=self.owner,
                                      attrs={'intensity':0.5, #'volumeIntensityScale':0.1,
                                             'heightAttenuated':False,
                                             'radius':0.1,
                                             'color': self.owner.color})
            self.owner.connectAttr('position',self._Adminlight,'position')
    def emit(self):
        if self.owner.exists():
            vel = 4
            bs.emitBGDynamics(position=(self.owner.torsoPosition[0]-0.25+random.random()*0.5,self.owner.torsoPosition[1]-0.25+random.random()*0.5,
                              self.owner.torsoPosition[2]-0.25+random.random()*0.5),velocity=((-vel+(random.random()*(vel*2)))+self.owner.velocity[0]*2,
                              (-vel+(random.random()*(vel*2)))+self.owner.velocity[1]*4,(-vel+(random.random()*(vel*2)))+self.owner.velocity[2]*2),
                              count=10,
                              scale=0.3+random.random()*1.1,
                              spread=0.1,
                              chunkType='sweat')
        
def __init__(self,color=(1,1,1),highlight=(0.5,0.5,0.5),character="Spaz",player=None,powerupsExpire=True):
        """
        Create a spaz for the provided bs.Player.
        Note: this does not wire up any controls;
        you must call connectControlsToPlayer() to do so.
        """
        # convert None to an empty player-ref
        if player is None: player = bs.Player(None)
        
        Spaz.__init__(self,color=color,highlight=highlight,character=character,sourcePlayer=player,startInvincible=True,powerupsExpire=powerupsExpire)
        self.lastPlayerAttackedBy = None # FIXME - should use empty player ref
        self.lastAttackedTime = 0
        self.lastAttackedType = None
        self.heldCount = 0
        self.lastPlayerHeldBy = None # FIXME - should use empty player ref here
        self._player = player
        
        profile = self._player.get_account_id()

        if profile in mbal.AdminList :   ##u'\u2B50' # ADMIN
           PermissionEffect(owner = self.node,prefix = bs.getSpecialChar('crown'),posPrefix = (0, 2.2, 0),particles=True,isAdmin=True,prefixAnimate = True)
        if profile in mbal.Fighter1stList : #1st fighter
           PermissionEffect(owner = self.node,prefix = bs.getSpecialChar('trophy4'),posPrefix =(-0.3, 1.8, 0),particles=True)
        if profile in mbal.Fighter2nd3rd : #2. 3. fighter
           PermissionEffect(owner = self.node,prefix = bs.getSpecialChar('trophy3'),posPrefix =(-0.3, 1.8, 0))
        if profile in mbal.FighterTop15List : #top15 fighter
           PermissionEffect(owner = self.node,prefix = bs.getSpecialChar('trophy2'),posPrefix =(-0.3, 1.8, 0))
        if profile in mbal.Scorer1stList : #1st scorer
           PermissionEffect(owner = self.node,prefix = bs.getSpecialChar('trophy4'),posPrefix =(0.3, 1.8, 0),particles=True)
        if profile in mbal.Scorer2nd3rdList : #2. 3. scorer
           PermissionEffect(owner = self.node,prefix = bs.getSpecialChar('trophy3'),posPrefix =(0.3, 1.8, 0))
        if profile in mbal.ScorerTop15List : #top15 scorer
           PermissionEffect(owner = self.node,prefix = bs.getSpecialChar('trophy2'),posPrefix =(0.3, 1.8, 0))
        if profile in mbal.autoKickList : #warn and kick him every time
           clID = self._player.getInputDevice().getClientID()
           kickName = self._player.getName()
           bs.screenMessage(kickName + ' in blacklist' + ' auto kicking in 3 seconds',color = (0,0.9,0))
           def kickIt():
               bsInternal._disconnectClient(clID)
           bs.gameTimer(4000,bs.Call(kickIt))

        # grab the node for this player and wire it to follow our spaz (so players' controllers know where to draw their guides, etc)
        if player.exists():
            playerNode = bs.getActivity()._getPlayerNode(player)
            self.node.connectAttr('torsoPosition',playerNode,'position')

    

bsSpaz.PlayerSpaz.__init__ = __init__




