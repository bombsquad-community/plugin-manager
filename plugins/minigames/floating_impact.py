# ba_meta require api 9

from __future__ import annotations

from typing import TYPE_CHECKING
from random import choice, uniform

########### Ballistica Modules ###########
import bascenev1 as bs
from babase import get_string_width, safecolor, charstr, SpecialChar

from bascenev1lib.gameutils import SharedObjects

from bascenev1lib.actor.onscreentimer import OnScreenTimer
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.bomb import Bomb

plugman = dict(
    plugin_name="floating_impact",
    description="A fun-type minigame where players should avoid \"bullets\" (Bullet Hell Minigame)",
    external_url="https://discord.com/channels/1001896771347304639/1554062155374928003",
    authors=[
        {"name": "FluffyPal", "email": "", "discord": "fluffypal"}
    ],
    version="1.0.0",
)


if TYPE_CHECKING:
    from typing import Any, Type, Union, Sequence, Optional


class Icon(bs.Actor):
    """Creates Live PLayer Character Spaz in-game icon on screen."""

    def __init__(
        self,
        player: Player,
        position: tuple[float, float],
        scale: float,
        show_lives: bool = True,
        show_death: bool = True,
        name_scale: float = 1.0,
        name_maxwidth: float = 115.0,
        flatness: float = 1.0,
        shadow: float = 1.0,
    ):
        super().__init__()

        self._player = player
        self._show_lives = show_lives
        self._show_death = show_death
        self._name_scale = name_scale
        self._outline_tex = bs.gettexture('characterIconMask')

        icon = player.get_icon()
        self.node = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'texture': icon['texture'],
                'tint_texture': icon['tint_texture'],
                'tint_color': icon['tint_color'],
                'vr_depth': 400,
                'tint2_color': icon['tint2_color'],
                'mask_texture': self._outline_tex,
                'opacity': 1.0,
                'absolute_scale': True,
                'attach': 'bottomCenter',
            },
        )
        self._name_text = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': bs.Lstr(value=player.getname()),
                'color': bs.safecolor(player.team.color),
                'h_align': 'center',
                'v_align': 'center',
                'vr_depth': 410,
                'maxwidth': name_maxwidth,
                'shadow': shadow,
                'flatness': flatness,
                'h_attach': 'center',
                'v_attach': 'bottom',
            },
        )
        if self._show_lives:
            self._lives_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': 'x0',
                    'color': (1, 1, 0.5),
                    'h_align': 'left',
                    'vr_depth': 430,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'h_attach': 'center',
                    'v_attach': 'bottom',
                },
            )
        self.set_position_and_scale(position, scale)

    def set_position_and_scale(
        self, position: tuple[float, float], scale: float
    ) -> None:
        """(Re)position the icon."""
        assert self.node
        self.node.position = position
        self.node.scale = [70.0 * scale]
        self._name_text.position = (position[0], position[1] + scale * 52.0)
        self._name_text.scale = 1.0 * scale * self._name_scale
        if self._show_lives:
            self._lives_text.position = (
                position[0] + scale * 10.0,
                position[1] - scale * 43.0,
            )
            self._lives_text.scale = 1.0 * scale

    def update_for_lives(self) -> None:
        """Update for the target player's current lives."""
        if self._player:
            lives = self._player.lives
        else:
            lives = 0
        if self._show_lives:
            if lives > 0:
                self._lives_text.text = 'x' + str(lives-1)
            else:
                self._lives_text.text = ''
        if lives == 0:
            self._name_text.opacity = 0.2
            assert self.node
            self.node.color = (0.7, 0.3, 0.3)
            self.node.opacity = 0.2

    def handle_player_spawned(self) -> None:
        """Our player spawned; hooray!"""
        if not self.node:
            return
        self.node.opacity = 1.0
        self.update_for_lives()

    def handle_player_died(self) -> None:
        """Well poo; our player died."""
        if not self.node:
            return
        if self._show_death:
            bs.animate(
                self.node,
                'opacity',
                {
                    0.00: 1.0,
                    0.05: 0.0,
                    0.10: 1.0,
                    0.15: 0.0,
                    0.20: 1.0,
                    0.25: 0.0,
                    0.30: 1.0,
                    0.35: 0.0,
                    0.40: 1.0,
                    0.45: 0.0,
                    0.50: 1.0,
                    0.55: 0.2,
                },
            )
            lives = self._player.lives
            if lives == 0:
                bs.timer(0.6, self.update_for_lives)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            self.node.delete()
            return None
        return super().handlemessage(msg)


Translate_Texts: dict[str, dict[str, str]] = {
    'gameEnds': {  # >>
        'id': 'Permainan Berakhir',
        'en': 'Game Ends',
    },
    'gameName': {
        'id': 'Bom Melayang',
        'en': 'Floating Impact',
    },
    'gameDesc': {
        'id': 'Hindari bom melayang',
        'en': 'Dodge the floating impact bomb',
    },
    'gameDescInGame': {
        'id': 'Hindari bom melayang',
        'en': 'Dodge the floating impact bomb',
    },
    'settingTimeLimit': {  # Time Limit
        'id': 'Batas Waktu (Detik)',
        'en': 'Time Limit (Seconds)',
    },
    'settingPlayerLives': {  # Player Lives
        'id': 'Nyawa Pemain',
        'en': 'Player Lives',
    },
    'settingMaxHit': {  # MaxHit
        'id': 'Hit Maksimal',
        'en': 'Max Hit',
    },
    'settingMaxHit1': {
        'id': 'Mati Instan',
        'en': 'Instant Death',
    },
    'settingMaxHit2': {
        'id': '2 Hit',
        'en': '2 Hits',
    },
    'settingMaxHit3': {
        'id': '3 Hit',
        'en': '3 Hits',
    },
    'settingMaxHit4': {
        'id': '4 Hit',
        'en': '4 Hits',
    },
    'settingMaxHit5': {
        'id': '5 Hit',
        'en': '5 Hits',
    },
    'settingBoxCount': {  # Box Count
        'id': 'Jumlah Kotak',
        'en': 'Box Count',
    },
    'settingBombVelocity': {  # Bomb Velocity
        'id': 'Kecepatan Bom',
        'en': 'Bomb Velocity',
    },
    'settingBombVelocitySlow': {
        'id': 'Lambat',
        'en': 'Slow',
    },
    'settingBombVelocityNormal': {
        'id': 'Normal',
        'en': 'Normal',
    },
    'settingBombVelocityFast': {
        'id': 'Cepat',
        'en': 'Fast',
    },
    'settingBombVelocityVeryFast': {
        'id': 'Sangat Cepat',
        'en': 'Very Fast',
    },
    'settingBombFollowsPlayer': {
        'id': 'Bom Ngikut Player',
        'en': 'Bomb Follows Player',
    },
    'settingEpicMode': {  # Epic Mode
        'id': 'Mode Epik',
        'en': 'Epic Mode',
    }}
"""Global Langs"""


def get_app_lang_as_id():
    """
    Returns The Language `ID`.
    Such as: `id`, `en`, `hi`, `...`
    """
    App_Lang = bs.app.lang.language
    lang_id = 'en'
    if App_Lang == 'Indonesian':
        lang_id = 'id'
    elif App_Lang == 'English':
        lang_id = 'en'
    return lang_id


app_lang = get_app_lang_as_id()


def get_lang_text(key: str) -> str:
    """
    Return Translated Text From `Str` Key Given.
    """
    # text key: lang -> text
    language_id = app_lang
    text = Translate_Texts.get(key, {}).get(language_id, '')
    if not text.strip() or text.strip() == '':
        return f"EmptyText: {'*[{}]'.format(key)}"
    return text


"""############################### Game Management ###############################"""


class Player(bs.Player['Team']):
    def __init__(self) -> None:
        self.survived: bool = True  # To track their "alive" state
        self.lives = 1  # For counting player Lives
        self.hitpoint_tag: bs.Node | None = None
        self.death_time: Optional[float] = None  # To track their died time
        self.icons: list[Icon] = []  # Their icons


class Team(bs.Team[Player]):
    def __init__(self) -> None:
        self.score = 0
        self.spawn_order = []


"""############################### Game Management ###############################"""


class FpHitByBomb:
    def __init__(self, playerspaz: FpPlayerSpaz) -> None:
        self.playerspaz = playerspaz


class FpBomb(Bomb):
    def explode(self):
        self.activity: FluffysGame5
        if self in self.activity.bombs:
            self.activity.bombs.remove(self)
        super().explode()


rainbow_delay = 0.15
rainbow_start_delay = 0.1

_colors = [
    (1.0, 0.0, 0.0),    # Red
    (1.0, 0.5, 0.0),    # Orange
    (1.0, 1.0, 0.0),    # Yellow
    (0.5, 1.0, 0.0),    # Chartreuse
    (0.0, 1.0, 0.0),    # Green
    (0.0, 1.0, 0.5),    # Spring Green
    (0.0, 0.5, 1.0),    # Azure
    (0.5, 0.0, 1.0),    # Violet
    (1.0, 0.0, 0.0),    # Red
]
_colors_len = len(_colors)

COLORS_KEYS = {rainbow_delay*a: col for a, col in enumerate(_colors)}


class FpPlayerSpaz(PlayerSpaz):
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.HitMessage):
            if self.shield and self.shield.exists():
                return super().handlemessage(msg)

            elif msg.hit_subtype == "impact":
                if self.node.invincible:
                    return  # type: ignore

                msg.flat_damage = 0.0
                msg.kick_back = 0.0
                msg.magnitude = 0.0
                msg.velocity_magnitude = 0.0
                msg.velocity = (0, 0, 0)
                msg.force_direction = (0, 0, 0)

                self.activity.handlemessage(FpHitByBomb(
                    playerspaz=self
                ))
            else:
                print(f"Oops, not an impact damage: {msg.hit_type} | {msg.hit_subtype}")
                return

        return super().handlemessage(msg)


# ba_meta export bascenev1.GameActivity
class FluffysGame5(bs.TeamGameActivity[Player, Team]):
    name = get_lang_text('gameName')
    description = f"{get_lang_text('gameDesc')}!\nBy FluffyPal :)"  # Game selection Desc
    scoreconfig = bs.ScoreConfig(
        label='Survived',
        scoretype=bs.ScoreType.MILLISECONDS,
        version='B'
    )
    announce_player_deaths = True
    allow_mid_activity_joins = False

    @classmethod
    def get_available_settings(
            cls, sessiontype: Type[bs.Session]) -> list[bs.Setting]:
        settings = [
            bs.IntSetting(get_lang_text('settingTimeLimit'),
                          min_value=0,
                          max_value=600,
                          increment=60,
                          default=180
                          ),
            bs.IntChoiceSetting(get_lang_text('settingMaxHit'),
                                choices=[
                (get_lang_text('settingMaxHit1'), 1),
                (get_lang_text('settingMaxHit2'), 2),
                (get_lang_text('settingMaxHit3'), 3),
                (get_lang_text('settingMaxHit4'), 4),
                (get_lang_text('settingMaxHit5'), 5)
            ],
                default=4
            ),
            bs.IntSetting(get_lang_text('settingPlayerLives'),
                          min_value=1,
                          max_value=2,
                          increment=1,
                          default=1
                          ),
            bs.IntSetting(get_lang_text('settingBoxCount'),
                          min_value=4,
                          max_value=8,
                          increment=2,
                          default=6
                          ),
            bs.IntChoiceSetting(get_lang_text('settingBombVelocity'),
                                choices=[
                ('Slow', 2),
                ('Normal', 4),
                ('Fast', 6),
                ('Very Fast', 8)
            ],
                default=4
            ),
            bs.BoolSetting(get_lang_text('settingBombFollowsPlayer'), default=False),
            bs.BoolSetting(get_lang_text('settingEpicMode'), default=False),
        ]
        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return (issubclass(sessiontype, bs.DualTeamSession)
                or issubclass(sessiontype, bs.FreeForAllSession))

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> list[str]:
        return [
            'Football Stadium'
        ]

    def get_instance_description(self) -> Union[str, Sequence]:
        """Description On Big Message On Begin"""
        return f"{get_lang_text('gameDescInGame')}! By FluffyPal :)\n"

    def get_instance_description_short(self) -> Union[str, Sequence]:
        """Description In Game On Top Left"""
        return f"{get_lang_text('gameDescInGame')}!"

    def __init__(self, settings: dict[str, Any]):
        super().__init__(settings)
        self._time_limit = float(settings[get_lang_text('settingTimeLimit')])

        self._player_lives = int(settings[get_lang_text('settingPlayerLives')])
        self._max_hit = int(settings[get_lang_text('settingMaxHit')])
        self._box_count = int(settings[get_lang_text('settingBoxCount')])
        self._bomb_speed = int(settings[get_lang_text('settingBombVelocity')])

        self._is_aim_bot = bool(settings[get_lang_text('settingBombFollowsPlayer')])
        self._epic_mode = bool(settings[get_lang_text('settingEpicMode')])

        self.aim_timer: bs.Timer | None = None
        self.delay_update_timer: bs.Timer | None = None

        self.bombs: list[FpBomb] = []

        musics = [
            bs.MusicType.SURVIVAL, bs.MusicType.FLYING, bs.MusicType.MARCHING,
            bs.MusicType.GRAND_ROMP, bs.MusicType.FORWARD_MARCH
        ]

        """Default Configurations"""
        self.default_music = choice(musics)
        self.slow_motion = self._epic_mode

        self._call_bomb_delay = 1.5
        self.hp_range = 50

        """For End Game Logic"""
        self._timer: Optional[OnScreenTimer] = None
        self._last_player_death_time: Optional[float] = None

        self._bomb_boxes: list[BombBox] = []

        self._players_ingame: list[Player] = []

        self._team_count = 0

    def on_player_join(self, player: Player) -> None:
        """Main Func To Handle Player Joins Logic"""
        if self.has_begun():
            bs.broadcastmessage(bs.Lstr(resource='playerDelayedJoinText',
                                subs=[('${PLAYER}', player.getname(full=True))]),
                                color=(0, 1, 0), transient=True)

            player.survived = False
            player.lives = 0

            assert self._timer is not None
            player.death_time = self._timer.getstarttime()  # Make Their Scores To Zero
            return

        self._players_ingame.append(player)
        player.icons = [Icon(player, position=(0, 75), scale=0.8, show_lives=True)]
        player.lives = self._player_lives
        self.spawn_player(player)  # Spawn Player

    def on_player_leave(self, player: Player) -> None:
        """Main Func To Handle Player Leaves Logic"""
        super().on_player_leave(player)

        if player.survived:
            self._update_icons()

        player.survived = False
        player.icons.clear()
        player.lives = 0

        self.check_end()

    def on_begin(self) -> None:
        """On Game Begin"""
        super().on_begin()

        self._timer = OnScreenTimer()  # Timer
        assert self._timer is not None
        self._timer.start()  # Start Timer
        self.setup_standard_time_limit(self._time_limit)
        """self.credit = bs.newnode('text', attrs={
                            'text': "Created By FluffyPal",
                            'scale': 0.75,
                            'position': (0, 80),
                            'shadow': 1,
                            'flatness': 1.2,
                            'color': (1.5, .85, 1),
                            'h_align': 'center',
                            'v_attach': 'bottom'})
        Make a lovely Credit :)
        bs.animate_array(
            self.credit, 'color', 3,{
                    0: (1.5, .85, 1),
                    1.5: self.colors[0],
                    3: self.colors[1],
                    4.5: self.colors[2],
                    6: self.colors[3],
                    7.5: self.colors[4],
                    9: (1.5, .85, 1),
            }, loop=True
        )"""
        self.add_credit()

        self._team_count = len(self.teams)

        self._update_icons()  # Update Player' Icons
        # self.setup_standard_powerup_drops()

        self.make_round()
        bs.timer(3 if not self.globalsnode.slow_motion else 3*0.3, self.check_end)

    ################################ Game Stuff ################################
    def make_round(self):
        self.add_wall()

        delay = 5 if not self.globalsnode.slow_motion else 5*0.3
        bs.timer(delay, self.create_bomb_boxes)
        bs.timer(delay*1.5, self.start_aim)

    def start_select_random_box_and_aim(self, player: Player | None = None):
        if self.has_ended() and not any(player.survived for player in self.players):
            return

        box = choice(self._bomb_boxes)
        box.aim_player(player)
        delay = self._call_bomb_delay if not self.globalsnode.slow_motion else self._call_bomb_delay * 0.4
        self.aim_timer = bs.Timer(delay, bs.CallPartial(
            self.start_select_random_box_and_aim, player))

    def start_aim(self):
        self.start_select_random_box_and_aim()
        delay = 1 if not self.globalsnode.slow_motion else 1 * 0.3
        self.delay_update_timer = bs.Timer(delay, self.update_delay, repeat=True)

    def stop_aim(self):
        self.aim_timer = None
        self.delay_update_timer = None

    def reset_bombs_gravity(self):
        for bomb in self.bombs:
            if bomb.node and bomb.node.exists():
                bomb.node.gravity_scale = 3

    def update_delay(self):
        if self._call_bomb_delay > 0.150:
            self._call_bomb_delay -= 0.0275

    def create_bomb_boxes(self):
        x_bound = 12.5
        z_bound = 5
        y_pos = 0.8
        boxes_per_side = self._box_count // 2

        for i in range(boxes_per_side):
            x_pos = -x_bound
            z_pos = z_bound * (i / (boxes_per_side - 1)) * 2 - z_bound
            b = BombBox(position=(x_pos, y_pos, z_pos),
                        velocity_strength=self._bomb_speed, is_aimbot=self._is_aim_bot)
            self._bomb_boxes.append(b)

        for i in range(boxes_per_side):
            x_pos = x_bound
            z_pos = z_bound * (i / (boxes_per_side - 1)) * 2 - z_bound
            b = BombBox(position=(x_pos, y_pos, z_pos),
                        velocity_strength=self._bomb_speed, is_aimbot=self._is_aim_bot)
            self._bomb_boxes.append(b)

    def add_wall(self):
        x_bound = 11.5
        z_bound = 5.5

        shared = SharedObjects.get()
        material = bs.Material()

        material.add_actions(
            conditions=(
                ('they_are_different_node_than_us',),
                'and',
                ('they_have_material', shared.player_material)
            ),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', True),
            ),
        )

        bs.newnode(  # wall_x_left
            'region',
            attrs={
                'position': (-x_bound, 5.5, 0),
                'scale': (0.2, 15, 20),
                'type': 'box',
                'materials': [material],
            }
        )
        bs.newnode(  # wall_x_right
            'region',
            attrs={
                'position': (x_bound, 5.5, 0),
                'scale': (0.2, 15, 20),
                'type': 'box',
                'materials': [material],
            }
        )
        bs.newnode(  # wall_z_top
            'region',
            attrs={
                'position': (0, 5.5, -z_bound),
                'scale': (27.5, 15, 0.2),
                'type': 'box',
                'materials': [material],
            }
        )
        bs.newnode(  # wall_z_bottom
            'region',
            attrs={
                'position': (0, 5.5, z_bound+0.5),
                'scale': (27.5, 15, 0.2),
                'type': 'box',
                'materials': [material],
            }
        )
    ################################ Game Stuff ################################

    def add_credit(self):
        # Split text into individual characters
        text = "Created By FluffyPal"
        x_pos = get_string_width(text, True)/100  # Starting x position based on text length

        self.credit_nodes = []
        for i, char in enumerate(text, 1):
            node = bs.newnode('text', attrs={
                'text': char,
                'scale': 0.025,
                'position': (-x_pos+i*0.25, 0.225, -6),  # Space out characters
                'shadow': 1,
                'flatness': 1.2,
                'opacity': 0.2,
                'color': _colors[(i-1) % _colors_len],
                'in_world': True,
                'h_align': 'center',
                'v_attach': 'bottom'
            })
            self.credit_nodes.append(node)

            bs.animate_array(node, 'color', 3,
                             keys=COLORS_KEYS,  # pyright: ignore[reportArgumentType]
                             loop=True, offset=rainbow_start_delay*i
                             )

    def _update_icons(self) -> None:
        # In free-for-all mode, everyone is just lined up along the bottom.
        if isinstance(self.session, bs.FreeForAllSession):
            count = len(self.teams)
            x_offs = 85
            xval = x_offs * (count - 1) * -0.5
            for team in self.teams:
                if len(team.players) == 1:
                    player: Player = team.players[0]
                    for icon in player.icons:
                        icon.set_position_and_scale((xval, 30), 0.7)
                        icon.update_for_lives()
                    xval += x_offs

        # In teams mode we split up teams.
        else:
            for team in self.teams:
                if team.id == 0:
                    xval = -50
                    x_offs = -85
                else:
                    xval = 50
                    x_offs = 85
                for player in team.players:
                    for icon in player.icons:
                        icon.set_position_and_scale((xval, 30), 0.7)
                        icon.update_for_lives()
                    xval += x_offs

    def spawn_player(self, player: Player) -> bs.Actor:
        spaz = FpPlayerSpaz(
            player=player,
            color=player.color,
            highlight=player.highlight,
            character=player.character,
        )
        player.actor = spaz
        player.actor.node.name_color = safecolor(player.color, target_intensity=0.75)

        spaz.connect_controls_to_player(
            enable_punch=False,
            enable_bomb=False,
            enable_pickup=False
        )
        if player.lives <= 1:
            spaz.play_big_death_sound = True

        for icon in player.icons:
            icon.handle_player_spawned()

        maxhp = self.hp_range * self._max_hit  # Each dmg will be self.hp_range
        spaz.hitpoints = maxhp
        spaz.hitpoints_max = maxhp

        self.add_hitpoint_tag(spaz)

        position = (uniform(-3, 3), 0.45, uniform(-3, 3))
        spaz.handlemessage(bs.StandMessage(position))
        return spaz

    def add_hitpoint_tag(self, playerspaz: FpPlayerSpaz):
        """Add HitPoint Tag To A Player"""
        player = playerspaz.getplayer(Player, True)

        math_node = bs.newnode(
            'math',
            owner=playerspaz.node,
            attrs={
                'input1': (0, -0.5, 0),
                'operation': 'add'
            }
        )

        hitpoint = self.get_player_hitpoint(player)
        hitpoint_text = f'{int(hitpoint)}' if hitpoint > 1 else charstr(SpecialChar.SKULL)

        text_node = bs.newnode('text',
                               owner=playerspaz.node,
                               attrs={
                                   'text': hitpoint_text,
                                   'in_world': True,
                                   'shadow': 1.25,
                                   'color': player.color,
                                   'flatness': 2.0,
                                   'scale': 0.0175,
                                   'h_align': 'center'
                               }
                               )

        playerspaz.node.connectattr('torso_position', math_node, 'input2')
        math_node.connectattr('output', text_node, 'position')

        player.hitpoint_tag = text_node

    def update_hitpoint_tag(self, player: Player):
        """Update HitPoint Tag (SHOULD EXIST FIRST)"""
        if player.exists() and player.hitpoint_tag and player.hitpoint_tag.exists():
            if self._has_ended:
                player.hitpoint_tag.scale = 0.02
                player.hitpoint_tag.color = (1, 1, 1)
                hitpoint_text = charstr(SpecialChar.HEART)

            elif (hitpoint := self.get_player_hitpoint(player)) > 0:
                hitpoint_text = f'{int(hitpoint)}' if hitpoint > 1 else charstr(SpecialChar.SKULL)

            else:  # hitpoint <= 0
                hitpoint_text = charstr(SpecialChar.LOGO_FLAT)

            player.hitpoint_tag.text = hitpoint_text

    def get_player_hitpoint(self, player: Player) -> int:
        """Get player logical/fixed hitpoint(s) left"""
        p_actor = player.actor
        assert isinstance(p_actor, FpPlayerSpaz)
        return int(p_actor.hitpoints // self.hp_range)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            player = msg.getplayer(Player)

            player.lives -= 1

            for icon in player.icons:
                icon.handle_player_died()

            self.update_hitpoint_tag(player)

            if player_killing := msg.getkillerplayer(Player):
                if player_killing.team.id != player.team.id:
                    assert isinstance(player_killing.actor, FpPlayerSpaz)
                    player_killing.actor.node.handlemessage(
                        "celebrate_r", (2000 if not self.globalsnode.slow_motion else 2000*0.5)
                    )  # Hooray

            if player.lives <= 0:
                curtime = bs.time()
                self._last_player_death_time = curtime
                player.survived = False
                # Record the player's moment of death
                player.death_time = curtime
            else:
                self.respawn_player(player, 2 if not self.globalsnode.slow_motion else 2*0.3)

            bs.pushcall(self.check_end)

        elif isinstance(msg, FpHitByBomb):
            playerspaz = msg.playerspaz
            player = playerspaz.getplayer(Player, True)

            if playerspaz.hitpoints > 50:
                playerspaz.hitpoints -= 50  # Each dmg will be 50

            else:
                playerspaz.handlemessage(bs.DieMessage(False, bs.DeathType.IMPACT))

            self.update_hitpoint_tag(player)

        return super().handlemessage(msg)

    def check_end(self):
        """Basic check end logic for mostly all lives-based games"""
        alive_teams = 0
        end_time = 2 if not self.globalsnode.slow_motion else 1.0
        for team in self.teams:
            for player in team.players:
                if player.survived:
                    alive_teams += 1
                    break

        if alive_teams <= 1:
            self.stop_aim()
            self.reset_bombs_gravity()
            bs.timer(end_time, self.end_game)

    def end_game(self) -> None:
        """End game logic for timer and lives based games"""
        if self.has_ended():
            return

        players: list[Player] = []
        if len(self._players_ingame) > 1 and self._team_count > 1:
            cur_time = bs.time() * (1 if not self.globalsnode.slow_motion else 3.33)
            assert self._timer is not None
            start_time = self._timer.getstarttime()
            # Mark death-time as now for any still-living players
            # and award players points for how long they lasted
            # (these per-player scores are only meaningful in team-games)
            for team in self.teams:
                for player in team.players:
                    if player.survived:
                        players.append(player)
                    survived = False

                    # Throw an extra fudge factor in so teams that
                    # didn't die come out ahead of teams that did
                    if player.death_time is None:
                        survived = True
                        player.death_time = cur_time + 1

                    # Award a per-player score depending on how many seconds
                    # they lasted (per-player scores only affect teams mode;
                    # everywhere else just looks at the per-team score)
                    score = 0
                    if player.death_time:
                        score = int(player.death_time - self._timer.getstarttime())
                    if survived:
                        score += 100  # A bit extra for survivors
                    self.stats.player_scored(player, score, screenmessage=False)

            # Stop updating our time text, and set the final time to match
            # exactly when our last guy died
            self._timer.stop(endtime=self._last_player_death_time)

            # Ok now calc game results: set a score for each team and then tell
            # the game to end
            results = bs.GameResults()

            # Remember that 'free-for-all' mode is simply a special form
            # of 'teams' mode where each player gets their own team, so we can
            # just always deal in teams and have all cases covered
            for team in self.teams:

                # Set the team score to the max time survived by any player on
                # that team
                longest_life = 0.0
                for player in team.players:
                    assert player.death_time is not None
                    longest_life = max(longest_life, player.death_time - start_time)

                # Submit the score value in milliseconds
                results.set_team_score(team, int(1000.0 * longest_life))
        else:
            results = bs.GameResults()

        self.end(results=results)
        for player in players:
            self.update_hitpoint_tag(player)


"""###################################### Props ######################################"""


class BombBox(bs.Actor):
    def __init__(self, position: Sequence[float], velocity_strength: float = 4, is_aimbot: bool = False) -> None:

        super().__init__()
        self.velocity_strength = velocity_strength
        self._is_aim_bot = is_aimbot
        self.bomb_y_pos = 0.45
        self.box_scale = 1.4
        self.activity: FluffysGame5

        shared = SharedObjects.get()
        box_material = bs.Material()

        # Make box only collide with players
        box_material.add_actions(
            conditions=(
                ('they_have_material', shared.attack_material),
                'or',
                ('they_have_material', shared.pickup_material)
            ),
            actions=(
                ('modify_part_collision', 'collide', False),
                ('modify_part_collision', 'physical', False),
            ),
        )

        box_material.add_actions(
            conditions=(
                ('they_dont_have_material', shared.footing_material)
            ),
            actions=(
                ('modify_part_collision', 'collide', False),
                ('modify_part_collision', 'physical', False),
            ),
        )

        self.node = bs.newnode(
            'prop',
            delegate=self,
            attrs={
                'body': 'box',
                'reflection': 'powerup',
                'position': position,
                'mesh': bs.getmesh('powerup'),
                'light_mesh': bs.getmesh('powerupSimple'),
                'color_texture': bs.gettexture('landMineLit'),
                'shadow_size': 0.5,
                'body_scale': self.box_scale,
                'mesh_scale': self.box_scale,
                'reflection_scale': [1.0],
                'materials': [box_material]
            }
        )

    # Main Trigger
    def aim_player(self, player: Player | None):
        """Aim random `alive` player with Bomb"""
        if not player:
            players: list[Player] = self.activity.players
            if alive_players := [p for p in players if p.is_alive()]:  # Let's find player that is not ded
                player = choice(alive_players)
            else:
                return

        self.spawn_bomb_and_target_player(player)

    def spawn_bomb_and_target_player(self, player: Player):
        # 0.8 Blast Radius = 60 dmg on head | Update 25-5-2025: No need BlastRadius Yay
        bomb = FpBomb(
            position=(self.node.position[0], self.bomb_y_pos, self.node.position[2]),
            blast_radius=1,
            bomb_type='impact',
            source_player=player,
            owner=player.node
        )
        bomb.node.gravity_scale = 0.0

        self.activity.bombs.append(bomb)

        if self._is_aim_bot:
            self._update_bomb_position_aimbot(player, bomb)
        else:
            self._update_bomb_position_straight(player, bomb)
        self.pulse_box()

    # AIM TYPE
    def _update_bomb_position_aimbot(self, player: Player, bomb: FpBomb):
        """Target a bomb to player: constantly following player"""
        # if not player.is_alive() and bomb.node.exists():
        # bomb.node.gravity_scale = 1
        # return
        if player.exists() and bomb.node.exists():
            p_pos = player.node.position
            p_init_pos = (p_pos[0], self.bomb_y_pos, p_pos[2])

            b_pos = bomb.node.position
            b_init_pos = (b_pos[0], self.bomb_y_pos, b_pos[2])
            direction = (bs.Vec3(p_init_pos) - bs.Vec3(b_init_pos)).normalized()

            bomb.node.velocity = (direction * self.velocity_strength)
            time_follow = 1 if not self.activity.slow_motion else 1*0.3
            bs.timer(time_follow, bs.CallPartial(self._update_bomb_position_aimbot, player, bomb))

    # AIM TYPE
    def _update_bomb_position_straight(self, player: Player, bomb: FpBomb):
        """Target a bomb to player: straight with constant speed from initial position"""
        if player.exists() and bomb.node.exists():
            p_pos = player.node.position
            p_init_pos = (p_pos[0], self.bomb_y_pos, p_pos[2])

            b_pos = bomb.node.position
            b_init_pos = (b_pos[0], self.bomb_y_pos, b_pos[2])

            direction = (bs.Vec3(p_init_pos) - bs.Vec3(b_init_pos)).normalized()
            bomb.node.velocity = (direction * self.velocity_strength)
            # HACK: The hek do it need this to move
            bs.timer(99, bs.CallPartial(self._update_bomb_position_straight, player, bomb))

    def pulse_box(self):
        bs.animate(
            self.node,
            "mesh_scale", {
                0.00: self.box_scale,
                0.05: self.box_scale+(self.box_scale*0.3),
                0.10: self.box_scale,
            }
        )
# Hohoho, whatcha doing here?
