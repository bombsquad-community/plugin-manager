# ba_meta require api 9
from __future__ import annotations

from typing import TYPE_CHECKING
import babase
import _babase
import bascenev1 as bs
from types import FunctionType
import enum


if TYPE_CHECKING:
    from typing import Type, Callable, Any, Tuple

plugman = dict(
    plugin_name="glowing_profiles",
    description="This plugin gives your profile glowlight, just like on some servers, but only offline",
    external_url="https://m.youtube.com/watch?v=Jb_dKz99rhY",
    authors=[
        {"name": "andrejkuroglo8", "email": "andrejkuroglo8@gmail.com", "discord": "andrewku"},
    ],
    version="1.0.0",
)


def redefine_method(dst: Tuple[Any, str], src: Tuple[Any, str]) -> None:
    if hasattr(getattr(*src), '__redefine_type') and getattr(*src).__redefine_type in (
            RedefineFlag.DECORATE_PRE, RedefineFlag.DECORATE_AFTER, RedefineFlag.DECORATE_ADVANCED):
        new = getattr(*src)
        old = getattr(*dst)
        func: Callable
        if getattr(*src).__redefine_type == RedefineFlag.DECORATE_AFTER:
            def func(*args, **kwargs):
                returned = old(*args, **kwargs)
                return new(*args, **kwargs, returned=returned)
        elif getattr(*src).__redefine_type == RedefineFlag.DECORATE_PRE:
            def func(*args, **kwargs):
                new(*args, **kwargs)
                return old(*args, **kwargs)
        else:
            def func(*args, **kwargs):
                return new(*args, **kwargs, old_function=old)

        setattr(*dst, func)
    else:
        setattr(*dst, getattr(*src))

    # Fucking super()!
    # dst.__code__ = CodeType(
    #     src.__code__.co_argcount,
    #     src.__code__.co_posonlyargcount,
    #     src.__code__.co_kwonlyargcount,
    #     src.__code__.co_nlocals,
    #     src.__code__.co_stacksize,
    #     src.__code__.co_flags,
    #     src.__code__.co_code,
    #     src.__code__.co_consts,
    #     src.__code__.co_names,
    #     src.__code__.co_varnames,
    #     src.__code__.co_filename,
    #     dst.__code__.co_name,
    #     src.__code__.co_firstlineno,
    #     src.__code__.co_lnotab,
    #     dst.__code__.co_freevars,
    #     dst.__code__.co_cellvars)


def redefine_class_methods(orig_cls: Type[object]) -> Callable[[Any], None]:
    """Returns decorator that redefines all class methods

    Parameters:
         orig_cls (Type[object]): class that will redefined"""

    def decorator(cls) -> None:
        # for method in filter(lambda x: isinstance(getattr(cls, x), FunctionType), dir(cls)):
        for method in cls._redefine_methods:
            if hasattr(orig_cls, method):
                redefine_method((orig_cls, method), (cls, method))
            else:
                setattr(orig_cls, method, getattr(cls, method))
                # setattr(getattr(orig_cls, 'self'), '__class__', getattr(cls, method))  # Fucking super()!!!!

    return decorator


class RedefineFlag(enum.Enum):
    REDEFINE = 0
    DECORATE_AFTER = 1
    DECORATE_PRE = 2
    DECORATE_ADVANCED = 3
    DECORATE = DECORATE_AFTER


def redefine_flag(*flags: RedefineFlag) -> Callable[[Callable], Callable]:
    def decorator(func: Callable) -> Callable:
        for flag in flags:
            if flag in (RedefineFlag.DECORATE_AFTER, RedefineFlag.REDEFINE, RedefineFlag.DECORATE_PRE,
                        RedefineFlag.DECORATE_ADVANCED):
                func.__redefine_type = flag
        return func

    return decorator


def get_locale(*args):
    return "Error"


@redefine_class_methods(bs.Chooser)
class Chooser:
    _redefine_methods = ('_gcinit', '_get_glowing_colors', 'update_from_profile',
                         '_getname')

    def _gcinit(self):
        if hasattr(self, '_gcinit_done'):
            return
        self.glow_dict = {}
        self._markers = ('"', "'", '^', '%', ';', '`')
        self._get_glowing_colors()
        self._gcinit_done = True

    @redefine_flag(RedefineFlag.REDEFINE)
    def _get_glowing_colors(self):
        """Search glowing code among profiles."""
        try:
            should_del = []
            for i in self._profilenames:
                for m in self._markers:
                    if i.startswith(m + ','):
                        code = i.split(',')
                        self.glow_dict[code[0]] = (
                            float(code[1]),
                            float(code[2]),
                            int(code[3]),
                            int(code[4]))
                        # should_del.append(i)
            for i in should_del:
                self._profilenames.remove(i)
        except Exception as err:
            print(err)
            ba.screenmessage(
                get_locale('init_glowing_code_error'),
                color=(1, 0, 0),
                clients=[self._player.get_input_device().client_id],
                transient=True)

    @redefine_flag(RedefineFlag.DECORATE_ADVANCED)
    def _getname(self, full=True, old_function=None):
        name = old_function(self, full)
        for m in self._markers:
            name = name.replace(m, '')
        return name

    @redefine_flag(RedefineFlag.DECORATE_ADVANCED)
    def update_from_profile(self, old_function):
        self._gcinit()
        from bascenev1 import _profile
        try:
            self._profilename = self._profilenames[self._profileindex]
            character = self._profiles[self._profilename]['character']

            if self._profilename[0] in self.glow_dict:
                if (character not in self._character_names
                        and character in _ba.app.spaz_appearances):
                    self._character_names.append(character)
                self._character_index = self._character_names.index(character)

                player_glowing_dict = self.glow_dict[self._profilename[0]]
                color_marker = player_glowing_dict[0]
                color_marker = max(-999.0, min(color_marker, 50.0))

                highlight_marker = float(player_glowing_dict[1])
                highlight_marker = max(-999.0, min(highlight_marker, 50.0))

                stabilize_color = int(player_glowing_dict[2]) > 0
                stabilize_highlight = int(player_glowing_dict[3]) > 0
                self._color, self._highlight = \
                    _profile.get_player_profile_colors(
                        self._profilename,
                        profiles=self._profiles)

                if stabilize_color:
                    m = max(self._color)
                    self._color = list(self._color)
                    for i in (0, 1, 2):
                        if self._color[i] == m:
                            self._color[i] = self._color[i] * color_marker
                    self._color = tuple(self._color)
                else:
                    self._color = (
                        self._color[0] * color_marker,
                        self._color[1] * color_marker,
                        self._color[2] * color_marker)

                if not stabilize_highlight:
                    self._highlight = (
                        self._highlight[0] * highlight_marker,
                        self._highlight[1] * highlight_marker,
                        self._highlight[2] * highlight_marker)
                else:
                    m = max(self._highlight)
                    self._highlight = list(self._highlight)
                    for i in (0, 1, 2):
                        if self._highlight[i] == m:
                            self._highlight[i] = \
                                self._highlight[i] * highlight_marker
                    self._highlight = tuple(self._highlight)
            else:
                old_function(self)
        except KeyError:
            self.character_index = self._random_character_index
            self._color = self._random_color
            self._highlight = self._random_highlight

        self._update_icon()
        self._update_text()

# ba_meta export babase.Plugin


class Glowing(babase.Plugin):
    pass
