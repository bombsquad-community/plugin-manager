import bs                  #Created By MythB # http://github.com/MythB
import bsUI
import bsInternal
	
def _onPartyMemberPress(self,clientID,isHost,widget):
    # if we're the host, pop up 'kick' options for all non-host members
    if bsInternal._getForegroundHostSession() is not None:
        kickStr = bs.Lstr(resource='kickText')
    else:
        # kick-votes appeared in build 14248
        if bsInternal._getConnectionToHostInfo().get('buildNumber',0) < 14248:
            return
        kickStr = bs.Lstr(resource='kickVoteText')
    p = bsUI.PopupMenuWindow(position=widget.getScreenSpaceCenter(),
                        scale = 2.3 if bsUI.gSmallUI else 1.65 if bsUI.gMedUI else 1.23,
                        choices=['kickOrg', "kick", "remove", "kill", "ban", "unban", "gj", "amnesty", "knock", "curse", "heal", "shield", "punch", "freeze", "thaw", "headless", "celebrate", "list", "headlessall", "healall", "shieldall", "punchall", "killall", "knockall", "freezeall", "thawall", "curseall", "celebrateall", "slow", "camera", "end", "help"],
                        choicesDisplay=[kickStr, "Kick", "Remove", "Kill", "Ban", "Unban", "GoodJob!", "Amnesty", "Knock", "Curse", "Heal", "Shield", "Punch", "Freeze", "Thaw", "Headless", "Celebrate", "List", "HeadlessAll", "HealAll", "ShieldAll", "PunchAll", "KillAll", "KnockAll", "FreezeAll", "ThawAll", "CurseAll", "CelebrateAll", "Slow", "Camera", "End", "Help"],
                        currentChoice='kickOrg',
                        delegate=self).getRootWidget()
    self._popupType = 'partyMemberPress'
    self._popupPartyMemberClientID = clientID
    self._popupPartyMemberIsHost = isHost 
    
    
def popupMenuSelectedChoice(self,popupWindow,choice):

    if choice == "kickOrg":
        if self._popupPartyMemberIsHost:
            bs.playSound(bs.getSound('error'))
            bs.screenMessage(bs.Lstr(resource='internal.cantKickHostError'),color=(1,0,0))
        else:
            #print self._popupPartyMemberClientID
            result = bsInternal._disconnectClient(self._popupPartyMemberClientID)
            if not result:
                bs.playSound(bs.getSound('error'))
                bs.screenMessage(bs.Lstr(resource='getTicketsWindow.unavailableText'),color=(1,0,0))
                
    elif choice == "kick":
        bsInternal._chatMessage("/"+choice+" "+ (str(self._popupPartyMemberClientID)))
        
    elif choice == "ban":
         for client in bsInternal._getGameRoster():
             if client['clientID'] == self._popupPartyMemberClientID:
                try:
                    bsInternal._chatMessage("/"+choice+" "+ str(client['players'][0]['name']))
                except:
                    pass
                
    elif choice == "unban":
         for client in bsInternal._getGameRoster():
             if client['clientID'] == self._popupPartyMemberClientID:
                try:
                    bsInternal._chatMessage("/"+choice+" "+ str(client['players'][0]['name']))
                except:
                    pass
                
    elif choice == "remove":
         for client in bsInternal._getGameRoster():
             if client['clientID'] == self._popupPartyMemberClientID:
                try:
                    bsInternal._chatMessage("/"+choice+" "+ str(client['players'][0]['name']))
                except:
                    pass
                
    elif choice == "curse":
         for client in bsInternal._getGameRoster():
             if client['clientID'] == self._popupPartyMemberClientID:
                try:
                    bsInternal._chatMessage("/"+choice+" "+ str(client['players'][0]['name']))
                except:
                    pass
                    
    elif choice == "celebrate":
         for client in bsInternal._getGameRoster():
             if client['clientID'] == self._popupPartyMemberClientID:
                try:
                    bsInternal._chatMessage("/"+choice+" "+ str(client['players'][0]['name']))
                except:
                    pass
                
    elif choice == "freeze":
         for client in bsInternal._getGameRoster():
             if client['clientID'] == self._popupPartyMemberClientID:
                try:
                    bsInternal._chatMessage("/"+choice+" "+ str(client['players'][0]['name']))
                except:
                    pass
                
    elif choice == "thaw":
         for client in bsInternal._getGameRoster():
             if client['clientID'] == self._popupPartyMemberClientID:
                try:
                    bsInternal._chatMessage("/"+choice+" "+ str(client['players'][0]['name']))
                except:
                    pass
                
    elif choice == "kill":
         for client in bsInternal._getGameRoster():
             if client['clientID'] == self._popupPartyMemberClientID:
                try:
                    bsInternal._chatMessage("/"+choice+" "+ str(client['players'][0]['name']))
                except:
                    pass
                    
    elif choice == "knock":
         for client in bsInternal._getGameRoster():
             if client['clientID'] == self._popupPartyMemberClientID:
                try:
                    bsInternal._chatMessage("/"+choice+" "+ str(client['players'][0]['name']))
                except:
                    pass
                    
    elif choice == "punch":
         for client in bsInternal._getGameRoster():
             if client['clientID'] == self._popupPartyMemberClientID:
                try:
                    bsInternal._chatMessage("/"+choice+" "+ str(client['players'][0]['name']))
                except:
                    pass
                
    elif choice == "headless":
         for client in bsInternal._getGameRoster():
             if client['clientID'] == self._popupPartyMemberClientID:
                try:
                    bsInternal._chatMessage("/"+choice+" "+ str(client['players'][0]['name']))
                except:
                    pass
                    
    elif choice == "heal":
         for client in bsInternal._getGameRoster():
             if client['clientID'] == self._popupPartyMemberClientID:
                try:
                    bsInternal._chatMessage("/"+choice+" "+ str(client['players'][0]['name']))
                except:
                    pass
                    
    elif choice == "shield":
         for client in bsInternal._getGameRoster():
             if client['clientID'] == self._popupPartyMemberClientID:
                try:
                    bsInternal._chatMessage("/"+choice+" "+ str(client['players'][0]['name']))
                except:
                    pass
                    
    elif choice == "gj":
         for client in bsInternal._getGameRoster():
             if client['clientID'] == self._popupPartyMemberClientID:
                try:
                    bsInternal._chatMessage("/"+choice+" "+ str(client['players'][0]['name']))
                except:
                    pass
                
    elif choice == "list":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "camera":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "slow":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "amnesty":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "help":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "end":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "headlessall":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "killall":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "freezeall":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "curseall":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "shieldall":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "healall":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "knockall":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "thawall":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "punchall":
        bsInternal._chatMessage("/"+choice)
        
    elif choice == "celebrateall":
        bsInternal._chatMessage("/"+choice)
        
    elif self._popupType == 'menu':
        if choice in ('mute', 'unmute'):
           bsConfig = bs.getConfig()
           bsConfig['Chat Muted'] = (choice == 'mute')
           bs.writeConfig()
           bs.applySettings()
           self._update()
    
    else:
        bs.textWidget(edit=self._textField,text='')
          
bsUI.PartyWindow._onPartyMemberPress = _onPartyMemberPress
bsUI.PartyWindow.popupMenuSelectedChoice = popupMenuSelectedChoice