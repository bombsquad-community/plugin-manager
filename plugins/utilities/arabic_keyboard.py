# ba_meta require api 9

import bauiv1

# Full Arabic characters (real Arabic keyboard layout simulation)
arabic_chars = [
    list('ضصثقفغعهخحج'),       # Row 1: QWERTY top
    list('شسيبلاتنمكط'),       # Row 2: QWERTY middle
    list('ئءؤرلاىةوزظ'),       # Row 3: QWERTY bottom (with 'لا' and more)
]

# Fill each row to exactly 10 characters
for row in arabic_chars:
    while len(row) < 10:
        row.append('‎')  # Invisible char

# Arabic numerals and essential symbols
arabic_nums = list('١٢٣٤٥٦٧٨٩٠') + list('؟،؛ـ“”أإآًٍُِّْ')[:16]
while len(arabic_nums) < 26:
    arabic_nums.append('‎')

# ba_meta export bauiv1.Keyboard


class ArabicKeyboard(bauiv1.Keyboard):
    """Arabic Keyboard by \ue048Freaku"""
    name = 'Arabic Keyboard by yANES'
    chars = arabic_chars
    nums = arabic_nums
    pages = {
        'symbols': tuple('!@#$%^&*()-_=+[{]}\\|;:\'",<.>/?')[:26]
    }
