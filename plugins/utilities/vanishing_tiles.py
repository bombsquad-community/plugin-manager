# ba_meta require api 9
from __future__ import annotations
from bascenev1lib.gameutils import SharedObjects
import bascenev1 as bs
import babase
import random
from typing import Optional, List, Dict, Any

# Vanishing Tiles - BombSquad Minigame
# Tiles disappear one by one. Survive all rounds to win.
# Last player/team standing takes the crown.

plugman = dict(
    plugin_name="vanishing_tiles",
    description="Tiles disappear gradually. Survive each round to continue. Last player standing wins!",
    external_url="https://discord.gg/sQGDsztQcy",
    authors=[
        {"name": "Mr.ghosty", "email": "", "discord": "gaurangbroyo"},
        {"name": "senchx",    "email": "", "discord": "senchx0"},
    ],
    version="2.0.0",
)


class Player(bs.Player['Team']):
    def __init__(self) -> None:
        super().__init__()
        self.death_time: Optional[float] = None


class Team(bs.Team[Player]):
    pass


# ba_meta export bascenev1.GameActivity
class VanishingTilesGame(bs.TeamGameActivity[Player, Team]):

    name = 'Vanishing Tiles'
    description = 'Tiles disappear one by one. Be the last one standing!'
    scoreconfig = bs.ScoreConfig(label='Survived', scoretype=bs.ScoreType.MILLISECONDS)
    announce_player_deaths = True

    @classmethod
    def get_available_settings(cls, sessiontype: type[bs.Session]) -> list[babase.Setting]:
        return [
            bs.BoolSetting('Epic Mode', default=False),
            bs.BoolSetting('Show Credits', default=True),
        ]

    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, (bs.FreeForAllSession, bs.DualTeamSession))

    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Vanishing Tiles Arena']

    def __init__(self, settings: dict) -> None:
        super().__init__(settings)
        self._epic_mode:     bool = bool(settings.get('Epic Mode', False))
        self._show_credits:  bool = bool(settings.get('Show Credits', True))
        self.default_music = bs.MusicType.EPIC if self._epic_mode else bs.MusicType.SURVIVAL

        self._round:          int = 1
        self._removing:       bool = False
        self._game_start_time: Optional[float] = None

        self._tile_nodes:   Dict[int, bs.Node] = {}
        self._region_nodes: Dict[int, bs.Node] = {}
        self._present_tile_ids: set[int] = set()

        self._remove_speed: float = 1.8

        self._collide_mat = bs.Material()
        self._collide_mat.add_actions(actions=(('modify_part_collision', 'collide', True),))
        self._no_collide_mat = bs.Material()
        self._no_collide_mat.add_actions(actions=(('modify_part_collision', 'collide', False),))

        self._default_tex = bs.gettexture('powerupHealth')
        self._warn_tex = bs.gettexture('powerupCurse')
        self._final_tex = bs.gettexture('powerupPunch')

        self._hud_round:   Optional[bs.Node] = None
        self._hud_players: Optional[bs.Node] = None
        self._hud_tiles:   Optional[bs.Node] = None
        self._credit_node: Optional[bs.Node] = None

        if self._epic_mode:
            self.slow_motion = True

    def spawn_player(self, player: Player) -> Any:
        if isinstance(self.session, bs.FreeForAllSession):
            pos = VanishingTilesMapDefs.points['spawn1']
            spaz = self.spawn_player_spaz(player, position=pos)
        else:
            spaz = self.spawn_player_spaz(player)
        spaz.connect_controls_to_player(
            enable_punch=False, enable_pickup=False, enable_bomb=False)
        spaz.set_bomb_count(0)
        return spaz

    def on_begin(self) -> None:
        super().on_begin()
        self._game_start_time = bs.time()

        if self._show_credits:
            self._credit_node = bs.newnode('text', attrs={
                'text':     'Made by Mr.Ghosty',
                'scale':    0.7,
                'position': (0, 8),
                'shadow':   0.8,
                'flatness': 1.0,
                'color':    (1.0, 0.3, 0.8, 1.0),
                'h_align':  'center',
                'v_attach': 'bottom',
            })
            bs.animate_array(self._credit_node, 'color', 4, {
                0.0: [1.0, 0.3, 0.8, 1.0],
                1.0: [0.3, 0.8, 1.0, 1.0],
                2.0: [0.4, 1.0, 0.4, 1.0],
                3.0: [1.0, 1.0, 0.2, 1.0],
                4.0: [1.0, 0.3, 0.8, 1.0],
            }, loop=True)

        self._build_hud()
        self._cleanup_tiles()
        self._spawn_all_tiles()
        self._show_round_banner()

        if not isinstance(self.session, bs.FreeForAllSession):
            if not all(len(t.players) >= 1 for t in self.teams):
                bs.broadcastmessage('Not enough players — draw!', color=(1, 1, 0))
                bs.timer(1.0, bs.CallStrict(self.end, bs.GameResults()))
                return

        bs.timer(1.0, self._check_initial_state)
        bs.timer(3.0, self._start_removal)

    def _build_hud(self) -> None:
        for attr in ('_hud_round', '_hud_players', '_hud_tiles'):
            node = getattr(self, attr, None)
            if node:
                try:
                    node.delete()
                except Exception:
                    pass
            setattr(self, attr, None)

        self._hud_round = bs.newnode('text', attrs={
            'text': '', 'scale': 0.85, 'position': (0, -40),
            'maxwidth': 300, 'h_align': 'center', 'v_align': 'center',
            'v_attach': 'top', 'h_attach': 'center',
            'shadow': 1.0, 'flatness': 1.0, 'color': (1, 1, 1, 1),
            'in_world': False,
        })
        self._hud_players = bs.newnode('text', attrs={
            'text': '', 'scale': 0.8, 'position': (0, -58),
            'maxwidth': 300, 'h_align': 'center', 'v_align': 'center',
            'v_attach': 'top', 'h_attach': 'center',
            'shadow': 1.0, 'flatness': 1.0, 'color': (1, 0.8, 0.2, 1),
            'in_world': False,
        })
        self._hud_tiles = bs.newnode('text', attrs={
            'text': '', 'scale': 0.8, 'position': (0, -74),
            'maxwidth': 300, 'h_align': 'center', 'v_align': 'center',
            'v_attach': 'top', 'h_attach': 'center',
            'shadow': 1.0, 'flatness': 1.0, 'color': (0.5, 1.0, 0.5, 1),
            'in_world': False,
        })
        self._refresh_hud()

    def _refresh_hud(self) -> None:
        alive = len([p for p in self.players if p.is_alive()])
        tiles = len(self._present_tile_ids)
        urgent = tiles <= 4

        if self._hud_round:
            self._hud_round.text = f'Round {self._round}'

        if self._hud_players:
            self._hud_players.text = f'Players alive: {alive}'

        if self._hud_tiles:
            self._hud_tiles.color = (1.0, 0.3, 0.3, 1) if urgent else (0.5, 1.0, 0.5, 1)
            self._hud_tiles.text = f'Tiles left: {tiles}'

    def _show_round_banner(self) -> None:
        node = bs.newnode('text', attrs={
            'text':     f'Round {self._round}',
            'scale':    1.3,
            'position': (0, 60),
            'shadow':   1.2,
            'flatness': 0.7,
            'color':    (1, 1, 0, 1),
            'h_align':  'center',
            'v_attach': 'center',
            'in_world': False,
        })
        bs.animate(node, 'scale', {0: 0.0, 0.15: 1.3, 2.0: 1.3, 2.5: 0.0})
        bs.timer(2.6, bs.CallStrict(node.delete))

    def on_player_join(self, player: Player) -> None:
        if self.has_begun():
            player.death_time = bs.time()
            bs.broadcastmessage(
                f'{player.getname()} joined! Currently Round {self._round} — '
                f'{len(self._present_tile_ids)} tiles left.',
                color=(0.5, 1.0, 1.0),
                transient=True,
            )
            return
        self.spawn_player(player)

    def _check_initial_state(self) -> None:
        if not [p for p in self.players if p.is_alive()]:
            bs.timer(1.0, self._check_end_game)

    def _spawn_all_tiles(self) -> None:
        positions = [
            (4.5, 2, -9), (4.5, 2, -6), (4.5, 2, -3), (4.5, 2, 0),
            (1.5, 2, -9), (1.5, 2, -6), (1.5, 2, -3), (1.5, 2, 0),
            (-1.5, 2, -9), (-1.5, 2, -6), (-1.5, 2, -3), (-1.5, 2, 0),
            (-4.5, 2, -9), (-4.5, 2, -6), (-4.5, 2, -3), (-4.5, 2, 0),
        ]
        model = bs.getmesh('buttonSquareOpaque')
        shared = SharedObjects.get()
        for i, pos in enumerate(positions):
            tile = bs.newnode('prop', attrs={
                'body':           'puck',
                'position':       pos,
                'mesh':           model,
                'mesh_scale':     3.73,
                'body_scale':     3.73,
                'gravity_scale':  0.0,
                'color_texture':  self._default_tex,
                'reflection':     'soft',
                'materials':      [self._no_collide_mat],
            })
            region = bs.newnode('region', attrs={
                'position':  pos,
                'scale':     (3.5, 0.1, 3.5),
                'type':      'box',
                'materials': [self._collide_mat, shared.footing_material],
            })
            self._tile_nodes[i] = tile
            self._region_nodes[i] = region
            self._present_tile_ids.add(i)
        self._refresh_hud()

    def _start_removal(self) -> None:
        if not self._removing:
            self._removing = True
            self._remove_next_tile()

    def _make_final_tile(self) -> None:
        try:
            tile_id = list(self._present_tile_ids)[0]
            tile = self._tile_nodes.get(tile_id)
            if tile and tile.exists():
                tile.color_texture = self._final_tex
        except Exception:
            pass

        self.slow_motion = True
        bs.broadcastmessage('LAST TILE!', color=(1, 0.4, 0.1))
        for p in self.players:
            if p.is_alive() and p.actor and p.actor.exists():
                p.actor.node.handlemessage(bs.CelebrateMessage(3.0))

        self._refresh_hud()
        bs.timer(3.0, self._round_end_check)

    def _remove_next_tile(self) -> None:
        if len(self._present_tile_ids) <= 1:
            self._make_final_tile()
            return

        urgent = len(self._present_tile_ids) <= 4
        if urgent:
            bs.getsound('shieldDown').play(0.4)

        tile_id = random.choice(list(self._present_tile_ids))
        self._remove_tile(tile_id)
        bs.timer(self._remove_speed, self._remove_next_tile)

    def _remove_tile(self, tile_id: int) -> None:
        tile = self._tile_nodes.get(tile_id)
        region = self._region_nodes.get(tile_id)
        if tile is None or not tile.exists():
            self._present_tile_ids.discard(tile_id)
            return

        tile.color_texture = self._warn_tex

        def vanish() -> None:
            if tile.exists():
                bs.emitfx(
                    position=tile.position,
                    count=20, scale=0.9, spread=0.5,
                    chunk_type='spark',
                )
                tile.delete()
            if region and region.exists():
                region.delete()
            self._present_tile_ids.discard(tile_id)
            self._refresh_hud()

        bs.timer(1.0, vanish)

    def _round_end_check(self) -> None:
        self.slow_motion = self._epic_mode

        if not isinstance(self.session, bs.FreeForAllSession):
            living_teams = [
                t for t in self.teams if any(p.is_alive() for p in t.players)]
            if len(living_teams) <= 1:
                self._removing = False
                self.end_game()
                return
        else:
            if len([p for p in self.players if p.is_alive()]) <= 1:
                self._removing = False
                self.end_game()
                return

        self._remove_speed = max(0.3, self._remove_speed * 0.75)
        self._round += 1
        survivors = [p for p in self.players if p.is_alive()]
        bs.broadcastmessage(
            f'Round {self._round}! Speed increasing!', color=(0.5, 1.0, 1.0))
        bs.timer(1.5, bs.CallStrict(self._next_round, survivors))

    def _next_round(self, survivors: List[Player]) -> None:
        safety = bs.newnode('region', attrs={
            'position':  (0, 1.5, -5),
            'scale':     (20, 0.2, 20),
            'type':      'box',
            'materials': [SharedObjects.get().footing_material],
        })
        self._cleanup_tiles()
        self._spawn_all_tiles()
        self._show_round_banner()
        self._refresh_hud()

        for p in survivors:
            if p.actor and p.actor.exists():
                p.actor.handlemessage(
                    bs.StandMessage(VanishingTilesMapDefs.points['spawn1']))

        bs.timer(2.5, bs.CallStrict(safety.delete))
        self._removing = False
        bs.timer(3.0, self._start_removal)

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)
            p = msg.getplayer(Player)
            p.death_time = bs.time()
            self._refresh_hud()
            bs.timer(0.5, self._check_end_game)
            return None
        return super().handlemessage(msg)

    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        bs.timer(0.2, self._check_team_empty)

    def _check_team_empty(self) -> None:
        if self.has_ended():
            return
        if isinstance(self.session, bs.FreeForAllSession):
            return
        for team in self.teams:
            if len(team.players) == 0:
                winner = next((t for t in self.teams if t is not team), None)
                bs.broadcastmessage('A team has no players — game over!',
                                    color=(1, 1, 0))
                bs.timer(1.0, bs.CallStrict(self.end_game))
                return

    def _check_end_game(self) -> None:
        if not self.has_begun():
            return
        if not isinstance(self.session, bs.FreeForAllSession):
            if len([t for t in self.teams
                    if any(p.is_alive() for p in t.players)]) <= 1:
                self.end_game()
        else:
            if len([p for p in self.players if p.is_alive()]) == 0:
                self.end_game()

    def end_game(self) -> None:
        if self.has_ended():
            return
        cur_time = bs.time()
        start = self._game_start_time or cur_time
        results = bs.GameResults()
        for team in self.teams:
            longest = 0.0
            for p in team.players:
                death = p.death_time or (cur_time + 1)
                longest = max(longest, death - start)
            results.set_team_score(team, int(longest * 1000))

        for attr in ('_hud_round', '_hud_players', '_hud_tiles'):
            node = getattr(self, attr, None)
            if node:
                try:
                    node.delete()
                except Exception:
                    pass

        if self._credit_node:
            try:
                self._credit_node.delete()
            except Exception:
                pass

        self.end(results=results)

    def _cleanup_tiles(self) -> None:
        for n in list(self._tile_nodes.values()):
            if n.exists():
                n.delete()
        for n in list(self._region_nodes.values()):
            if n.exists():
                n.delete()
        self._tile_nodes.clear()
        self._region_nodes.clear()
        self._present_tile_ids.clear()


class VanishingTilesMapDefs:
    points = {'spawn1': (0, 3, -5)}
    boxes = {
        'area_of_interest_bounds': (0, 4, -5, 0, 0, 0, 16, 8, 16),
        'map_bounds':              (0, 4, -5, 0, 0, 0, 30, 14, 30),
    }


class VanishingTilesMap(bs.Map):
    defs = VanishingTilesMapDefs()
    name = 'Vanishing Tiles Arena'

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'powerupHealth'

    @classmethod
    def on_preload(cls) -> Any:
        return {
            'bgtex':  bs.gettexture('menuBG'),
            'bgmesh': bs.getmesh('thePadBG'),
        }

    def __init__(self) -> None:
        super().__init__()
        self.node = bs.newnode('terrain', attrs={
            'mesh':          self.preloaddata['bgmesh'],
            'lighting':      False,
            'background':    True,
            'color_texture': self.preloaddata['bgtex'],
        })


bs._map.register_map(VanishingTilesMap)


# ba_meta export babase.Plugin
class Main(babase.Plugin):
    def __init__(self) -> None:
        babase.app.classic.add_coop_practice_level(
            bs.Level(
                name='Vanishing Tiles',
                displayname='Vanishing Tiles',
                gametype=VanishingTilesGame,
                settings={},
                preview_texture_name='powerupHealth',
            )
        )
