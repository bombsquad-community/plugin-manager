# ba_meta require api 7
from __future__ import annotations
from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
    from typing import Any, Sequence, Callable, List, Dict, Tuple, Optional, Union
    
from os import listdir,mkdir
from shutil import copy,copytree
import ba
import _ba
from bastd.ui.watch import WatchWindow as ww
from bastd.ui.popup import PopupWindow

#mod by ʟօʊքɢǟʀօʊ
#export replays to mods folder and share with your friends or have a backup

def Print(*args,color=None,top=None):
    out=""
    for arg in args:
        a=str(arg)
        out += a
    ba.screenmessage(out,color=color,top=top) 

def cprint(*args):
    out=""
    for arg in args:
        a=str(arg)
        out += a
    _ba.chatmessage(out)
    
internal_dir="/data/data/net.froemling.bombsquad/files/bombsquad_config/replays"
external_dir="/storage/emulated/0/Android/data/net.froemling.bombsquad/files/mods/replays"
#colors
pink=(1,0.2,0.8)
green=(0.4,1,0.4)
red=(1,0,0)

try:
    mkdir(external_dir)
    Print("You are ready to share replays",color=pink)
except FileExistsError:
    pass
    
class Help(PopupWindow):
    def __init__(self):
        uiscale = ba.app.ui.uiscale
        self.width = 800
        self.height = 300
          
        PopupWindow.__init__(self,
                             position=(0.0, 0.0),
                             size=(self.width, self.height),
                             scale=1.2,)
        
        ba.containerwidget(edit=self.root_widget,on_outside_click_call=self.close)
        ba.textwidget(parent=self.root_widget,position=(0 , self.height * 0.6),  text=f"•Replays are exported to\n {external_dir}\n•Importing replay and other features comming in v1.2")
    
    def close(self):
        ba.playsound(ba.getsound('swish'))
        ba.containerwidget(edit=self.root_widget, transition="out_right",)


class SettingWindow():
    def __init__(self):
        self.draw_ui()
        self.selected_widget = None
        self.selected_name= None
    
    def on_select_text(self,widget,name):        
        if self.selected_widget is not None:                                      
            ba.textwidget(edit=self.selected_widget,color=(1,1,1))                        
        ba.textwidget(edit=widget,color=(1,1,0))
        self.selected_name = name
        self.selected_widget = widget
        
    def draw_ui(self):
        self.uiscale = ba.app.ui.uiscale
        self.root=ba.Window(ba.containerwidget(size=(900, 670),on_outside_click_call=self.close,transition="in_right")).get_root_widget()

        ba.textwidget(
            parent=self.root,
            size=(200, 100),
            position=(150, 550),
            scale=2,
            selectable=False,
            h_align="center",
            v_align="center",
            text="ShareReplay",
            color=green)
            
        ba.buttonwidget(
            parent=self.root,
            position=(400,580),
            size=(35,35),
            label="Help",
            on_activate_call=Help)
    
        ba.buttonwidget(
            parent=self.root,
            position=(770, 460),
            size=(90, 70),
            scale=1.5,
            label="EXPORT",
            on_activate_call=self.export)
        
        self.close_button = ba.buttonwidget(
            parent=self.root,
            position=(820, 590),
            size=(35, 35),
            icon=ba.gettexture("crossOut"),
            icon_color=(1, 0.2, 0.2),
            scale=2,
            color=(1, 0.2, 0.2),
            extra_touch_border_scale=3,
            on_activate_call=self.close)
        
        scroll=ba.scrollwidget(
            parent=self.root,
            size=(500,400),
            position=(200,150))
        self.scroll=ba.columnwidget(parent=scroll,size=(500,900),selection_loops_to_parent=True,single_depth=True)
        
        height=900    
        for i in listdir(internal_dir):
            height-=40
            a=i
            i = ba.textwidget(
                parent=self.scroll, 
                size=(500,50), 
                text= i.split(".")[0],
                position=(10,height),
                selectable=True,
                max_chars=40,
                click_activate=True,)
                
            ba.textwidget(edit=i,on_activate_call=ba.Call(self.on_select_text,i,a))
               
        
    def export(self):
      if self.selected_name is None:
          Print("Select a replay",color=red)
          return      
      copy(internal_dir+"/"+self.selected_name,external_dir+"/"+self.selected_name)      
      Print(self.selected_name[0:-4]+" exported", top=True,color=pink)#image={"texture":ba.gettexture("bombColor"),"tint_texture":None,"tint_color":None,"tint2_color":None})
      
    def close(self):
        ba.playsound(ba.getsound('swish'))
        ba.containerwidget(edit=self.root, transition="out_right",)    
        

# ++++++++++++++++for keyboard navigation++++++++++++++++

        #ba.widget(edit=self.enable_button, up_widget=decrease_button, down_widget=self.lower_text,left_widget=save_button, right_widget=save_button)        

# --------------------------------------------------------------------------------------------------

ww.__old_init__=ww.__init__

def new_init(self,transition="in_right",origin_widget=None):
    self.__old_init__(transition,origin_widget)
    self._share_button = ba.buttonwidget(
        parent=self._root_widget,
        position=(self._width*0.70, self._height*0.80),
        size=(220, 60),
        scale=1.0,
        color=green,
        icon=ba.gettexture('usersButton'),
        iconscale=1.5,
        label="SHARE REPLAY",
        on_activate_call=SettingWindow)
        
        
# ba_meta export plugin

class main(ba.Plugin):
    def on_app_running(self):
       
        ww.__init__=new_init
          
    def has_settings_ui(self):
        return True
    
    def show_settings_ui(self,button):
        SettingWindow()
        
    