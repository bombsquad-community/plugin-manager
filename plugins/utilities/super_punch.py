# To learn more, see https://ballistica.net/wiki/meta-tag-system
# ba_meta require api 8

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bascenev1 as bs
import bauiv1 as bui
from bauiv1lib import popup
from bascenev1lib.actor import playerspaz
from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.mainmenu import MainMenuSession

if TYPE_CHECKING:
	from typing import Any, Callable


class ModInfo:
	cfgname = 'Super Punch' # config name
	cfglist = {
		'punch_scale': 1.0,
		'fast_hits': True,
		'enable_mod': True,
	} # config list
	url = 'https://youtu.be/WCq3yAis7VU' # video


class ModLang:
	lang = babase.app.lang.language
	if lang == 'Spanish':
		title = 'Opciones del Mod'
		enable = 'Habilitar Mod'
		punch_scale = 'Potencia de Golpe'
		fast_hits = 'Golpes Rápidos'
	elif lang == 'Chinese':
		title = '模组设置'
		enable = '启用模组'
		punch_scale = '拳击力量等级'
		fast_hits = '快速点击'
	else:
		title = 'Mod Settings'
		enable = 'Enable Mod'
		punch_scale = 'Punch Power Scale'
		fast_hits = 'Fast Hits'


class ConfigNumberEdit:
	"""A set of controls for editing a numeric config value.

	It will automatically save and apply the config when its
	value changes.
	"""

	nametext: bui.Widget
	"""The text widget displaying the name."""

	valuetext: bui.Widget
	"""The text widget displaying the current value."""

	minusbutton: bui.Widget
	"""The button widget used to reduce the value."""

	plusbutton: bui.Widget
	"""The button widget used to increase the value."""

	def __init__(
		self,
		parent: bui.Widget,
		configkey: str,
		position: tuple[float, float],
		minval: float = 0.0,
		maxval: float = 100.0,
		increment: float = 1.0,
		callback: Callable[[float], Any] | None = None,
		xoffset: float = 0.0,
		displayname: str | bui.Lstr | None = None,
		changesound: bool = True,
		textscale: float = 1.0,
		maxwidth: float = 160,
	):
		if displayname is None:
			displayname = configkey

		self._configkey = configkey
		self._minval = minval
		self._maxval = maxval
		self._increment = increment
		self._callback = callback
		self._value = bui.app.config[ModInfo.cfgname][configkey]

		self.nametext = bui.textwidget(
			parent=parent,
			position=position,
			size=(100, 30),
			text=displayname,
			maxwidth=maxwidth + xoffset,
			color=(0.8, 0.8, 0.8, 1.0),
			h_align='left',
			v_align='center',
			scale=textscale,
		)
		self.valuetext = bui.textwidget(
			parent=parent,
			position=(246 + xoffset, position[1]),
			size=(60, 28),
			editable=False,
			color=(0.3, 1.0, 0.3, 1.0),
			h_align='right',
			v_align='center',
			text=str(int(self._value)),
			padding=2,
		)
		self.minusbutton = bui.buttonwidget(
			parent=parent,
			position=(330 + xoffset, position[1]),
			size=(28, 28),
			label='-',
			autoselect=True,
			on_activate_call=bui.Call(self._down),
			repeat=True,
			enable_sound=changesound,
		)
		self.plusbutton = bui.buttonwidget(
			parent=parent,
			position=(380 + xoffset, position[1]),
			size=(28, 28),
			label='+',
			autoselect=True,
			on_activate_call=bui.Call(self._up),
			repeat=True,
			enable_sound=changesound,
		)
		# Complain if we outlive our widgets.
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
		bui.app.config[ModInfo.cfgname][self._configkey] = self._value
		bui.app.config.apply_and_commit()

	def _update_display(self) -> None:
		bui.textwidget(edit=self.valuetext, text=str(int(self._value)))
	

class ModSettingsPopup(popup.PopupWindow):

	def __init__(self):
		uiscale = bui.app.ui_v1.uiscale
		self._transitioning_out = False
		self._width = 480
		self._height = 260
		bg_color = (0.4, 0.37, 0.49)

		# creates our _root_widget
		super().__init__(
			position=(0.0, 0.0),
			size=(self._width, self._height),
			scale=(
				2.06
				if uiscale is bui.UIScale.SMALL
				else 1.4
				if uiscale is bui.UIScale.MEDIUM
				else 1.0
			),
			bg_color=bg_color,
		)

		self._cancel_button = bui.buttonwidget(
			parent=self.root_widget,
			position=(34, self._height - 48),
			size=(50, 50),
			scale=0.7,
			label='',
			color=bg_color,
			on_activate_call=self._on_cancel_press,
			autoselect=True,
			icon=bui.gettexture('crossOut'),
			iconscale=1.2)
		bui.containerwidget(edit=self.root_widget,
						   cancel_button=self._cancel_button)

		if ModInfo.url != '':
			url_button = bui.buttonwidget(
				parent=self.root_widget,
				position=(self._width - 86, self._height - 51),
				size=(82, 82),
				scale=0.5,
				label='',
				color=(1.1, 0.0, 0.0),
				on_activate_call=self._open_url,
				autoselect=True,
				icon=bui.gettexture('startButton'),
				iconscale=1.83,
				icon_color=(1.3, 1.3, 1.3))

		title = bui.textwidget(
			parent=self.root_widget,
			position=(self._width * 0.49, self._height - 27 - 5),
			size=(0, 0),
			h_align='center',
			v_align='center',
			scale=1.0,
			text=ModLang.title,
			maxwidth=self._width * 0.6,
			color=bui.app.ui_v1.title_color)

		checkbox_size = (self._width * 0.7, 50)
		checkbox_maxwidth = 250
		
		v = 0
		v += 115
		ConfigNumberEdit(
			parent=self.root_widget,
			position=(self._width * 0.08, self._height - v),
			configkey='punch_scale',
			displayname=ModLang.punch_scale,
			callback=self._change_val,
			maxwidth=200,
		)
		v += 66
		bui.checkboxwidget(
			parent=self.root_widget,
			position=(self._width * 0.155, self._height - v),
			size=checkbox_size,
			autoselect=True,
			maxwidth=checkbox_maxwidth,
			scale=1.0,
			textcolor=(0.8, 0.8, 0.8),
			value=bui.app.config[ModInfo.cfgname]['fast_hits'],
			text=ModLang.fast_hits,
			on_value_change_call=self._fast_hits,
		)
		v += 50
		bui.checkboxwidget(
			parent=self.root_widget,
			position=(self._width * 0.155, self._height - v),
			size=checkbox_size,
			autoselect=True,
			maxwidth=checkbox_maxwidth,
			scale=1.0,
			textcolor=(0.8, 0.8, 0.8),
			value=bui.app.config[ModInfo.cfgname]['enable_mod'],
			text=ModLang.enable,
			on_value_change_call=self._enable_mod,
		)

	def _change_val(self, val: int) -> None:
		self._update_mod()

	def _fast_hits(self, val: bool) -> None:
		bui.app.config[ModInfo.cfgname]['fast_hits'] = val
		bui.app.config.apply_and_commit()
		self._update_mod()

	def _enable_mod(self, val: bool) -> None:
		bui.app.config[ModInfo.cfgname]['enable_mod'] = val
		bui.app.config.apply_and_commit()
		self._update_mod()
		
	def _update_mod(self) -> None:
		activity = bs.get_foreground_host_activity()
		session = bs.get_foreground_host_session()
		if not isinstance(session, MainMenuSession):
			with activity.context:
				if not activity.players:
					return
				for player in activity.players:
					if not player.is_alive():
						continue
					factory = SpazFactory.get()
					if bui.app.config[ModInfo.cfgname]['enable_mod']:
						player.actor._punch_power_scale = bui.app.config[
							ModInfo.cfgname]['punch_scale']
						if bui.app.config[ModInfo.cfgname]['fast_hits']:
							cooldown = 0
						else:
							if player.actor._has_boxing_gloves:
								cooldown = factory.punch_cooldown_gloves
							else:
								cooldown = factory.punch_cooldown
						player.actor._punch_cooldown = cooldown
					else:
						if player.actor._has_boxing_gloves:
							player.actor._punch_power_scale = factory.punch_power_scale_gloves
							player.actor._punch_cooldown = factory.punch_cooldown_gloves
						else:
							player.actor._punch_power_scale = factory.punch_power_scale
							player.actor._punch_cooldown = factory.punch_cooldown

	def _open_url(self) -> None:
		bui.open_url(ModInfo.url)

	def _on_cancel_press(self) -> None:
		self._transition_out()

	def _transition_out(self) -> None:
		if not self._transitioning_out:
			self._transitioning_out = True
			bui.containerwidget(edit=self.root_widget, transition='out_scale')

	def on_popup_cancel(self) -> None:
		bui.getsound('swish').play()
		self._transition_out()


class NewPlayerSpaz(playerspaz.PlayerSpaz):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.old_equip_boxing_gloves = self.equip_boxing_gloves
		self._old_gloves_wear_off = self._gloves_wear_off
		if babase.app.config[ModInfo.cfgname]['enable_mod']:
			self._punch_power_scale = babase.app.config[ModInfo.cfgname]['punch_scale']
			self._punch_cooldown = 0

	def equip_boxing_gloves(self) -> None:
		super().equip_boxing_gloves()
		if babase.app.config[ModInfo.cfgname]['enable_mod']:
			self._punch_power_scale = babase.app.config[ModInfo.cfgname]['punch_scale']
			self._punch_cooldown = 0

	def _gloves_wear_off(self) -> None:
		super().equip_boxing_gloves()
		if babase.app.config[ModInfo.cfgname]['enable_mod']:
			self._punch_power_scale = babase.app.config[ModInfo.cfgname]['punch_scale']
			self._punch_cooldown = 0


class CustomMod:
	def __init__(self) -> None:
		playerspaz.PlayerSpaz = NewPlayerSpaz


# ba_meta export plugin
class ModPlugin(babase.Plugin):

	def on_app_running(self) -> None:
		self.setup_config()
		self.custom_mod()

	def custom_mod(self) -> None:
		CustomMod()

	def setup_config(self) -> None:
		if ModInfo.cfgname in babase.app.config:
			for key in ModInfo.cfglist.keys():
				if not key in babase.app.config[ModInfo.cfgname]:
					babase.app.config[ModInfo.cfgname] = ModInfo.cfglist
					babase.app.config.apply_and_commit()
					break
		else:
			babase.app.config[ModInfo.cfgname] = ModInfo.cfglist
			babase.app.config.apply_and_commit()

	def has_settings_ui(self) -> bool:
		return True

	def show_settings_ui(self, source_widget: babase.Widget | None) -> None:
		ModSettingsPopup()