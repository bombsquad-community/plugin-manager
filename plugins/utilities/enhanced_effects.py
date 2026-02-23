# ba_meta require api 9
from __future__ import annotations

from typing import TYPE_CHECKING

import random
import weakref
import babase
import bascenev1 as bs

from bascenev1lib.actor.background import Background

if TYPE_CHECKING:
    from typing import Any

plugman = dict(
    plugin_name="enhanced_effects",
    description="Explosions affect character colors, slow-mo tnt, fair colored shields, a trippy background screen and maybe more in the future!",
    external_url="",
    authors=[
        {"name": "DinoWattz", "email": "", "discord": ""}
    ],
    version="1.0.0",
)

# Transparent Background (kinda hacky, works best on pc with high/higher quality 'visuals' setting)
BACKGROUND_OPACITY = 0.5
def __modified_background_init(
        self,
        fade_time: float = 0.5,
        start_faded: bool = False,
        show_logo: bool = False,
    ):
        super(type(self), self).__init__()
        self._dying = False
        self.fade_time = fade_time
        # We're special in that we create our node in the session
        # scene instead of the activity scene.
        # This way we can overlap multiple activities for fades
        # and whatnot.
        session = bs.getsession()
        self._session = weakref.ref(session)
        with session.context:
            self.node = bs.newnode(
                'image',
                delegate=self,
                attrs={
                    'fill_screen': True,
                    'texture': bs.gettexture('bg'),
                    'tilt_translate': -0.3,
                    'has_alpha_channel': False,
                    'color': (1, 1, 1),
                    'opacity': BACKGROUND_OPACITY,
                },
            )
            if not start_faded:
                bs.animate(
                    self.node,
                    'opacity',
                    {0.0: 0.0, self.fade_time: BACKGROUND_OPACITY},
                    loop=False,
                )
            if show_logo:
                logo_texture = bs.gettexture('logo')
                logo_mesh = bs.getmesh('logo')
                logo_mesh_transparent = bs.getmesh('logoTransparent')
                self.logo = bs.newnode(
                    'image',
                    owner=self.node,
                    attrs={
                        'texture': logo_texture,
                        'mesh_opaque': logo_mesh,
                        'mesh_transparent': logo_mesh_transparent,
                        'scale': (0.7, 0.7),
                        'vr_depth': -250,
                        'color': (0.15, 0.15, 0.15),
                        'position': (0, 0),
                        'tilt_translate': -0.05,
                        'absolute_scale': False,
                    },
                )
                self.node.connectattr('opacity', self.logo, 'opacity')
                # add jitter/pulse for a stop-motion-y look unless we're in VR
                # in which case stillness is better
                if not bs.app.env.vr:
                    self.cmb = bs.newnode(
                        'combine', owner=self.node, attrs={'size': 2}
                    )
                    for attr in ['input0', 'input1']:
                        bs.animate(
                            self.cmb,
                            attr,
                            {0.0: 0.693, 0.05: 0.7, 0.5: 0.693},
                            loop=True,
                        )
                    self.cmb.connectattr('output', self.logo, 'scale')
                    cmb = bs.newnode(
                        'combine', owner=self.node, attrs={'size': 2}
                    )
                    cmb.connectattr('output', self.logo, 'position')
                    # Gen some random keys for that stop-motion-y look.
                    keys = {}
                    timeval = 0.0
                    for _i in range(10):
                        keys[timeval] = (random.random() - 0.5) * 0.0015
                        timeval += random.random() * 0.1
                    bs.animate(cmb, 'input0', keys, loop=True)
                    keys = {}
                    timeval = 0.0
                    for _i in range(10):
                        keys[timeval] = (random.random() - 0.5) * 0.0015 + 0.05
                        timeval += random.random() * 0.1
                    bs.animate(cmb, 'input1', keys, loop=True)

def _modified_background_die(self, immediate: bool = False) -> None:
    session = self._session()
    if session is None and self.node:
        # If session is gone, our node should be too,
        # since it was part of the session's scene.
        # Let's make sure that's the case.
        # (since otherwise we have no way to kill it)
        bs.logging.exception(
            'got None session on Background _die'
            ' (and node still exists!)'
        )
    elif session is not None:
        with session.context:
            if not self._dying and self.node:
                self._dying = True
                if immediate:
                    self.node.delete()
                else:
                    bs.animate(
                        self.node,
                        'opacity',
                        {0.0: self.node.opacity, self.fade_time: 0.0},
                        loop=False,
                    )
                    bs.timer(self.fade_time + 0.1, self.node.delete)

Background.__init__ = __modified_background_init
Background._die = _modified_background_die

# Tools
def blend_toward(
    rgb: tuple[float, float, float],
    target: tuple[float, float, float],
    amount: float = 1.0,
    perceptual: bool = False
) -> tuple[float, ...]:
    """
    Blend 'rgb' toward 'target' by 'amount' (0..1).

    If perceptual=True, blend in linear-light space for smoother, more
    natural-looking fades.
    """
    def clamp01(x: float) -> float:
        return max(0.0, min(1.0, x))

    def srgb_to_linear(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    def linear_to_srgb(c: float) -> float:
        return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055

    a = clamp01(amount)

    if not perceptual:
        return tuple(clamp01(c + (t - c) * a) for c, t in zip(rgb, target))

    # Gamma-aware blend
    rgb_lin = [srgb_to_linear(clamp01(c)) for c in rgb]
    target_lin = [srgb_to_linear(clamp01(c)) for c in target]
    blended_lin = [
        c + (t - c) * a for c, t in zip(rgb_lin, target_lin)
    ]
    return tuple(clamp01(linear_to_srgb(c)) for c in blended_lin)

# ba_meta export babase.Plugin
class Plugin(babase.Plugin):
    def on_app_running(self) -> None:
        from bascenev1lib.actor.bomb import Blast, ExplodeHitMessage
        from bascenev1lib.actor.spaz import Spaz
        from bascenev1lib.actor.spazbot import SpazBot
        from bascenev1lib.actor.playerspaz import PlayerSpaz

        # Colored Shields
        org_equip_shields = Spaz.equip_shields

        def equip_shields(self, decay: bool = False) -> None:
            org_equip_shields(self, decay)
            if self.shield is not None:
                safe_highlight = bs.safecolor(getattr(self, '_original_highlight', self.node.highlight), target_intensity=0.75)
                self.shield.color = bs.normalized_color(safe_highlight)

        Spaz.equip_shields = equip_shields

        # Slow Motion TNT Explosion
        org_blast_init = Blast.__init__

        def new_init(self: Blast, blast_type='normal', hit_type='explosion', *args, **kwargs) -> None:
            org_blast_init(self, blast_type=blast_type, hit_type=hit_type, *args, **kwargs)

            if blast_type == 'tnt' and hit_type == 'explosion':
                bs.camerashake(3.0)
                activity = bs.getactivity()
                gnode = activity.globalsnode

                # Pause
                gnode.paused = True
                self._pause_timer = bs.DisplayTimer(0.01, bs.CallPartial(setattr, gnode, 'paused', True), True)

                delay = 0.06

                bs.displaytimer(delay, bs.CallPartial(setattr, self, '_pause_timer', None))
                bs.displaytimer(delay, bs.CallPartial(setattr, gnode, 'paused', False))

                # Slow Motion
                gnode.slow_motion = True
                self._slow_motion_timer = bs.DisplayTimer(0.01, bs.CallPartial(setattr, gnode, 'slow_motion', True), True)

                delay += 0.14

                bs.displaytimer(delay, bs.CallPartial(setattr, self, '_slow_motion_timer', None))
                bs.displaytimer(delay, bs.CallPartial(setattr, gnode, 'slow_motion', activity.slow_motion))

        Blast.__init__ = new_init

        # Explosion Spaz Coloring
        org_handlemessage = Blast.handlemessage

        def new_handlemessage(self: Blast, msg: Any, *args, **kwargs) -> Any:
            org_handlemessage(self, msg, *args, **kwargs)

            if isinstance(msg, ExplodeHitMessage):
                    node = bs.getcollision().opposingnode
                    delegate = node.getdelegate(PlayerSpaz) or node.getdelegate(SpazBot)
                    if (delegate and not delegate.shield) and not node.invincible:
                        if not hasattr(delegate, '_original_color'):
                            delegate._original_color = node.color
                            delegate._original_highlight = node.highlight

                        original_color = delegate._original_color
                        original_highlight = delegate._original_highlight

                        blend_time = 1.0
                        start_time = 6.0
                        end_time = 7.0

                        bs.emitfx(
                            position=node.position,
                            velocity=node.velocity,
                            count=int(4.0 + random.random() * 4),
                            emit_type='tendrils',
                            tendril_type='ice' if self.blast_type == 'ice' else 'smoke',
                        )

                        explosion_intensity = 0.70 if not self.blast_type == 'tnt' else 0.96
                        
                        if self.blast_type == 'ice':
                            explosion_intensity = 0.91
                            explosion_color = (0.07, 0.6, 1.5)
                        elif self.blast_type == 'sticky':
                            explosion_intensity = 0.91
                            explosion_color = (0.07, 0.9, 0.07)
                            blend_time = 1.0
                            start_time = 1.2
                            end_time = 3.0
                        else:
                            explosion_color = (0.07, 0.03, 0.0)


                        blend_color = blend_toward(node.color, explosion_color, explosion_intensity, True)
                        blend_highlight = blend_toward(node.highlight, explosion_color, explosion_intensity-0.03, True)

                        bs.animate_array(node, 'color', 3, {
                            blend_time: blend_color,
                            start_time: blend_color,
                            end_time: original_color
                        })
                        bs.animate_array(node, 'highlight', 3, {
                            blend_time: blend_highlight,
                            start_time: blend_highlight,
                            end_time: original_highlight
                        })

                        delegate._color_timer = bs.Timer(end_time, bs.CallPartial(delattr, delegate, '_original_color'))
                        delegate._highlight_timer = bs.Timer(end_time, bs.CallPartial(delattr, delegate, '_original_highlight'))

        Blast.handlemessage = new_handlemessage