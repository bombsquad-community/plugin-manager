import sys
import os
import json


def try_insert(expath: str | None = None):
    if expath:
        sys.path.insert(0, expath)
    try:
        from bsLanguageTest import values
        return values
    except ModuleNotFoundError:
        if expath in sys.path:
            sys.path.remove(expath)
        return None


def try_file(expn: str | None = None):
    try:
        return open(expn, 'w')
    except FileNotFoundError:
        return None


name = input('What\'s the name of your test language (Name/None)? ').lower() or 'bslanguagetest'
values = try_insert()
while not values:
    values = try_insert(input('Couldn\'t find "bsLanguageTest.py" file in the current directory; do you have the file in a custom directory (Path/None)? '))
path = input('Enter the directory path you\'d like the file to be dumped in (Path/None): ') or os.path.abspath(os.getcwd())
namex = '/' + name + '.json'
f = try_file(path + namex)
while not f:
    path = input('The entered path is incorrect, please enter a valid directory path (Path/None)') or os.path.abspath(os.getcwd())
    f = try_file(path + namex)
with f:
    f.write(json.dumps(values))
print('Done! "' + name + '.json" created in ' + path)
