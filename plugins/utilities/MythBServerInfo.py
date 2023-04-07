# -*- coding: utf-8 -*-
import bs                               #Created By MythB # http://github.com/MythB
import bsUtils
import bsInternal
import json
import os
from bsMap import Map, registerMap
import MythBAdminList as mbal

#statsfile = 'C:\Users\MythB\Desktop\SERVER STATS\stats.json'
statsfile = '/root/bs/stats/stats.json'
#Use your own file location here

##Create Empty Map
class MythBServerInfoMap(Map):
    import rampageLevelDefs as defs
    name = 'Player Stats By MythB'
    playTypes = ['MythB']

    @classmethod
    def getPreviewTextureName(cls):
        return 'rampageBGColor'

    def __init__(self):
        Map.__init__(self)

registerMap(MythBServerInfoMap)


def bsGetAPIVersion():
    return 4
# how BombSquad asks us what games we provide
def bsGetGames():
    return [MythBServerInfo]

class ScreenLanguageEnglish(object):
    customLang = 'CUSTOM POWERUPS'
    top15scoreLang = 'TOP 15 SCORERS'
    top15fighterLang = 'TOP 15 FIGHTERS'
    rankLang = 'Rank'
    avgPtsLang = 'avgPTS'
    kdLang = 'K/D'
    infoLang = '* you need to play at least 20 games to be listed !'
    speedInfoLang = 'Makes you run FASTER !\nyou\'ll love it'
    speedTextLang = 'SPEED BOOTS'
    superStarInfoLang = 'Makes you Invincible\nreally powerful !'
    superStarTextLang = 'SUPER STAR'
    iceCubeInfoLang = 'Makes you FROZEN ! \nKEEP AWAY !'
    iceCubeTextLang = 'ICE CUBE'
    surpriseInfoLang = 'Looks like Med-Pack\nbe careful \nit\'s FAKE !'
    surpriseTextLang = 'SURPRISE'
    martyInfoLang = 'Drops sticky bombs\nto your location\nwhen you were killed!'
    martyTextLang = 'MARTYRDOM'
    welcomeTextLang = 'welcome to Myth B. server'

class ScreenLanguageTurkish(object):
    customLang = 'ÖZEL GÜÇLENDİRİCİLER'
    top15scoreLang = 'İLK 15 SKORCU'
    top15fighterLang = 'İLK 15 DÖVÜŞÇÜ'
    rankLang = 'Sıra'
    avgPtsLang = 'ortPUAN'
    kdLang = 'K/D'
    infoLang = '* sıralamaya girmek için, en az 20 oyun oynamalısınız !'
    speedInfoLang = 'Daha hızlı koşmanı sağlar!\nHoşuna gidecek'
    speedTextLang = 'HIZ ÇİZMELERİ'
    superStarInfoLang = 'Seni Dokunulmaz yapar\naşırı güçlü !'
    superStarTextLang = 'SÜPER YILDIZ'
    iceCubeInfoLang = 'Seni DONDURUR ! \nUZAK DUR !'
    iceCubeTextLang = 'BUZ KÜPÜ'
    surpriseInfoLang = 'Sağlık-Paketine benziyor\nama SAHTE ! \ndikkat et !'
    surpriseTextLang = 'SÜRPRİZ'
    martyInfoLang = 'Öldürüldüğünüz konuma \nyapışkan bombalar\ndüşürür !'
    martyTextLang = 'ŞEHİTLİK'
    welcomeTextLang = 'Myth B. sunucusuna hoşgeldiniz'

ScreenLanguage = ScreenLanguageEnglish
if bs.getLanguage() == 'Turkish':
    ScreenLanguage = ScreenLanguageTurkish

class MythBServerInfo(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return ''

    @classmethod
    def getSupportedMaps(cls, sessionType):
        return [u'Player Stats By MythB']
    
    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)    
        scoreList = []
        kdList = []
        if os.path.exists(statsfile):
            try:
                with open(statsfile) as f:
                    data = json.loads(f.read())
                    for i in data:  #check if player never were killed # check if player played at least 20 games  else make all scores zero / names -- check id none
                        avgScore = data[i]['name_full'] if data[i]['played'] > 19 else \
                        '--', float(data[i]['scores']) / (data[i]['played']) if data[i]['played'] > 19 else \
                        0, i if data[i]['played'] > 19 else 'null'
                        kdRatio = data[i]['name_full'] if data[i]['played'] > 19 else \
                        '--', float(data[i]['kills']) / ( 1 if data[i]['killed'] == 0 else data[i]['killed']) if data[i]['played'] > 19 else \
                        0, i if data[i]['played'] > 19 else 'null'
                        #sorted(ortList,key=itemgetter(2))
                        #ortListy = sorted(ortList, key=itemgetter(2), reverse=True)
                        #print ortList   #0nick  2ortkill 4 ortkilled  6ort score
                        scoreList.append(avgScore)
                        kdList.append(kdRatio)
            except Exception as (e):
                print e
                bs.screenMessage('Unavailable Now ',color = (0.9,0,0))
        else:
            kdList = []
            scoreList = []
            print ('statsfile not exists')
        
        kdListSorted = sorted(kdList, key=lambda x: float(x[1]), reverse=True)
        scoreListSorted = sorted(scoreList, key=lambda x: float(x[1]), reverse=True)
        
        fighter1list = []
        fighter2and3list = []
        fighter15list = []
        scorer1list = []
        scorer2and3list = []
        scorer15list = []
        fighter1list.append((str(kdListSorted[0][2])if len(kdListSorted) > 0 else 'null'))
        fighter2and3list.append((str(kdListSorted[1][2])if len(kdListSorted) > 1 else 'null'))
        fighter2and3list.append((str(kdListSorted[2][2])if len(kdListSorted) > 2 else 'null'))
        scorer1list.append((str(scoreListSorted[0][2])if len(scoreListSorted) > 0 else 'null'))
        scorer2and3list.append((str(scoreListSorted[1][2])if len(scoreListSorted) > 1 else 'null'))
        scorer2and3list.append((str(scoreListSorted[2][2])if len(scoreListSorted) > 2 else 'null'))
        fighter15list.append((str(kdListSorted[3][2])if len(kdListSorted) > 3 else 'null'))
        fighter15list.append((str(kdListSorted[4][2])if len(kdListSorted) > 4 else 'null'))
        fighter15list.append((str(kdListSorted[5][2])if len(kdListSorted) > 5 else 'null'))
        fighter15list.append((str(kdListSorted[6][2])if len(kdListSorted) > 6 else 'null'))
        fighter15list.append((str(kdListSorted[7][2])if len(kdListSorted) > 7 else 'null'))
        fighter15list.append((str(kdListSorted[8][2])if len(kdListSorted) > 8 else 'null'))
        fighter15list.append((str(kdListSorted[9][2])if len(kdListSorted) > 9 else 'null'))
        fighter15list.append((str(kdListSorted[10][2])if len(kdListSorted) > 10 else 'null'))
        fighter15list.append((str(kdListSorted[11][2])if len(kdListSorted) > 11 else 'null'))
        fighter15list.append((str(kdListSorted[12][2])if len(kdListSorted) > 12 else 'null'))
        fighter15list.append((str(kdListSorted[13][2])if len(kdListSorted) > 13 else 'null'))
        fighter15list.append((str(kdListSorted[14][2])if len(kdListSorted) > 14 else 'null'))
        scorer15list.append((str(scoreListSorted[3][2])if len(scoreListSorted) > 3 else 'null'))
        scorer15list.append((str(scoreListSorted[4][2])if len(scoreListSorted) > 4 else 'null'))
        scorer15list.append((str(scoreListSorted[5][2])if len(scoreListSorted) > 5 else 'null'))
        scorer15list.append((str(scoreListSorted[6][2])if len(scoreListSorted) > 6 else 'null'))
        scorer15list.append((str(scoreListSorted[7][2])if len(scoreListSorted) > 7 else 'null'))
        scorer15list.append((str(scoreListSorted[8][2])if len(scoreListSorted) > 8 else 'null'))
        scorer15list.append((str(scoreListSorted[9][2])if len(scoreListSorted) > 9 else 'null'))
        scorer15list.append((str(scoreListSorted[10][2])if len(scoreListSorted) > 10 else 'null'))
        scorer15list.append((str(scoreListSorted[11][2])if len(scoreListSorted) > 11 else 'null'))
        scorer15list.append((str(scoreListSorted[12][2])if len(scoreListSorted) > 12 else 'null'))
        scorer15list.append((str(scoreListSorted[13][2])if len(scoreListSorted) > 13 else 'null'))
        scorer15list.append((str(scoreListSorted[14][2])if len(scoreListSorted) > 14 else 'null'))
        
        with open(bs.getEnvironment()['systemScriptsDirectory'] + "/MythBAdminList.py") as file:
          s = [row for row in file]
          s[1] = 'Fighter1stList = ' + str(fighter1list) + '\n'
          s[2] = 'Fighter2nd3rd = '+ str(fighter2and3list) + '\n'
          s[3] = 'FighterTop15List = '+ str(fighter15list) + '\n'
          s[4] = 'Scorer1stList = '+ str(scorer1list) + '\n'
          s[5] = 'Scorer2nd3rdList = '+ str(scorer2and3list) + '\n'
          s[6] = 'ScorerTop15List = '+ str(scorer15list) + '\n'
          f = open(bs.getEnvironment()['systemScriptsDirectory'] + "/MythBAdminList.py",'w')
          for updates in s:
              f.write(updates)
          f.close()
          reload(mbal)
            
        #mbal.AdminList[1] = str(kdListSorted[0][2])
        #print mbal.AdminList

        #background
        self._backgroundLogo = bs.newNode('image', delegate=self, attrs={
                               'fillScreen':True,
                               'texture':bs.getTexture('menuBG'),
                               'tiltTranslate':-0.3,
                               'hasAlphaChannel':False,
                               'color':(1, 1, 1)})
        #top10score
        textTopScore = ScreenLanguage.top15scoreLang
        posTopScore = (180,210)
        scaleTopScore = 1.0
        colorTopScore = (1.0, 0.6, 0.8, 1)
        maxWidthTopScore = 300
        self.powerUpText(textTopScore,posTopScore,scaleTopScore,colorTopScore,maxWidthTopScore)

        #top10Fighter
        textTopFighter = ScreenLanguage.top15fighterLang
        posTopFighter = (-230,210)
        scaleTopFighter = 1.0
        colorTopFighter = (1.0, 0.6, 0.8, 1)
        maxWidthTopFighter = 300
        self.powerUpText(textTopFighter,posTopFighter,scaleTopFighter,colorTopFighter,maxWidthTopFighter)

        #top10scoreRanktext
        textTopScoreRank = ScreenLanguage.rankLang
        posTopScoreRank = (180,175)
        scaleTopScoreRank = 0.9
        colorTopScoreRank = (0.9, 0.8, 1, 1)
        maxWidthTopScoreRank = 300
        self.powerUpText(textTopScoreRank,posTopScoreRank,scaleTopScoreRank,colorTopScoreRank,maxWidthTopScoreRank)

        #top10ScoreAvgtext
        textTopScoreAVG = ScreenLanguage.avgPtsLang
        posTopScoreAVG = (490,175)
        scaleTopScoreAVG = 0.9
        colorTopScoreAVG = (0.9, 0.8, 1, 1)
        maxWidthTopScoreAVG = 300
        self.powerUpText(textTopScoreAVG,posTopScoreAVG,scaleTopScoreAVG,colorTopScoreAVG,maxWidthTopScoreAVG)

        #top10FighterRanktext
        textTopFighterRank = ScreenLanguage.rankLang
        posTopFighterRank = (-230,175)
        scaleTopFighterRank = 0.9
        colorTopFighterRank = (0.9, 0.8, 1, 1)
        maxWidthTopFighterRank = 300
        self.powerUpText(textTopFighterRank,posTopFighterRank,scaleTopFighterRank,colorTopFighterRank,maxWidthTopFighterRank)

        #top10FighterKDtext
        textTopFighterKD = ScreenLanguage.kdLang
        posTopFighterKD = (90,175)
        scaleTopFighterKD = 0.9
        colorTopFighterKD = (0.9, 0.8, 1, 1)
        maxWidthTopFighterKD = 300
        self.powerUpText(textTopFighterKD,posTopFighterKD,scaleTopFighterKD,colorTopFighterKD,maxWidthTopFighterKD)
        
        
        #rank fighter
        fighterRank1 = bs.getSpecialChar('trophy4')+'1. ' + (kdListSorted[0][0] if len(kdListSorted) > 0 else '--')
        fighterRank2 = bs.getSpecialChar('trophy3')+'2. ' + (kdListSorted[1][0] if len(kdListSorted) > 1 else '--')
        fighterRank3 = bs.getSpecialChar('trophy3')+'3. ' + (kdListSorted[2][0] if len(kdListSorted) > 2 else '--')
        fighterRank4 = bs.getSpecialChar('trophy2')+'4. ' + (kdListSorted[3][0] if len(kdListSorted) > 3 else '--')
        fighterRank5 = bs.getSpecialChar('trophy2')+'5. ' + (kdListSorted[4][0] if len(kdListSorted) > 4 else '--')
        fighterRank6 = bs.getSpecialChar('trophy2')+'6. ' + (kdListSorted[5][0] if len(kdListSorted) > 5 else '--')
        fighterRank7 = bs.getSpecialChar('trophy2')+'7. ' + (kdListSorted[6][0] if len(kdListSorted) > 6 else '--')
        fighterRank8 = bs.getSpecialChar('trophy2')+'8. ' + (kdListSorted[7][0] if len(kdListSorted) > 7 else '--')
        fighterRank9 = bs.getSpecialChar('trophy2')+'9. ' + (kdListSorted[8][0] if len(kdListSorted) > 8 else '--')
        fighterRank10 = bs.getSpecialChar('trophy2')+'10. ' + (kdListSorted[9][0] if len(kdListSorted) > 9 else '--')
        fighterRank11 = bs.getSpecialChar('trophy2')+'11. ' + (kdListSorted[10][0] if len(kdListSorted) > 10 else '--')
        fighterRank12 = bs.getSpecialChar('trophy2')+'12. ' + (kdListSorted[11][0] if len(kdListSorted) > 11 else '--')
        fighterRank13 = bs.getSpecialChar('trophy2')+'13. ' + (kdListSorted[12][0] if len(kdListSorted) > 12 else '--')
        fighterRank14 = bs.getSpecialChar('trophy2')+'14. ' + (kdListSorted[13][0] if len(kdListSorted) > 13 else '--')
        fighterRank15 = bs.getSpecialChar('trophy2')+'15. ' + (kdListSorted[14][0] if len(kdListSorted) > 14 else '--')
        
        #K/D ratio
        fighterKD1 = str("{0:.2f}".format(kdListSorted[0][1]) if len(kdListSorted) > 0 else '--')
        fighterKD2 = str("{0:.2f}".format(kdListSorted[1][1]) if len(kdListSorted) > 1 else '--')
        fighterKD3 = str("{0:.2f}".format(kdListSorted[2][1]) if len(kdListSorted) > 2 else '--')
        fighterKD4 = str("{0:.2f}".format(kdListSorted[3][1]) if len(kdListSorted) > 3 else '--')
        fighterKD5 = str("{0:.2f}".format(kdListSorted[4][1]) if len(kdListSorted) > 4 else '--')
        fighterKD6 = str("{0:.2f}".format(kdListSorted[5][1]) if len(kdListSorted) > 5 else '--')
        fighterKD7 = str("{0:.2f}".format(kdListSorted[6][1]) if len(kdListSorted) > 6 else '--')
        fighterKD8 = str("{0:.2f}".format(kdListSorted[7][1]) if len(kdListSorted) > 7 else '--')
        fighterKD9 = str("{0:.2f}".format(kdListSorted[8][1]) if len(kdListSorted) > 8 else '--')
        fighterKD10 = str("{0:.2f}".format(kdListSorted[9][1]) if len(kdListSorted) > 9 else '--')
        fighterKD11 = str("{0:.2f}".format(kdListSorted[10][1]) if len(kdListSorted) > 10 else '--')
        fighterKD12 = str("{0:.2f}".format(kdListSorted[11][1]) if len(kdListSorted) > 11 else '--')
        fighterKD13 = str("{0:.2f}".format(kdListSorted[12][1]) if len(kdListSorted) > 12 else '--')
        fighterKD14 = str("{0:.2f}".format(kdListSorted[13][1]) if len(kdListSorted) > 13 else '--')
        fighterKD15 = str("{0:.2f}".format(kdListSorted[14][1]) if len(kdListSorted) > 14 else '--')
        
        #rank score
        scoreRank1 = bs.getSpecialChar('trophy4')+'1. ' + (scoreListSorted[0][0] if len(scoreListSorted) > 0 else '--')
        scoreRank2 = bs.getSpecialChar('trophy3')+'2. ' + (scoreListSorted[1][0] if len(scoreListSorted) > 1 else '--')
        scoreRank3 = bs.getSpecialChar('trophy3')+'3. ' + (scoreListSorted[2][0] if len(scoreListSorted) > 2 else '--')
        scoreRank4 = bs.getSpecialChar('trophy2')+'4. ' + (scoreListSorted[3][0] if len(scoreListSorted) > 3 else '--')
        scoreRank5 = bs.getSpecialChar('trophy2')+'5. ' + (scoreListSorted[4][0] if len(scoreListSorted) > 4 else '--')
        scoreRank6 = bs.getSpecialChar('trophy2')+'6. ' + (scoreListSorted[5][0] if len(scoreListSorted) > 5 else '--')
        scoreRank7 = bs.getSpecialChar('trophy2')+'7. ' + (scoreListSorted[6][0] if len(scoreListSorted) > 6 else '--')
        scoreRank8 = bs.getSpecialChar('trophy2')+'8. ' + (scoreListSorted[7][0] if len(scoreListSorted) > 7 else '--')
        scoreRank9 = bs.getSpecialChar('trophy2')+'9. ' + (scoreListSorted[8][0] if len(scoreListSorted) > 8 else '--')
        scoreRank10 = bs.getSpecialChar('trophy2')+'10. ' + (scoreListSorted[9][0] if len(scoreListSorted) > 9 else '--')
        scoreRank11 = bs.getSpecialChar('trophy2')+'11. ' + (scoreListSorted[10][0] if len(scoreListSorted) > 10 else '--')
        scoreRank12 = bs.getSpecialChar('trophy2')+'12. ' + (scoreListSorted[11][0] if len(scoreListSorted) > 11 else '--')
        scoreRank13 = bs.getSpecialChar('trophy2')+'13. ' + (scoreListSorted[12][0] if len(scoreListSorted) > 12 else '--')
        scoreRank14 = bs.getSpecialChar('trophy2')+'14. ' + (scoreListSorted[13][0] if len(scoreListSorted) > 13 else '--')
        scoreRank15 = bs.getSpecialChar('trophy2')+'15. ' + (scoreListSorted[14][0] if len(scoreListSorted) > 14 else '--')
        
        #AVG score
        AVGscore1 = str("{0:.1f}".format(scoreListSorted[0][1]) if len(scoreListSorted) > 0 else '--')
        AVGscore2 = str("{0:.1f}".format(scoreListSorted[1][1]) if len(scoreListSorted) > 1 else '--')
        AVGscore3 = str("{0:.1f}".format(scoreListSorted[2][1]) if len(scoreListSorted) > 2 else '--')
        AVGscore4 = str("{0:.1f}".format(scoreListSorted[3][1]) if len(scoreListSorted) > 3 else '--')
        AVGscore5 = str("{0:.1f}".format(scoreListSorted[4][1]) if len(scoreListSorted) > 4 else '--')
        AVGscore6 = str("{0:.1f}".format(scoreListSorted[5][1]) if len(scoreListSorted) > 5 else '--')
        AVGscore7 = str("{0:.1f}".format(scoreListSorted[6][1]) if len(scoreListSorted) > 6 else '--')
        AVGscore8 = str("{0:.1f}".format(scoreListSorted[7][1]) if len(scoreListSorted) > 7 else '--')
        AVGscore9 = str("{0:.1f}".format(scoreListSorted[8][1]) if len(scoreListSorted) > 8 else '--')
        AVGscore10 = str("{0:.1f}".format(scoreListSorted[9][1]) if len(scoreListSorted) > 9 else '--')
        AVGscore11 = str("{0:.1f}".format(scoreListSorted[10][1]) if len(scoreListSorted) > 10 else '--')
        AVGscore12 = str("{0:.1f}".format(scoreListSorted[11][1]) if len(scoreListSorted) > 11 else '--')
        AVGscore13 = str("{0:.1f}".format(scoreListSorted[12][1]) if len(scoreListSorted) > 12 else '--')
        AVGscore14 = str("{0:.1f}".format(scoreListSorted[13][1]) if len(scoreListSorted) > 13 else '--')
        AVGscore15 = str("{0:.1f}".format(scoreListSorted[14][1]) if len(scoreListSorted) > 14 else '--')
        
        #fighter
        fighterPos1 = (-230,130)
        fighterPos2 = (-230,100)
        fighterPos3 = (-230,70)
        fighterPos4 = (-230,40)
        fighterPos5 = (-230,10)
        fighterPos6 = (-230,-20)
        fighterPos7 = (-230,-50)
        fighterPos8 = (-230,-80)
        fighterPos9 = (-230,-110)
        fighterPos10 = (-230,-140)
        fighterPos11 = (-230,-170)
        fighterPos12 = (-230,-200)
        fighterPos13 = (-230,-230)
        fighterPos14 = (-230,-260)
        fighterPos15 = (-230,-290)
        
        #KD
        KDpos1 = (90,130)
        KDpos2 = (90,100)
        KDpos3 = (90,70)
        KDpos4 = (90,40)
        KDpos5 = (90,10)
        KDpos6 = (90,-20)
        KDpos7 = (90,-50)
        KDpos8 = (90,-80)
        KDpos9 = (90,-110)
        KDpos10 = (90,-140)
        KDpos11 = (90,-170)
        KDpos12 = (90,-200)
        KDpos13 = (90,-230)
        KDpos14 = (90,-260)
        KDpos15 = (90,-290)
        
        
        #score
        scorePos1 = (180,130)
        scorePos2 = (180,100)
        scorePos3 = (180,70)
        scorePos4 = (180,40)
        scorePos5 = (180,10)
        scorePos6 = (180,-20)
        scorePos7 = (180,-50)
        scorePos8 = (180,-80)
        scorePos9 = (180,-110)
        scorePos10 = (180,-140)
        scorePos11 = (180,-170)
        scorePos12 = (180,-200)
        scorePos13 = (180,-230)
        scorePos14 = (180,-260)
        scorePos15 = (180,-290)
        
        #AVGpos
        AVGpos1 = (490,130)
        AVGpos2 = (490,100)
        AVGpos3 = (490,70)
        AVGpos4 = (490,40)
        AVGpos5 = (490,10)
        AVGpos6 = (490,-20)
        AVGpos7 = (490,-50)
        AVGpos8 = (490,-80)
        AVGpos9 = (490,-110)
        AVGpos10 = (490,-140)
        AVGpos11 = (490,-170)
        AVGpos12 = (490,-200)
        AVGpos13 = (490,-230)
        AVGpos14 = (490,-260)
        AVGpos15 = (490,-290)
        
        #call fighters list
        self.ranklists(fighterRank1,fighterPos1)
        self.ranklists(fighterRank2,fighterPos2)
        self.ranklists(fighterRank3,fighterPos3)
        self.ranklists(fighterRank4,fighterPos4)
        self.ranklists(fighterRank5,fighterPos5)
        self.ranklists(fighterRank6,fighterPos6)
        self.ranklists(fighterRank7,fighterPos7)
        self.ranklists(fighterRank8,fighterPos8)
        self.ranklists(fighterRank9,fighterPos9)
        self.ranklists(fighterRank10,fighterPos10)
        self.ranklists(fighterRank11,fighterPos11)
        self.ranklists(fighterRank12,fighterPos12)
        self.ranklists(fighterRank13,fighterPos13)
        self.ranklists(fighterRank14,fighterPos14)
        self.ranklists(fighterRank15,fighterPos15)
        
        #call KD list
        self.ranklists(fighterKD1,KDpos1)
        self.ranklists(fighterKD2,KDpos2)
        self.ranklists(fighterKD3,KDpos3)
        self.ranklists(fighterKD4,KDpos4)
        self.ranklists(fighterKD5,KDpos5)
        self.ranklists(fighterKD6,KDpos6)
        self.ranklists(fighterKD7,KDpos7)
        self.ranklists(fighterKD8,KDpos8)
        self.ranklists(fighterKD9,KDpos9)
        self.ranklists(fighterKD10,KDpos10)
        self.ranklists(fighterKD11,KDpos11)
        self.ranklists(fighterKD12,KDpos12)
        self.ranklists(fighterKD13,KDpos13)
        self.ranklists(fighterKD14,KDpos14)
        self.ranklists(fighterKD15,KDpos15)
              
        
        #call score list
        self.ranklists(scoreRank1,scorePos1)
        self.ranklists(scoreRank2,scorePos2)
        self.ranklists(scoreRank3,scorePos3)
        self.ranklists(scoreRank4,scorePos4)
        self.ranklists(scoreRank5,scorePos5)
        self.ranklists(scoreRank6,scorePos6)
        self.ranklists(scoreRank7,scorePos7)
        self.ranklists(scoreRank8,scorePos8)
        self.ranklists(scoreRank9,scorePos9)
        self.ranklists(scoreRank10,scorePos10)
        self.ranklists(scoreRank11,scorePos11)
        self.ranklists(scoreRank12,scorePos12)
        self.ranklists(scoreRank13,scorePos13)
        self.ranklists(scoreRank14,scorePos14)
        self.ranklists(scoreRank15,scorePos15)
        
        #call AVGscore List
        self.ranklists(AVGscore1,AVGpos1)
        self.ranklists(AVGscore2,AVGpos2)
        self.ranklists(AVGscore3,AVGpos3)
        self.ranklists(AVGscore4,AVGpos4)
        self.ranklists(AVGscore5,AVGpos5)
        self.ranklists(AVGscore6,AVGpos6)
        self.ranklists(AVGscore7,AVGpos7)
        self.ranklists(AVGscore8,AVGpos8)
        self.ranklists(AVGscore9,AVGpos9)
        self.ranklists(AVGscore10,AVGpos10)
        self.ranklists(AVGscore11,AVGpos11)
        self.ranklists(AVGscore12,AVGpos12)
        self.ranklists(AVGscore13,AVGpos13)
        self.ranklists(AVGscore14,AVGpos14)
        self.ranklists(AVGscore15,AVGpos15)
  
        
        #dönenler
        self.starlogo = bs.newNode('image', delegate=self, attrs={
                               'texture':bs.getTexture('achievementOutline'), ##storeCharacter frameInset logo
                               'position': (470,280),   #(300,90)
                               'scale':(100,100),
                               'tiltTranslate':0,
                               'hasAlphaChannel':True,
                               'opacity':1.0,
                               'color':(1, 1, 0)})    
        bsUtils.animate(self.starlogo, 'rotate', {0: 0.0, 350: 360.0}, loop=True)
        
        #dönenler
        self.starlogo2 = bs.newNode('image', delegate=self, attrs={
                               'texture':bs.getTexture('achievementOutline'),
                               'position': (-470,280),
                               'scale':(100,100),
                               'tiltTranslate':0,
                               'hasAlphaChannel':True,
                               'opacity':1.0,
                               'color':(1, 1, 0)})
        bsUtils.animate(self.starlogo2, 'rotate', {0: 0.0, 350: -360.0}, loop=True)                     
        
        
        #speed image
        imageTextSpeed = bs.getTexture('powerupSpeed')
        imagePosSpeed = (-560,145)
        imageColorSpeed = (1, 1, 1)
        imageAlphaSpeed = True
        self.powerUpImage(imageTextSpeed,imagePosSpeed,imageColorSpeed,imageAlphaSpeed)
                              
        #superStar image
        imageTextSuperStar = bs.getTexture('levelIcon')
        imagePosSuperStar = (-560,45)
        imageColorSuperStar = (1, 1, 1)
        imageAlphaSuperStar = True
        self.powerUpImage(imageTextSuperStar,imagePosSuperStar,imageColorSuperStar,imageAlphaSuperStar)
                               
        #iceCube image
        imageTextIceCube = bs.getTexture('softRect')
        imagePosIceCube = (-560,-50)
        imageColorIceCube = (0.9, 0.9, 1)
        imageAlphaIceCube = True
        self.powerUpImage(imageTextIceCube,imagePosIceCube,imageColorIceCube,imageAlphaIceCube)
                               
        #surprise image
        imageTextSurprise = bs.getTexture('powerupHealth')
        imagePosSurprise = (-560,-150)
        imageColorSurprise = (1, 1, 1)
        imageAlphaSurprise = True
        self.powerUpImage(imageTextSurprise,imagePosSurprise,imageColorSurprise,imageAlphaSurprise)
        
        #martyrdom image
        imageTextMarty = bs.getTexture('achievementCrossHair')
        imagePosMarty = (-560,-255)
        imageColorMarty = (1, 1, 1)
        imageAlphaMarty = True
        self.powerUpImage(imageTextMarty,imagePosMarty,imageColorMarty,imageAlphaMarty)
        
        #custom Powerups
        #bsUtils.animate(self.customPowerUps, 'scale', {0: 1,120: 1,120: 1,120: 0.99},loop=True)
        textPowerUp = ScreenLanguage.customLang
        posPowerUp = (-560,210)
        scalePowerUp = 1.0
        colorPowerUp = (1.0, 0.6, 0.8, 1)
        maxWidthPowerUp = 180
        self.powerUpText(textPowerUp,posPowerUp,scalePowerUp,colorPowerUp,maxWidthPowerUp)
        
        #info for players
        textTyFor = ScreenLanguage.infoLang
        posTyFor = (0,-320)
        scaleTyFor = 1.0
        colorTyFor = (1.0, 0.6, 0.8, 1)
        maxWidthTyFor = 300
        self.powerUpText(textTyFor,posTyFor,scaleTyFor,colorTyFor,maxWidthTyFor)

        #speed
        textSpeedInfo = ScreenLanguage.speedInfoLang
        posSpeedInfo = (-500,135)
        scaleSpeedInfo = 0.8
        colorSpeedInfo = (0.9, 0.9, 0.9, 1)
        maxWidthSpeedInfo = 250
        textSpeed = ScreenLanguage.speedTextLang
        posSpeed = (-500,170)
        scaleSpeed = 0.7
        colorSpeed = (0.9, 0.8, 1, 1)
        maxWidthSpeed = 180
        self.powerUpText(textSpeed,posSpeed,scaleSpeed,colorSpeed,maxWidthSpeed)
        self.powerUpText(textSpeedInfo,posSpeedInfo,scaleSpeedInfo,colorSpeedInfo,maxWidthSpeedInfo)
        
        #superStar
        textSuperStarInfo = ScreenLanguage.superStarInfoLang
        posSuperStarInfo = (-500,35)
        scaleSuperStarInfo = 0.8
        colorSuperStarInfo = (0.9, 0.9, 0.9, 1)
        maxWidthSuperStarInfo = 250
        textSuperStar = ScreenLanguage.superStarTextLang
        posSuperStar = (-500,70)
        scaleSuperStar = 0.7
        colorSuperStar = (0.9, 0.8, 1, 1)
        maxWidthSuperStar = 180
        self.powerUpText(textSuperStar,posSuperStar,scaleSuperStar,colorSuperStar,maxWidthSuperStar)
        self.powerUpText(textSuperStarInfo,posSuperStarInfo,scaleSuperStarInfo,colorSuperStarInfo,maxWidthSuperStarInfo)
        
        #iceCube
        textIceCubeInfo = ScreenLanguage.iceCubeInfoLang
        posIceCubeInfo = (-500,-63)
        scaleIceCubeInfo = 0.8
        colorIceCubeInfo = (0.9, 0.9, 0.9, 1)
        maxWidthIceCubeInfo = 250
        textIceCube = ScreenLanguage.iceCubeTextLang
        posIceCube = (-500,-23)
        scaleIceCube = 0.7
        colorIceCube = (0.9, 0.8, 1, 1)
        maxWidthIceCube = 180
        self.powerUpText(textIceCube,posIceCube,scaleIceCube,colorIceCube,maxWidthIceCube)
        self.powerUpText(textIceCubeInfo,posIceCubeInfo,scaleIceCubeInfo,colorIceCubeInfo,maxWidthIceCubeInfo)
        
        #surprise
        textSurpriseInfo = ScreenLanguage.surpriseInfoLang
        posSurpriseInfo = (-500,-165)
        scaleSurpriseInfo = 0.75
        colorSurpriseInfo = (0.9, 0.9, 0.9, 1)
        maxWidthSurpriseInfo = 250
        textSurprise = ScreenLanguage.surpriseTextLang
        posSurprise = (-500,-115)
        scaleSurprise = 0.7
        colorSurprise = (0.9, 0.8, 1, 1)
        maxWidthSurprise = 180
        self.powerUpText(textSurprise,posSurprise,scaleSurprise,colorSurprise,maxWidthSurprise)
        self.powerUpText(textSurpriseInfo,posSurpriseInfo,scaleSurpriseInfo,colorSurpriseInfo,maxWidthSurpriseInfo)
        
        #martyrdom
        textMartyInfo = ScreenLanguage.martyInfoLang
        posMartyInfo = (-500,-270)
        scaleMartyInfo = 0.75
        colorMartyInfo = (0.9, 0.9, 0.9, 1)
        maxWidthMartyInfo = 250
        textMarty = ScreenLanguage.martyTextLang
        posMarty = (-500,-220)
        scaleMarty = 0.7
        colorMarty= (0.9, 0.8, 1, 1)
        maxWidthMarty = 180
        self.powerUpText(textMarty,posMarty,scaleMarty,colorMarty,maxWidthMarty)
        self.powerUpText(textMartyInfo,posMartyInfo,scaleMartyInfo,colorMartyInfo,maxWidthMartyInfo)
                       
        self._sound = bs.newNode('sound',attrs={'sound':bs.getSound('victoryMusic'),'volume':1.0})             
        self._endGameTimer = bs.Timer(17000,bs.WeakCall(self.endGame))
        #bsUtils.ZoomText('MYTHB', lifespan=22000, jitter=2.0,
                         #position=(100,120), scale=0.6, maxWidth=800,
                         #trail=True, color=(0.5,0.5,1)).autoRetain()
        bsUtils.ZoomText(ScreenLanguage.welcomeTextLang, lifespan=999000, jitter=2.0,
                         position=(0,270), scale=1.1, maxWidth=800,
                         trail=False, color=(0.6,0.6,1)).autoRetain()
    
    def powerUpText(self,text,pos,scale,color,maxWidth):
        powerText = bs.newNode('text', attrs={
                       'text':text,
                       'position':pos,
                       'hAlign':'left',
                       'vAlign':'center',
                       'maxWidth':maxWidth,
                       'flatness':1.0,
                       'shadow':1.0,
                       'color':color,
                       'scale':scale})
    
    def powerUpImage(self,image,pos,color,alpha):
        powerimage = bs.newNode('image', delegate=self, attrs={
                               'texture':image,
                               'position':pos,
                               'scale':(80,80),
                               'tiltTranslate':0,
                               'hasAlphaChannel':alpha,
                               #'opacity':0.5,
                               'color':color})
        bsUtils.animateArray(powerimage, 'scale', 1, {2:(80,80), 550:(75, 75),1100:(80,80)},loop=True)
    
    def ranklists(self,text,pos):
        #if fighterRank1 pos 0 100 # so -30 for every value 
        
        rankText = bsUtils.Text(text,
                               position=pos,
                               hAlign='left', vAlign='center', maxWidth=300,scale=1.0,
                               color=(0.9, 0.9, 0.9, 1),shadow=1.0,flatness=1.0,
                               transition='inLeft', transitionDelay=500).autoRetain()
        
    def spawnPlayer(self,player):
        return
    
    
    def endGame(self):
        #bsInternal._fadeScreen(False, time=500)
        bs.screenMessage('GAME STARTING...',color = (0,0.9,0))
        ourResults = bs.TeamGameResults()
        for team in self.teams: ourResults.setTeamScore(team,0)
        self.end(results=ourResults)
