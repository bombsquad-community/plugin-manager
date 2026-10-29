# coding=utf-8
import os
import bs
import shutil
import hashlib

NEW_CHARACTER_DIRECTORY = 'IronSpiderMan'  # The directory contains which were described in README
NEW_CHARACTER_NAME = u'Iron Spider'  # ensure unicode
SUPPORTED_PLATFORMS = ['android', 'other']  # other means Win, Linux, Mac as they all use .dds


### YOU DONNOT HAVE TO EDIT ANYTHING BELOW ###

class InstallerLanguageEnglish(object):
    installing = u'Installing character [%s]...'
    success = u'Character [%s] installation succeeded!'
    fail = u'Character [%s] installation failed'
    notSupported = u'Character [%s] is not supported on %s'


class InstallerLanguageChinese(object):
    installing = u'正在安装地图[%s], 请稍候...'
    success = u'地图[%s]安装完成！'
    fail = u'地图[%s]安装失败'
    notSupported = u'地图[%s]不支持%s平台！'

	
class InstallerLanguageSpanish(object):
    installing = u'Instalando Personaje [%s]...'
    success = u'Personaje [%s] instalación finalizada!'
    fail = u'Personaje [%s] instalación fallida'
    notSupported = u'Personaje [%s] no soportada en %s'
	
InstallerLanguage = InstallerLanguageEnglish
if bs.getLanguage() == 'Chinese':
    InstallerLanguage = InstallerLanguageChinese
if bs.getLanguage() == 'Spanish':
    InstallerLanguage = InstallerLanguageSpanish


class NewCharacterInstaller(object):
    characterName = NEW_CHARACTER_NAME
    copyDir = NEW_CHARACTER_DIRECTORY
    supportedPlatforms = SUPPORTED_PLATFORMS

    def __init__(self):
        self.characterFilesDir = bs.getEnvironment()['userScriptsDirectory'] + '/' + self.copyDir + '/'
        self.scriptsDir = bs.getEnvironment()['systemScriptsDirectory'] + '/'
        self.dataDir = self.scriptsDir + '../'
        self.modelsDir = self.dataDir + 'models/'
        self.audioDir = self.dataDir + 'audio/'
        self.texturesDir = self.dataDir + 'textures/'

        self.platform = bs.getEnvironment()['platform']
        self.models = []
        self.textures = []
        self.audio = []
        self.searchFiles()

    def searchFiles(self):
        root, dirs, files = os.walk(self.characterFilesDir).next()
        for fn in files:
            if fn.endswith('.ktx') or fn.endswith('.dds'):
                self.textures.append(fn)
            if fn.endswith('.bob') or fn.endswith('.cob'):
                self.models.append(fn)
            if fn.endswith('.ogg'):
                self.audio.append(fn)

        initFile = self.characterFilesDir + '__init__.py'
        if not os.path.isfile(initFile):
            f = open(initFile, 'w')
            f.close()

    @staticmethod
    def checkFileSame(f1, f2):
        try:
            md5s = [hashlib.md5(), hashlib.md5()]
            fs = [f1, f2]
            for i in range(2):
                f = open(fs[i], 'rb')
                block_size = 2 ** 20
                while True:
                    data = f.read(block_size)
                    if not data: break
                    md5s[i].update(data)
                f.close()
                md5s[i] = md5s[i].hexdigest()
            return md5s[0] == md5s[1]
        except Exception, e:
            return False

    def checkInstalled(self):
        installed = True
        for model in self.models:
            systemModel = self.modelsDir + model
            modModel = self.characterFilesDir + model
            if not os.path.isfile(systemModel):
                installed = False
                break
            if not self.checkFileSame(systemModel, modModel):
                installed = False
                break

        for texture in self.textures:
            if self.platform == 'android':
                if texture.endswith('.dds'):
                    continue
            else:
                if texture.endswith('.ktx'):
                    continue
            systemTexture = self.texturesDir + texture
            modTexture = self.characterFilesDir + texture
            if not os.path.isfile(systemTexture):
                installed = False
                break
            if not self.checkFileSame(systemTexture, modTexture):
                installed = False
                break

        for au in self.audio:
            systemAudio = self.audioDir + au
            modAudio = self.characterFilesDir + au
            if not os.path.exists(systemAudio):
                installed = False
                break
            if not self.checkFileSame(systemAudio, modAudio):
                installed = False
                break

        return installed

    def checkSupported(self):
        if self.platform == 'android':
            if 'android' in self.supportedPlatforms:
                return True
        else:
            if 'other' in self.supportedPlatforms:
                return True
        return False

    def install(self):
        if not self.checkSupported():
            bs.screenMessage(InstallerLanguage.notSupported % (self.characterName, self.platform))
            return

        if self.checkInstalled():
            exec 'import ' + NEW_CHARACTER_DIRECTORY + '.bsNewCharacter'
            return

        bs.screenMessage(InstallerLanguage.installing % self.characterName)

        try:
            for model in self.models:
                systemModel = self.modelsDir + model
                modModel = self.characterFilesDir + model
                shutil.copy(modModel, systemModel)

            for texture in self.textures:
                if self.platform == 'android':
                    if texture.endswith('.dds'):
                        continue
                else:
                    if texture.endswith('.ktx'):
                        continue
                systemTex = self.texturesDir + texture
                modTex = self.characterFilesDir + texture
                shutil.copy(modTex, systemTex)

            for au in self.audio:
                systemAudio = self.audioDir + au
                modAudio = self.characterFilesDir + au
                shutil.copy(modAudio, systemAudio)

            bs.screenMessage(InstallerLanguage.success % self.characterName, color=(0, 1, 0))

            bs.reloadMedia()
            exec 'import ' + NEW_CHARACTER_DIRECTORY + '.bsNewCharacter'
        except IOError, e:
            bs.screenMessage(InstallerLanguage.fail % self.characterName, color=(1, 0, 0))
            bs.screenMessage(str(e), color=(1, 0, 0))
            print e


NewCharacterInstaller().install()
