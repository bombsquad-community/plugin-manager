# Ported by brostos to api 8
# Tool used to make porting easier.(https://github.com/bombsquad-community/baport)
"""
I apreciate any kind of modification. So feel free to use or edit code or change credit string.... no problem.

really awsome servers:
    Bombsquad Consultancy Service - https://discord.gg/2RKd9QQdQY
    bombspot - https://discord.gg/ucyaesh
    cyclones - https://discord.gg/pJXxkbQ7kH

how to use:
    Account -> PlayerProfile -> Edit(new profile -> edit)
    Open profile you like (every profile has dirrent tags, settings (Configs))
    enable tag for profile you like, edit tag you want. enable cool flashy animation
"""

from __future__ import annotations
from bauiv1lib.profile.edit import EditProfileWindow
from bauiv1lib.colorpicker import ColorPicker
from bauiv1lib.popup import PopupMenu
from bascenev1lib.actor.playerspaz import PlayerSpaz
from baenv import TARGET_BALLISTICA_BUILD as build_number
import babase
import bauiv1 as bui
import bascenev1 as bs
import _babase

from typing import (
    Tuple,
    Optional,
    Sequence,
    Union,
    Callable,
    Any,
    List,
    cast
)

__version__ = 2.0
__author__ = "pranav1711#2006"


# Default Confings/Settings
Configs = {
    "enabletag": False,
    "tag": "",
    "scale": "medium",
    "opacity": 1.0,
    "shadow": 0.0,
    "animtag": False,
    "frequency": 0.5
}

# Useful global fucntions


def setconfigs() -> None:
    """
    Set required defualt configs for mod
    """
    cnfg = babase.app.config
    profiles = cnfg['Player Profiles']
    if not "TagConf" in cnfg:
        cnfg["TagConf"] = {}
    for p in profiles:
        if not p in cnfg["TagConf"]:
            cnfg["TagConf"][str(p)] = Configs
    babase.app.config.apply_and_commit()


def getanimcolor(name: str) -> dict:
    """
    Returns dictnary of colors with prefective time -> {seconds: (r, g, b)}
    """
    freq = babase.app.config['TagConf'][str(name)]['frequency']
    s1 = 0.0
    s2 = s1 + freq
    s3 = s2 + freq

    animcolor = {
        s1: (1, 0, 0),
        s2: (0, 1, 0),
        s3: (0, 0, 1)
    }
    return animcolor


def gethostname() -> str:
    """
    Return player name, by using -1 only host can use tags.
    """
    session = bs.get_foreground_host_session()
    with session.context:
        for player in session.sessionplayers:
            if player.inputdevice.client_id == -1:
                name = player.getname(full=True, icon=False)
                break
        if name == bui.app.plus.get_v1_account_name:
            return '__account__'
        return name


# Dummy functions for extend functionality for class object
PlayerSpaz.init = PlayerSpaz.__init__
EditProfileWindow.init = EditProfileWindow.__init__

# PlayerSpaz object at -> bascenev1lib.actor.playerspaz


def NewPlayerSzapInit(self,
                      player: bs.Player,
                      color: Sequence[float] = (1.0, 1.0, 1.0),
                      highlight: Sequence[float] = (0.5, 0.5, 0.5),
                      character: str = 'Spaz',
                      powerups_expire: bool = True) -> None:
    self.init(player, color, highlight, character, powerups_expire)
    self.curname = gethostname()

    try:
        cnfg = babase.app.config["TagConf"]
        if cnfg[str(self.curname)]["enabletag"]:
            # Tag node
            self.mnode = bs.newnode('math', owner=self.node, attrs={
                                    'input1': (0, 1.5, 0), 'operation': 'add'})
            self.node.connectattr('torso_position', self.mnode, 'input2')

            tagtext = cnfg[str(self.curname)]["tag"]
            opacity = cnfg[str(self.curname)]["opacity"]
            shadow = cnfg[str(self.curname)]["shadow"]
            sl = cnfg[str(self.curname)]["scale"]
            scale = 0.01 if sl == 'mediam' else 0.009 if not sl == 'large' else 0.02

            self.Tag = bs.newnode(
                type='text',
                owner=self.node,
                attrs={
                    'text': str(tagtext),
                    'in_world': True,
                    'shadow': shadow,
                    'color': (0, 0, 0),
                    'scale': scale,
                    'opacity': opacity,
                    'flatness': 1.0,
                    'h_align': 'center'})
            self.mnode.connectattr('output', self.Tag, 'position')

            if cnfg[str(self.curname)]["animtag"]:
                kys = getanimcolor(self.curname)
                bs.animate_array(node=self.Tag, attr='color', size=3, keys=kys, loop=True)
    except Exception:
        pass


def NewEditProfileWindowInit(self,
                             existing_profile: Optional[str],
                             in_main_menu: bool,
                             transition: str = 'in_right') -> None:
    """
    New boilerplate for editprofilewindow, addeds button to call TagSettings window
    """
    self.existing_profile = existing_profile
    self.in_main_menu = in_main_menu
    self.init(existing_profile, in_main_menu, transition)

    v = self._height - 115.0
    x_inset = self._x_inset
    b_width = 50
    b_height = 30

    self.tagwinbtn = bui.buttonwidget(
        parent=self._root_widget,
        autoselect=True,
        position=(505 + x_inset, v - 38 - 15),
        size=(b_width, b_height),
        color=(0.6, 0.5, 0.6),
        label='Tag',
        button_type='square',
        text_scale=1.2,
        on_activate_call=babase.Call(_on_tagwinbtn_press, self))


def _on_tagwinbtn_press(self):
    """
    Calls tag config window passes all paramisters 
    """
    bui.containerwidget(edit=self._root_widget, transition='out_scale')
    bui.app.ui_v1.set_main_menu_window(
        TagWindow(self.existing_profile,
                  self.in_main_menu,
                  self._name,
                  transition='in_right').get_root_widget(), from_window=self._root_widget)


# ba_meta require api 8
# ba_meta export plugin
class Tag(babase.Plugin):
    def __init__(self) -> None:
        """
        Tag above actor player head, replacing PlayerSpaz class for getting actor,
        using EditProfileWindow for UI.
        """
        if _babase.env().get("build_number", 0) >= 20327:
            setconfigs()
            self.Replace()

    def Replace(self) -> None:
        """
        Replacing bolierplates no harm to relative funtionality only extending 
        """
        PlayerSpaz.__init__ = NewPlayerSzapInit
        EditProfileWindow.__init__ = NewEditProfileWindowInit


class TagWindow(bui.Window):

    def __init__(self,
                 existing_profile: Optional[str],
                 in_main_menu: bool,
                 profilename: str,
                 transition: Optional[str] = 'in_right'):
        self.existing_profile = existing_profile
        self.in_main_menu = in_main_menu
        self.profilename = profilename

        uiscale = bui.app.ui_v1.uiscale
        self._width = 870.0 if uiscale is babase.UIScale.SMALL else 670.0
        self._height = (390.0 if uiscale is babase.UIScale.SMALL else
                        450.0 if uiscale is babase.UIScale.MEDIUM else 520.0)
        extra_x = 100 if uiscale is babase.UIScale.SMALL else 0
        self.extra_x = extra_x
        top_extra = 20 if uiscale is babase.UIScale.SMALL else 0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition=transition,
                scale=(2.06 if uiscale is babase.UIScale.SMALL else
                       1.4 if uiscale is babase.UIScale.MEDIUM else 1.0)))

        self._back_button = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            selectable=False,  # FIXME: when press a in text field it selets to button
            position=(52 + self.extra_x, self._height - 60),
            size=(60, 60),
            scale=0.8,
            label=babase.charstr(babase.SpecialChar.BACK),
            button_type='backSmall',
            on_activate_call=self._back)
        bui.containerwidget(edit=self._root_widget, cancel_button=self._back_button)

        self._save_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width - (177 + extra_x),
                      self._height - 60),
            size=(155, 60),
            color=(0, 0.7, 0.5),
            autoselect=True,
            selectable=False,  # FIXME: when press a in text field it selets to button
            scale=0.8,
            label=babase.Lstr(resource='saveText'),
            on_activate_call=self.on_save)
        bui.widget(edit=self._save_button, left_widget=self._back_button)
        bui.widget(edit=self._back_button, right_widget=self._save_button)
        bui.containerwidget(edit=self._root_widget, start_button=self._save_button)

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(0, self._height - 52 - top_extra),
            size=(self._width, 25),
            text='Tag',
            color=bui.app.ui_v1.title_color,
            scale=1.5,
            h_align='center',
            v_align='top')

        self._scroll_width = self._width - (100 + 2 * extra_x)
        self._scroll_height = self._height - 115.0
        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 724.0
        self._spacing = 32
        self._extra_button_spacing = self._spacing * 2.5

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(50 + extra_x, 50),
            simple_culling_v=20.0,
            highlight=False,
            size=(self._scroll_width,
                  self._scroll_height),
            selection_loops_to_parent=True)
        bui.widget(edit=self._scrollwidget, right_widget=self._scrollwidget)

        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width,
                  self._sub_height),
            background=False,
            selection_loops_to_parent=True)

        v = self._sub_height - 35
        v -= self._spacing * 1.2

        self._prof = babase.app.config["TagConf"][self.profilename]
        self.enabletagcb = bui.checkboxwidget(
            parent=self._subcontainer,
            autoselect=False,
            position=(10.0, v + 30),
            size=(10, 10),
            text='Enable Tag',
            textcolor=(0.8, 0.8, 0.8),
            value=self._prof['enabletag'],
            on_value_change_call=babase.Call(self.change_val, [f'{self.profilename}', 'enabletag']),
            scale=1.1 if uiscale is babase.UIScale.SMALL else 1.5,
            maxwidth=430)

        self.tag_text = bui.textwidget(
            parent=self._subcontainer,
            text='Tag',
            position=(25.0, v - 30),
            flatness=1.0,
            scale=1.55,
            maxwidth=430,
            h_align='center',
            v_align='center',
            color=(0.8, 0.8, 0.8))

        self.tagtextfield = bui.textwidget(
            parent=self._subcontainer,
            position=(100.0, v - 45),
            size=(350, 50),
            text=self._prof["tag"],
            h_align='center',
            v_align='center',
            max_chars=16,
            autoselect=True,
            editable=True,
            padding=4,
            color=(0.9, 0.9, 0.9, 1.0))

        self.tag_color_text = bui.textwidget(
            parent=self._subcontainer,
            text='Color',
            position=(40.0, v - 80),
            flatness=1.0,
            scale=1.25,
            maxwidth=430,
            h_align='center',
            v_align='center',
            color=(0.8, 0.8, 0.8))

        self.tag_scale_text = bui.textwidget(
            parent=self._subcontainer,
            text='Scale',
            position=(40.0, v - 130),
            flatness=1.0,
            scale=1.25,
            maxwidth=430,
            h_align='center',
            v_align='center',
            color=(0.8, 0.8, 0.8))

        self.tag_scale_button = PopupMenu(
            parent=self._subcontainer,
            position=(330.0, v - 145),
            width=150,
            autoselect=True,
            on_value_change_call=bs.WeakCall(self._on_menu_choice),
            choices=['large', 'medium', 'small'],
            button_size=(150, 50),
            # choices_display=('large', 'medium', 'small'),
            current_choice=self._prof["scale"])

        CustomConfigNumberEdit(
            parent=self._subcontainer,
            position=(40.0, v - 180),
            xoffset=65,
            displayname='Opacity',
            configkey=['TagConf', f'{self.profilename}', 'opacity'],
            changesound=False,
            minval=0.5,
            maxval=2.0,
            increment=0.1,
            textscale=1.25)

        CustomConfigNumberEdit(
            parent=self._subcontainer,
            position=(40.0, v - 230),
            xoffset=65,
            displayname='Shadow',
            configkey=['TagConf', f'{self.profilename}', 'shadow'],
            changesound=False,
            minval=0.0,
            maxval=2.0,
            increment=0.1,
            textscale=1.25)

        self.enabletaganim = bui.checkboxwidget(
            parent=self._subcontainer,
            autoselect=True,
            position=(10.0, v - 280),
            size=(10, 10),
            text='Animate tag',
            textcolor=(0.8, 0.8, 0.8),
            value=self._prof['enabletag'],
            on_value_change_call=babase.Call(self.change_val, [f'{self.profilename}', 'animtag']),
            scale=1.1 if uiscale is babase.UIScale.SMALL else 1.5,
            maxwidth=430)

        CustomConfigNumberEdit(
            parent=self._subcontainer,
            position=(40.0, v - 330),
            xoffset=65,
            displayname='Frequency',
            configkey=['TagConf', f'{self.profilename}', 'frequency'],
            changesound=False,
            minval=0.1,
            maxval=5.0,
            increment=0.1,
            textscale=1.25)

    def _back(self) -> None:
        """
        transit window into back window
        """
        bui.containerwidget(edit=self._root_widget,
                            transition='out_scale')
        bui.app.ui_v1.set_main_menu_window(EditProfileWindow(
            self.existing_profile,
            self.in_main_menu,
            transition='in_left').get_root_widget(), from_window=self._root_widget)

    def change_val(self, config: List[str], val: bool) -> None:
        """
        chamges the value of check boxes
        """
        cnfg = babase.app.config["TagConf"]
        try:
            cnfg[config[0]][config[1]] = val
            bui.getsound('gunCocking').play()
        except Exception:
            bui.screenmessage("error", color=(1, 0, 0))
            bui.getsound('error').play()
        babase.app.config.apply_and_commit()

    def _on_menu_choice(self, choice: str):
        """
        Changes the given choice in configs
        """
        cnfg = babase.app.config["TagConf"][self.profilename]
        cnfg["scale"] = choice
        babase.app.config.apply_and_commit()

    def on_save(self):
        """
        Gets the text in text field of tag and then save it
        """
        text: str = cast(str, bui.textwidget(query=self.tagtextfield))
        profile = babase.app.config["TagConf"][self.profilename]
        if not text == "" or not text.strip():
            profile['tag'] = text
            babase.app.config.apply_and_commit()
            bui.getsound('gunCocking').play()
        else:
            bui.screenmessage(f"please define tag", color=(1, 0, 0))
            bui.getsound('error').play()

        bui.containerwidget(edit=self._root_widget,
                            transition='out_scale')
        bui.app.ui_v1.set_main_menu_window(EditProfileWindow(
            self.existing_profile,
            self.in_main_menu,
            transition='in_left').get_root_widget(), from_window=self._root_widget)


class CustomConfigNumberEdit:
    """A set of controls for editing a numeric config value.

    It will automatically save and apply the config when its
    value changes.

    Attributes:

        nametext
            The text widget displaying the name.

        valuetext
            The text widget displaying the current value.

        minusbutton
            The button widget used to reduce the value.

        plusbutton
            The button widget used to increase the value.
    """

    def __init__(self,
                 parent: bui.Widget,
                 configkey: List[str],
                 position: Tuple[float, float],
                 minval: float = 0.0,
                 maxval: float = 100.0,
                 increment: float = 1.0,
                 callback: Callable[[float], Any] = None,
                 xoffset: float = 0.0,
                 displayname: Union[str, babase.Lstr] = None,
                 changesound: bool = True,
                 textscale: float = 1.0):
        self._minval = minval
        self._maxval = maxval
        self._increment = increment
        self._callback = callback
        self._configkey = configkey
        self._value = babase.app.config[configkey[0]][configkey[1]][configkey[2]]

        self.nametext = bui.textwidget(
            parent=parent,
            position=position,
            size=(100, 30),
            text=displayname,
            maxwidth=160 + xoffset,
            color=(0.8, 0.8, 0.8, 1.0),
            h_align='left',
            v_align='center',
            scale=textscale)

        self.valuetext = bui.textwidget(
            parent=parent,
            position=(246 + xoffset, position[1]),
            size=(60, 28),
            editable=False,
            color=(0.3, 1.0, 0.3, 1.0),
            h_align='right',
            v_align='center',
            text=str(self._value),
            padding=2)

        self.minusbutton = bui.buttonwidget(
            parent=parent,
            position=(330 + xoffset, position[1]),
            size=(28, 28),
            label='-',
            autoselect=True,
            on_activate_call=babase.Call(self._down),
            repeat=True,
            enable_sound=changesound)

        self.plusbutton = bui.buttonwidget(parent=parent,
                                           position=(380 + xoffset, position[1]),
                                           size=(28, 28),
                                           label='+',
                                           autoselect=True,
                                           on_activate_call=babase.Call(self._up),
                                           repeat=True,
                                           enable_sound=changesound)

        bui.uicleanupcheck(self, self.nametext)
        self._update_display()

    def _up(self) -> None:
        self._value = min(self._maxval, self._value + self._increment)
        self._changed()

    def _down(self) -> None:
        self._value = max(self._minval, self._value - self._increment)
        self._changed()

    def _changed(self) -> None:
        self._update_display()
        if self._callback:
            self._callback(self._value)
        babase.app.config[self._configkey[0]][self._configkey[1]
                                              ][self._configkey[2]] = float(str(f'{self._value:.1f}'))
        babase.app.config.apply_and_commit()

    def _update_display(self) -> None:
        bui.textwidget(edit=self.valuetext, text=f'{self._value:.1f}')
