# Made by your friend: Freaku

# Translate function through google webpage by: OnurV2 (from their BombsquadDetails.py mod)
# Github: https://github.com/OnurV2
# YT: https://m.youtube.com/@OnurV2


import babase
import bauiv1 as bui
from bauiv1lib.popup import PopupMenu
import bauiv1lib.party
import urllib.parse
import urllib.request
import threading
import random

__version__ = "1.1.4"
__author__ = "Freaku"

plugman = dict(
    description="Translate yours/others chat. Just click on the message to translate them. Open Plugin Settings/Double click 'Trans' button to open translation settings. Compatible with other PW mods (like advanced_party_window)",
    external_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    authors=[
        {"name": __author__, "email": "", "discord": "freakyyyy"}
    ],
    version=__version__,
)

show_translate_result = True
config = babase.app.config

# Convert Ballistica Locale -> this mod's language name.
def get_default_translate_language():
    locale = babase.app.locale.default_locale

    # Ballistica 1.7.40 Locale objects have a .value such as 'eng'.
    locale_value = getattr(locale, 'value', str(locale))

    locale_map = {
        'eng': 'English',
        'ara': 'Arabic',
        'zho': 'Chinese (simplified)',
        'hrv': 'Croatian',
        'ces': 'Czech',
        'dan': 'Danish',
        'nld': 'Dutch',
        'fin': 'Finnish',
        'fra': 'French',
        'deu': 'German',
        'ell': 'Greek',
        'hin': 'Hindi',
        'hun': 'Hungarian',
        'ind': 'Indonesian',
        'ita': 'Italian',
        'jpn': 'Japanese',
        'kor': 'Korean',
        'msa': 'Malay',
        'mal': 'Malayalam',
        'mar': 'Marathi',
        'fas': 'Persian',
        'pol': 'Polish',
        'por': 'Portuguese',
        'ron': 'Romanian',
        'rus': 'Russian',
        'srp': 'Serbian',
        'slk': 'Slovak',
        'spa': 'Spanish',
        'swe': 'Swedish',
        'tam': 'Tamil',
        'tel': 'Telugu',
        'tha': 'Thai',
        'tur': 'Turkish',
        'ukr': 'Ukrainian',
        'vie': 'Vietnamese',
        'tgl': 'Tagalog',
    }

    return locale_map.get(locale_value, 'English')


default_language = get_default_translate_language()

default_config = {
    'O Source Trans Lang': 'Auto Detect',
    'O Target Trans Lang': default_language,
    'Y Source Trans Lang': 'Auto Detect',
    'Y Target Trans Lang': default_language,
}

for key, value in default_config.items():
    if key not in config:
        config[key] = value

# Repair configs created with the old Locale-object behavior.
for key in ('O Target Trans Lang', 'Y Target Trans Lang'):
    if not isinstance(config[key], str):
        config[key] = default_language



# Language names -> Google Translate language codes.
translate_languages = {
    'Auto Detect': 'auto',
    'Arabic': 'ar',
    'Chinese (simplified)': 'zh-CN',
    'Chinese (traditional)': 'zh-TW',
    'Croatian': 'hr',
    'Czech': 'cs',
    'Danish': 'da',
    'Dutch': 'nl',
    'English': 'en',
    'Esperanto': 'eo',
    'Finnish': 'fi',
    'Tagalog': 'tl',
    'French': 'fr',
    'German': 'de',
    'Greek': 'el',
    'Hindi': 'hi',
    'Hungarian': 'hu',
    'Indonesian': 'id',
    'Italian': 'it',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Malay': 'ms',
    'Malayalam': 'ml',
    'Marathi': 'mr',
    'Persian': 'fa',
    'Polish': 'pl',
    'Portuguese': 'pt',
    'Romanian': 'ro',
    'Russian': 'ru',
    'Serbian': 'sr',
    'Slovak': 'sk',
    'Spanish': 'es',
    'Swedish': 'sv',
    'Tamil': 'ta',
    'Telugu': 'te',
    'Thai': 'th',
    'Turkish': 'tr',
    'Ukrainian': 'uk',
    'Vietnamese': 'vi',
}

available_translate_languages = list(translate_languages.keys())
available_translate_languages.sort()

available_translate_languages.remove('Auto Detect')
available_translate_languages.insert(0, 'Auto Detect')



def translate(text, _callback, source='auto', target='en'):
    try:
        text = urllib.parse.quote(text)
        url = f'https://translate.google.com/m?tl={target}&sl={source}&q={text}'
        request = urllib.request.Request(url)
        data = urllib.request.urlopen(request).read().decode('utf-8')
        result = data[(data.find('"result-container">'))+len('"result-container">')
                       :data.find('</div><div class="links-container">')]
        replace_list = [('&#39;', '\''), ('&quot;', '"'), ('&amp;', '&')]
        for i in replace_list:
            result = result.replace(i[0], i[1])
        if show_translate_result:
            bui.pushcall(bui.CallPartial(_callback, result), from_other_thread=True)
    except Exception:
        print('Translation failed. Please connect to the internet.')


class NewPW(bauiv1lib.party.PartyWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_msg_clicked = None
        self._last_time_pressed_msg = 0.0
        self._last_time_pressed_translate = 0.0
        self._double_press_interval = 0.3
        self._last_translate_widget = None
        bui.buttonwidget(
            parent=self._root_widget,
            size=(50, 35),
            label='Trans',
            button_type='square',
            autoselect=True,
            position=(self._width - 10, 35),
            on_activate_call=self._translate_your_chat
        )

    def _translate_your_chat(self):
        global show_translate_result
    
        if (
            babase.apptime() - self._last_time_pressed_translate
            < self._double_press_interval
            and self._last_translate_widget is self._text_field
        ):
            show_translate_result = False
            self._last_time_pressed_translate = 0.0
            self._last_translate_widget = None
            TranslateWindow()
            return

        show_translate_result = True
        self._last_time_pressed_translate = babase.apptime()
        self._last_translate_widget = self._text_field

        text = str(bui.textwidget(query=self._text_field))

        def _apply_translation(translated):
            if self._text_field.exists():
                bui.textwidget(
                    edit=self._text_field,
                    text=translated
                )

        threading.Thread(
            target=translate,
            args=(
                text,
                _apply_translation,
                translate_languages[config['Y Source Trans Lang']],
                translate_languages[config['Y Target Trans Lang']]
            ),
            daemon=True
        ).start()

    def _add_msg(self, msg: str):
        txt = bui.textwidget(
            parent=self._columnwidget,
            h_align='left',
            v_align='center',
            scale=0.55,
            size=(900, 13),
            text=msg,
            autoselect=True,
            maxwidth=self._scroll_width * 0.94,
            shadow=0.3,
            flatness=1.0,
            on_activate_call=bui.CallPartial(self._copy_msg, msg),
            selectable=True,
        )

        self._chat_texts.append(txt)
        while len(self._chat_texts) > 40:
            self._chat_texts.pop(0).delete()
        bui.containerwidget(edit=self._columnwidget, visible_child=txt)

        bui.textwidget(edit=txt,
                       on_activate_call=bui.CallPartial(self._translate_other, txt, msg),
                       click_activate=True)

    def _translate_other(self, txt, msg):
        global show_translate_result
    
        if (
            babase.apptime() - self._last_time_pressed_msg
            < self._double_press_interval
            and self._last_msg_clicked == txt
        ):
            show_translate_result = False
            self._last_time_pressed_msg = 0.0
            self._copy_msg(msg)
            return

        show_translate_result = True
        self._last_msg_clicked = txt
        self._last_time_pressed_msg = babase.apptime()

        nickname = ''
        split_msg = msg

        if len(msg.split(':')) > 1:
            nickname = msg.split(':')[0] + ': '
            split_msg = ':'.join(msg.split(':')[1:])[1:]
    
        def _apply_translation(translated):
            if txt.exists():
                bui.textwidget(
                    edit=txt,
                    text=nickname + translated
                )

        threading.Thread(
            target=translate,
            args=(
                split_msg,
                _apply_translation,
                translate_languages[config['O Source Trans Lang']],
                translate_languages[config['O Target Trans Lang']]
            ),
            daemon=True
        ).start()


class TranslateWindow:
    def __init__(self):
        self.tips = ['Double click \'Trans\' button to\nquickly open translation settings', 'Click others message to\ntranslate them',
                     'Double click message to copy them!', 'Close & reopen chat window\n to see original messages']
        self._uiscale = bui.app.ui_v1.uiscale

        self._root_widget = bui.containerwidget(parent=bui.get_special_widget('overlay_stack'),
                                                size=(450, 250),
                                                transition='in_scale',
                                                scale=(2 if self._uiscale is babase.UIScale.SMALL else
                                                       1.4 if self._uiscale is babase.UIScale.MEDIUM else 1.3),
                                                on_outside_click_call=babase.CallPartial(self._back, sound=True))

        self._tips_text = bui.textwidget(parent=self._root_widget,
                                         color=(0, 1, 1),
                                         h_align='center',
                                         v_align='center',
                                         text='Tips: '+random.choice(self.tips),
                                         position=(200, 188),
                                         maxwidth=250)

        self.other_chat = bui.textwidget(parent=self._root_widget,
                                         color=(1, 1, 1),
                                         h_align='left',
                                         v_align='center',
                                         text='Others chat:',
                                         position=(-10, 140),
                                         maxwidth=59)

        self.your_chat = bui.textwidget(parent=self._root_widget,
                                        color=(1, 1, 1),
                                        h_align='left',
                                        v_align='center',
                                        text='Your chat:',
                                        position=(-10, 55),
                                        maxwidth=59)

        self.other_chat_arrow = bui.textwidget(parent=self._root_widget,
                                               color=(1, 1, 1),
                                               h_align='center',
                                               v_align='center',
                                               text=babase.charstr(babase.SpecialChar.RIGHT_ARROW),
                                               position=(200, 140),
                                               maxwidth=59)

        self.your_chat_arrow = bui.textwidget(parent=self._root_widget,
                                              color=(1, 1, 1),
                                              h_align='center',
                                              v_align='center',
                                              text=babase.charstr(babase.SpecialChar.RIGHT_ARROW),
                                              position=(200, 55),
                                              maxwidth=59)

        self.other_source_button = PopupMenu(parent=self._root_widget,
                                             position=(54, 140),
                                             autoselect=False,
                                             on_value_change_call=babase.CallPartial(
                                                 self._set_translate_language, 'O Source Trans Lang'),
                                             choices=available_translate_languages,
                                             button_size=(150, 30),
                                             current_choice=config['O Source Trans Lang'])

        self.other_target_button = PopupMenu(parent=self._root_widget,
                                             position=(243, 140),
                                             autoselect=False,
                                             on_value_change_call=babase.CallPartial(
                                                 self._set_translate_language, 'O Target Trans Lang'),
                                             choices=available_translate_languages[1:],
                                             button_size=(150, 30),
                                             current_choice=config['O Target Trans Lang'])

        self.your_source_button = PopupMenu(parent=self._root_widget,
                                            position=(54, 55),
                                            autoselect=False,
                                            on_value_change_call=babase.CallPartial(
                                                self._set_translate_language, 'Y Source Trans Lang'),
                                            choices=available_translate_languages,
                                            button_size=(150, 30),
                                            current_choice=config['Y Source Trans Lang'])

        self.your_target_button = PopupMenu(parent=self._root_widget,
                                            position=(243, 55),
                                            autoselect=False,
                                            on_value_change_call=babase.CallPartial(
                                                self._set_translate_language, 'Y Target Trans Lang'),
                                            choices=available_translate_languages[1:],
                                            button_size=(150, 30),
                                            current_choice=config['Y Target Trans Lang'])

    def _set_translate_language(self, lang, choice):
        config[lang] = choice
        config.commit()

    def _back(self, sound=False):
        self.other_source_button = None
        self.other_target_button = None
        self.your_source_button = None
        self.your_target_button = None
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
        if sound:
            bui.getsound('swish').play()


# ba_meta require api 9
# ba_meta export babase.Plugin
class byFreaku(babase.Plugin):
    def __init__(self):
        bauiv1lib.party.PartyWindow = NewPW

    def has_settings_ui(self):
        return True

    def show_settings_ui(self, source_widget):
        TranslateWindow()