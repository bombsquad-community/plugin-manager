# coding=utf-8
import bs


def bsGetAPIVersion():
    return 4


def bsGetGames():
    return [FlyBoxingGame]


class FlyBoxingGame(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return 'Fly'

    @classmethod
    def getDescription(cls, sessionType):
        return ('Fight')

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if (issubclass(sessionType, bs.TeamsSession)
                        or issubclass(sessionType, bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls, sessionType):
        return bs.getMapsSupportingPlayType("melee")

    @classmethod
    def getSettings(cls, sessionType):
        return [
            ("胜利所需要的击杀数", {'minValue': 1, 'default': 5, 'increment': 1}),
            ("Time Limit", {'choices': [('无', 0), ('1 分钟', 60),
                                        ('2 分钟', 120), ('5 分钟', 300),
                                        ('10 分钟', 600), ('20 分钟', 1200)], 'default': 0}),
            ("Respawn Times",
             {'choices': [('很短', 0.25), ('短', 0.5), ('正常', 1.0), ('长', 2.0), ('很长', 4.0)],
              'default': 1.0}),
            # ("史诗模式", {'default': True}),
        ]

    def __init__(self, settings):
        bs.TeamGameActivity.__init__(self, settings)
        # if self.settings['史诗模式']: self._isSlowMotion = True
        self._isSlowMotion = True  # 默认史诗模式，不改了

        # print messages when players die since it matters here..
        self.announcePlayerDeaths = True

        self._scoreBoard = bs.ScoreBoard()

    def getInstanceDescription(self):
        return ('对BOSS造成伤害最高者获胜')

    def getInstanceScoreBoardDescription(self):
        return ('对BOSS造成伤害最高者获胜')

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic')  # if self.settings['史诗模式'] else 'GrandRomp')

    def onTeamJoin(self, team):
        team.gameData['score'] = 0
        if self.hasBegun(): self._updateScoreBoard()

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self._scoreToWin = 10000
        self._updateScoreBoard()
        self._dingSound = bs.getSound('dingSmall')

    def spawnPlayer(self, player):
        name = player.getName(full=True)
        spaz = self.spawnPlayerSpaz(player)
        spaz.connectControlsToPlayer(enablePunch=True,
                                     enableBomb=True,
                                     enablePickUp=True)

        spaz.node.fly = True


    def handleMessage(self, m):

        if isinstance(m, bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self, m)  # augment standard behavior

            player = m.spaz.getPlayer()
            self.respawnPlayer(player)

            killer = m.killerPlayer
            if killer is None: return

            # handle team-kills
            if killer.getTeam() is player.getTeam():

                # in free-for-all, killing yourself loses you a point
                if isinstance(self.getSession(), bs.FreeForAllSession):
                    player.getTeam().gameData['score'] = max(0, player.getTeam().gameData['score'] - 1)

                # in teams-mode it gives a point to the other team
                else:
                    bs.playSound(self._dingSound)
                    for team in self.teams:
                        if team is not killer.getTeam():
                            team.gameData['score'] += 1

            # killing someone on another team nets a kill
            else:
                killer.getTeam().gameData['score'] += 1
                bs.playSound(self._dingSound)
                # in FFA show our score since its hard to find on the scoreboard
                try:
                    killer.actor.setScoreText(str(killer.getTeam().gameData['score']) + '/' + str(self._scoreToWin),
                                              color=killer.getTeam().color, flash=True)
                except Exception:
                    pass

            self._updateScoreBoard()

            # if someone has won, set a timer to end shortly
            # (allows the dust to clear and draws to occur if deaths are close enough)
            if any(team.gameData['score'] >= self._scoreToWin for team in self.teams):
                bs.gameTimer(500, self.endGame)

        else:
            bs.TeamGameActivity.handleMessage(self, m)

    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team, team.gameData['score'], self._scoreToWin)

    def endGame(self):
        results = bs.TeamGameResults()
        for t in self.teams: results.setTeamScore(t, t.gameData['score'])
        self.end(results=results)
