#mood light plugin by ʟօʊքɢǟʀօʊ

# ba_meta require api 7
from __future__ import annotations
from typing import TYPE_CHECKING, cast

import ba
import _ba
import random
from ba._map import Map
from bastd import mainmenu
from bastd.ui.party import PartyWindow
from bastd.gameutils import SharedObjects
from time import sleep
if TYPE_CHECKING:
    from typing import Any, Sequence, Callable, List, Dict, Tuple, Optional, Union

class SettingWindow(ba.Window):
        def __init__(self):
            global Ldefault,Udefault
            Ldefault=5 
            Udefault=20
            self.draw_ui()
        
        def increase_limit(self):
            global Ldefault,Udefault
            try:   
                if Udefault>=29 and self.selected=="upper":
                    ba.textwidget(edit=self.warn_text,text="Careful!You risk get blind beyond this point")
                elif self.selected=="lower" and Ldefault>=-20 or self.selected=="upper" and Udefault<=30:
                    ba.textwidget(edit=self.warn_text,text="")
            
                if self.selected=="lower":
                    Ldefault += 1
                    ba.textwidget(edit=self.lower_text,text=str(Ldefault))
                elif self.selected=="upper":
                    Udefault+=1
                    ba.textwidget(edit=self.upper_text,text=str(Udefault))
            except AttributeError:
                ba.textwidget(edit=self.warn_text,text="Click on number to select it")   
                        
        def decrease_limit(self):              
            global Ldefault,Udefault
            try: 
                if Ldefault<=-19 and self.selected == "lower":
                    ba.textwidget(edit=self.warn_text,text="DON'T BE AFRAID OF DARK,IT'S A PLACE WHERE YOU CAN HIDE")
                elif (self.selected == "upper" and Udefault <=30) or (self.selected== "lower" and Ldefault>=-20):
                    ba.textwidget(edit=self.warn_text,text="")
            
            
                if self.selected=="lower":
                    Ldefault -= 1
                    ba.textwidget(edit=self.lower_text,text=str(Ldefault))
                elif self.selected=="upper":
                    Udefault -=1
                    ba.textwidget(edit=self.upper_text,text=str(Udefault))
            except AttributeError:
                ba.textwidget(edit=self.warn_text,text="Click on number to select it")            
        
        def on_text_click(self,selected):
            self.selected=selected
            if selected=="upper":                
                ba.textwidget(edit=self.upper_text,color=(0,0,1))
                ba.textwidget(edit=self.lower_text,color=(1,1,1))
            elif selected=="lower":
                ba.textwidget(edit=self.lower_text,color=(0,0,1))
                ba.textwidget(edit=self.upper_text,color=(1,1,1))
            else:
                ba.screenmessage("this should't happen from on_text_click")
                                        
        def draw_ui(self):
            self.uiscale=ba.app.ui.uiscale
            
            super().__init__(
                root_widget=ba.containerwidget(
                    size=(800, 800),
                    on_outside_click_call=self.close,
                    transition="in_right",))
        
            increase_button=ba.buttonwidget(
                parent=self._root_widget,
                position=(250,100),
                size=(50,50),
                label="+",
                scale=2,
                on_activate_call=self.increase_limit)
                
            decrease_button=ba.buttonwidget(
                parent=self._root_widget,
                position=(100,100),
                size=(50,50),
                scale=2,
                label="-",
                on_activate_call=self.decrease_limit)
                
            
            self.lower_text=ba.textwidget(
                parent=self._root_widget,
                size=(200,100),
                scale=2,
                position=(100,300),
                h_align="center",
                v_align="center",
                maxwidth=400.0,
                text=str(Ldefault),
                click_activate=True,
                selectable=True)
                 
            self.upper_text=ba.textwidget(
                parent=self._root_widget,
                size=(200,100),
                scale=2,
                position=(500,300),
                h_align="center",
                v_align="center",
                maxwidth=400.0,
                text=str(Udefault),
                click_activate=True,
                selectable=True)              
                                                          
            self.warn_text=ba.textwidget(
                parent=self._root_widget,
                text="",
                size=(400,100),
                position=(200,500),
                h_align="center",
                v_align="center",
                maxwidth=600)
               
            close_button=ba.buttonwidget(
                parent=self._root_widget,
                position=(700,650),
                size=(100,100),
                icon=ba.gettexture('crossOut'),
                on_activate_call=self.close,
                color=(0.8,0.2,0.2))
            
            ba.containerwidget(edit=self._root_widget, cancel_button=close_button)
            ba.textwidget(edit=self.upper_text,on_activate_call=ba.Call(self.on_text_click,"upper"))
            ba.textwidget(edit=self.lower_text,on_activate_call=ba.Call(self.on_text_click,"lower"))
                
        def close(self):            
            ba.containerwidget(edit=self._root_widget, transition="out_right")


# ba_meta export plugin
class moodlight(ba.Plugin):
    def __init__(self):
        pass
    Map._old_init = Map.__init__
    
    def on_app_running(self):
        try:
            SettingWindow()
            _ba.timer(0.5, self.on_chat_message, True)  
        except Exception as err:
            ba.screenmessage(str(err)) 
    
    def on_chat_message(self):
        messages=_ba.get_chat_messages() 
        if len(messages)>0:
            lastmessage=messages[-1].split(":")[-1].strip().lower()
            if lastmessage in ("/mood light","/mood lighting","/mood_light","/mood_lighting","/moodlight","ml"):
                _ba.chatmessage("Mood light settings opened")
                SettingWindow()
        
    def on_plugin_manager_prompt(self):
        SettingWindow()
    
    def _new_init(self, vr_overlay_offset: Optional[Sequence[float]] = None) -> None:
        self._old_init(vr_overlay_offset)   
        in_game = not isinstance(_ba.get_foreground_host_session(), mainmenu.MainMenuSession)
        if not in_game: return
        
        gnode = _ba.getactivity().globalsnode

        def changetint(self):
        	   ba.animate_array(gnode, 'tint', 3, {
                       0.0: gnode.tint, 
                       1.0: (random.randrange(Ldefault,Udefault)/10, random.randrange(Ldefault,Udefault)/10, random.randrange(Ldefault,Udefault)/10) 
               }) 
        _ba.timer(0.3, changetint, repeat= True) 
 
    
    Map.__init__ = _new_init
