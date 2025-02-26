# ba_meta require api 9

"""
    by shailesh
    discord: shailesh_gabu_11/ShailesH
    
    Function:
        Holds text message of party window's text field.
    
    Logic: 
        store text whenever party window close.
        Then whenever it's open, edit text field with stored text.
    
    Query:    
        Why is there 'z' at first and last in file name?
            first 'z' reason >
              because want to compile this file at last.  
              so this plugin can be compatible with other party window plugins.
            last 'z' reason >
              Nothing... for decoration purpose.
"""

from __future__ import annotations 

# Ballistica API.
import bauiv1 as bui

# Ballistica Libraries.
from bauiv1lib.party import PartyWindow

    
# ba_meta export plugin
class plg(bui.Plugin):
    """ Our plugin type for the game """
    
    # The party window text field's text; that to be hold.
    text: str = ""
    
    # we gonna use decorators cause we need make this mod compatible with others.
    def new_init(func: function) -> function:
    
        def wrapper(*args, **kwargs) -> None:
            # original code.
            func(*args, **kwargs)
            # Editing...
            bui.textwidget(edit=args[0]._text_field, text=plg.text)
        
        return wrapper
    # wrapping new code.
    PartyWindow.__init__ = new_init(PartyWindow.__init__)    

    def new_close(func: function) -> function:

        def wrapper(*args, **kwargs) -> None:
            # storing...
            plg.text = bui.textwidget(query=args[0]._text_field))
            # original code.
            func(*args, **kwargs)
            
        return wrapper
    # wrapping new code.   
    PartyWindow.close = new_close(PartyWindow.close)