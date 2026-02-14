# Hard Work (took me 54 hours), and thx for Polish
# ba_meta require api 9
"""
Players List v1.7 - An Live Players View.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import babase
import bauiv1 as bui
import bascenev1 as bs
from bauiv1 import (
    containerwidget as cw,
    buttonwidget as bw,
    textwidget as tw,
    checkboxwidget as cbw,
    scrollwidget as sw,
    get_special_widget as gsw
)
from bauiv1lib.popup import PopupMenu
from colorsys import hsv_to_rgb

if TYPE_CHECKING:
    from typing import Any

plugman = dict(
    plugin_name="players_list",
    description="A plugin that shows you live players list",
    external_url="https://m.youtube.com/drap_bs",
    authors=[
        {"name": "Drap", "email": "mrunittest@gmail.com", "discord": "drap_bs"}
    ],
    version="1.7.0",
)

PLAYERS_ICON = ""


class ColorPickerWindow:
    """Advanced color picker with custom RGB and preset colors"""
    
    # Preset colors grid (4 rows × 8 columns = 32 colors)
    PRESET_COLORS = [
        # Row 1 - Reds to Greens
        [(1.2, 0.0, 0.0), (0.65, 0.0, 0.0), (1.2, 0.8, 0.0), (0.89, 0.59, 0.0), (0.67, 1.0, 0.0), (0.52, 0.78, 0.0), (0.0, 1.2, 0.0), (0.0, 0.78, 0.0)],
        # Row 2 - Cyans to Purples
        [(0.0, 1.2, 0.8), (0.0, 0.78, 0.52), (0.0, 0.8, 1.2), (0.0, 0.52, 0.78), (0.0, 0.0, 1.2), (0.0, 0.0, 0.78), (0.8, 0.0, 1.2), (0.52, 0.0, 0.78)],
        # Row 3 - Browns/Tans
        [(1.0, 0.82, 0.48), (0.8, 0.62, 0.28), (0.8, 0.8, 0.0), (0.55, 0.55, 0.0)],
    ]
    
    def __init__(self, callback, parent_window):
        self._callback = callback
        self._parent = parent_window
        self._width = 1100
        self._height = 750
        
        # Current RGB values
        self._r = 1.25
        self._g = 1.25
        self._b = 1.25
        
        # Load saved colors from config
        cfg = babase.app.config
        self._saved_colors = cfg.get('Players Display - Saved Colors', [])
        
        self._root_widget = cw(
            parent=gsw('overlay_stack'),
            size=(self._width, self._height),
            transition='in_scale',
            stack_offset=(250.0, -11.0),
            color=(0.25, 0.25, 0.25)
        )
        
        # ═══════════════════════════════════════════════════
        # LEFT SECTION - Custom Color Creator
        # ═══════════════════════════════════════════════════
        left_container = cw(
            parent=self._root_widget,
            position=(-531.9, 5.9),
            size=(520.0, 750.0),
            color=(0.25, 0.25, 0.25),
            root_selectable=True
        )
        
        # "Custom" title
        tw(
            parent=self._root_widget,
            position=(-306.8, 711.5),
            size=(100, 30),
            text='Custom',
            color=(0.75, 0.75, 0.75),
            scale=1.65
        )
        
        # ═══ RGB Color Displays ═══
        # Red display
        self._red_display = bw(
            parent=self._root_widget,
            position=(-481.5, 602.3),
            size=(120.0, 85.0),
            label='',
            button_type='square',
            color=(self._r, 0, 0),
            enable_sound=False
        )
        
        # Green display
        self._green_display = bw(
            parent=self._root_widget,
            position=(-481.5, 516.3),
            size=(120.0, 85.0),
            label='',
            button_type='square',
            color=(0, self._g, 0),
            enable_sound=False
        )
        
        # Blue display
        self._blue_display = bw(
            parent=self._root_widget,
            position=(-481.5, 429.3),
            size=(120.0, 85.0),
            label='',
            button_type='square',
            color=(0, 0, self._b),
            enable_sound=False
        )
        
        # Preview display (gray box)
        self._preview_display = bw(
            parent=self._root_widget,
            position=(-481.5, 316.3),
            size=(120.0, 85.0),
            label='',
            button_type='square',
            color=(self._r, self._g, self._b),
            enable_sound=False
        )
        
        # ═══ RGB Control Buttons ═══
        # RED controls
        bw(
            parent=self._root_widget,
            position=(-358.4, 599.3),
            size=(150.0, 90.0),
            label='+',
            button_type='square',
            textcolor=(0.75, 0.0, 0.0),
            text_scale=2,
            color=(0.15, 0.1, 0.1),
            on_activate_call=lambda: self._adjust_color('r', 0.05)
        )
        
        bw(
            parent=self._root_widget,
            position=(-208.4, 599.3),
            size=(130.0, 90.0),
            label='−',
            button_type='square',
            color=(0.15, 0.1, 0.1),
            text_scale=2,
            textcolor=(0.75, 0, 0),
            on_activate_call=lambda: self._adjust_color('r', -0.05)
        )
        
        # GREEN controls
        bw(
            parent=self._root_widget,
            position=(-358.4, 509.3),
            size=(150.0, 90.0),
            label='+',
            button_type='square',
            textcolor=(0, 0.75, 0.0),
            text_scale=2,
            color=(0.1, 0.15, 0.1),
            on_activate_call=lambda: self._adjust_color('g', 0.05)
        )
        
        bw(
            parent=self._root_widget,
            position=(-208.4, 509.3),
            size=(130.0, 90.0),
            label='−',
            button_type='square',
            color=(0.1, 0.15, 0.1),
            text_scale=2,
            textcolor=(0, 0.75, 0),
            on_activate_call=lambda: self._adjust_color('g', -0.05)
        )
        
        # BLUE controls
        bw(
            parent=self._root_widget,
            position=(-358.4, 419.3),
            size=(150.0, 90.0),
            label='+',
            button_type='square',
            textcolor=(0, 0.0, 0.75),
            text_scale=2,
            color=(0.1, 0.1, 0.15),
            on_activate_call=lambda: self._adjust_color('b', 0.05)
        )
        
        bw(
            parent=self._root_widget,
            position=(-208.4, 418.3),
            size=(130.0, 90.0),
            label='−',
            button_type='square',
            color=(0.1, 0.1, 0.15),
            text_scale=2,
            textcolor=(0, 0, 0.75),
            on_activate_call=lambda: self._adjust_color('b', -0.05)
        )
        
        # ═══ RGB Value Displays ═══
        self._r_text = tw(
            parent=self._root_widget,
            position=(-343.5, 343.4),
            size=(100, 30),
            text=f'{self._r:.2f}',
            color=(1.0, 0.0, 0.0)
        )
        
        self._g_text = tw(
            parent=self._root_widget,
            position=(-253.5, 343.4),
            size=(100, 30),
            text=f'{self._g:.2f}',
            color=(0.0, 1.0, 0.0)
        )
        
        self._b_text = tw(
            parent=self._root_widget,
            position=(-153.5, 343.4),
            size=(100, 30),
            text=f'{self._b:.2f}',
            color=(0.0, 0.0, 1.0)
        )
        
        # ═══ Separator Lines ═══
        bui.imagewidget(
            texture=bui.gettexture('white'),
            opacity=0.6,
            position=(-460.6, 406.2),
            size=(370.0, 4.0),
            parent=self._root_widget,
            color=(0.4, 0.4, 0.4)
        )
        
        bui.imagewidget(
            texture=bui.gettexture('white'),
            opacity=0.6,
            position=(-478.6, 246.2),
            size=(400.0, 4.0),
            parent=self._root_widget,
            color=(0.4, 0.4, 0.4)
        )
        
        bui.imagewidget(
            texture=bui.gettexture('white'),
            opacity=0.2,
            position=(-281.3, 250.8),
            size=(4.0, 52.0),
            parent=self._root_widget
        )
        
        # ═══ Action Buttons ═══
        # Save button
        bw(
            parent=self._root_widget,
            position=(-483.2, 255.0),
            size=(200.0, 45.0),
            label='Save',
            button_type='square',
            textcolor=(1.2, 1.2, 1.2),
            color=(0.0, 0.89, 0.0),
            on_activate_call=self._save_color
        )
        
        # Apply button
        bw(
            parent=self._root_widget,
            position=(-271.2, 256.0),
            size=(200.0, 45.0),
            label='Apply',
            button_type='square',
            textcolor=(1.2, 1.2, 1.2),
            color=(0.0, 0.89, 0.0),
            on_activate_call=self._apply_custom_color
        )
        
        # ═══ Saved Colors Section ═══
        tw(
            parent=self._root_widget,
            position=(-476.8, 212.5),
            size=(100, 30),
            text='Saved',
            color=(0.65, 0.65, 0.65),
            scale=1.2
        )
        
        self._saved_scroll = bui.hscrollwidget(
            parent=self._root_widget,
            position=(-487.9, 63.4),
            size=(420.0, 140.0),
            capture_arrows=True,
            border_opacity=1.2
        )
        
        # ═══════════════════════════════════════════════════
        # RIGHT SECTION - Preset Colors
        # ═══════════════════════════════════════════════════
        
        # "Colors" title
        tw(
            parent=self._root_widget,
            position=(193.2, 711.5),
            size=(100, 30),
            text='Colors',
            color=(0.75, 0.75, 0.75),
            scale=1.65
        )
        
        tw(
            parent=self._root_widget,
            position=(273.2, 702.5),
            size=(100, 30),
            text='pick one for your list !',
            color=(0.55, 0.55, 0.55),
            scale=0.875
        )
        
        # Separator line
        bui.imagewidget(
            texture=bui.gettexture('white'),
            opacity=0.6,
            position=(139.4, 396.2),
            size=(750.0, 7.5),
            parent=self._root_widget,
            color=(0.4, 0.4, 0.4)
        )
        
        bui.imagewidget(
            texture=bui.gettexture('white'),
            opacity=0.2,
            position=(495.7, 402.8),
            size=(7.5, 87.5),
            parent=self._root_widget
        )
        
        # Preset colors grid
        self._create_preset_colors()
        
        # "More Colors Soon...." text
        tw(
            parent=self._root_widget,
            position=(442.6, 347.5),
            size=(100, 30),
            text='More Colors Soon....',
            color=(0.32, 0.32, 0.32),
            shadow=False
        )
        
        # Loading spinner
        bui.spinnerwidget(
            parent=self._root_widget,
            position=(554.3, 323.2),
            size=45.0
        )
        
        # Back button (top left corner)
        bw(
            parent=self._root_widget,
            position=(-510, 690),
            size=(60, 50),
            label='<',
            color=(0.6, 0.1, 0.1),
            textcolor=(1, 0.8, 0.8),
            text_scale=1.5,
            on_activate_call=self._close
        )
        
        # Load saved colors
        self._load_saved_colors()
        
        cw(edit=self._root_widget, on_cancel_call=self._close)
    
    def _load_saved_colors(self):
        """Load and display saved colors from config"""
        if not self._saved_colors:
            return
        
        # Create container for saved colors
        self._saved_container = bui.containerwidget(
            parent=self._saved_scroll,
            size=(max(1000, len(self._saved_colors) * 70), 100),
            background=False
        )
        
        # Add all saved color buttons
        for idx, color in enumerate(self._saved_colors):
            x_pos = idx * 70
            bw(
                parent=self._saved_container,
                position=(x_pos, 10),
                size=(60, 90),
                label='',
                button_type='square',
                color=color,
                on_activate_call=lambda c=color: self._select_saved_color(c)
            )
    
    def _create_preset_colors(self):
        """Create preset color buttons grid"""
        # Starting positions
        start_x = 88.1
        button_size = 80.0
        spacing = 20.0
        
        row_positions = [589.1, 499.1, 409.1]
        
        for row_idx, row_colors in enumerate(self.PRESET_COLORS):
            y = row_positions[row_idx]
            
            for col_idx, color in enumerate(row_colors):
                x = start_x + col_idx * (button_size + spacing)
                
                bw(
                    parent=self._root_widget,
                    position=(x, y),
                    size=(button_size, button_size),
                    label='',
                    button_type='square',
                    color=color,
                    on_activate_call=lambda c=color: self._select_preset_color(c)
                )
    
    def _adjust_color(self, channel: str, amount: float):
        """Adjust RGB values"""
        if channel == 'r':
            self._r = max(0.0, min(1.5, self._r + amount))
        elif channel == 'g':
            self._g = max(0.0, min(1.5, self._g + amount))
        elif channel == 'b':
            self._b = max(0.0, min(1.5, self._b + amount))
        
        self._update_displays()
        bui.getsound('click01').play()
    
    def _update_displays(self):
        """Update all color displays"""
        # Update individual color displays
        bw(edit=self._red_display, color=(self._r, 0, 0))
        bw(edit=self._green_display, color=(0, self._g, 0))
        bw(edit=self._blue_display, color=(0, 0, self._b))
        
        # Update preview
        bw(edit=self._preview_display, color=(self._r, self._g, self._b))
        
        # Update RGB text displays
        tw(edit=self._r_text, text=f'{self._r:.2f}')
        tw(edit=self._g_text, text=f'{self._g:.2f}')
        tw(edit=self._b_text, text=f'{self._b:.2f}')
    
    def _save_color(self):
        """Save current color to saved list"""
        current_color = (self._r, self._g, self._b)
        self._saved_colors.append(current_color)
        
        # Save to config
        cfg = babase.app.config
        cfg['Players Display - Saved Colors'] = self._saved_colors
        cfg.commit()
        
        # Create container for saved colors if doesn't exist
        if not hasattr(self, '_saved_container'):
            self._saved_container = bui.containerwidget(
                parent=self._saved_scroll,
                size=(1000, 100),
                background=False
            )
        
        # Add color button in horizontal line
        x_pos = (len(self._saved_colors) - 1) * 70  # 70 = button width + spacing
        
        saved_btn = bw(
            parent=self._saved_container,
            position=(x_pos, 10),
            size=(60, 90),
            label='',
            button_type='square',
            color=current_color,
            on_activate_call=lambda c=current_color: self._select_saved_color(c)
        )
        
        bui.screenmessage('Saved!', color=(0, 1, 0))
        bui.getsound('cashRegister').play()
    
    def _select_saved_color(self, color: tuple):
        """Select a saved color and apply it"""
        # Update custom RGB values
        self._r, self._g, self._b = color
        self._update_displays()
        
        # Apply the color
        self._callback(color)
        bui.screenmessage('Applied!', color=(0, 1, 0))
        bui.getsound('ding').play()
    
    def _apply_custom_color(self):
        """Apply the custom RGB color (don't close)"""
        self._callback((self._r, self._g, self._b))
        bui.screenmessage('Applied!', color=(0, 1, 0))
        bui.getsound('dingSmall').play()
    
    def _select_preset_color(self, color: tuple):
        """Select a preset color and close the window"""
        self._callback(color)
        self._close()  # Close the window after selecting
    
    def _close(self):
        cw(edit=self._root_widget, transition='out_scale')


class SettingsWindow:
    """Main settings window with live preview"""
    
    # Design styles
    DESIGNS = ['box', 'simple', 'minimal']
    
    def __init__(self, source_widget=None):
        self._width = 1150
        self._height = 700
        
        # Get current settings
        cfg = babase.app.config
        self._temp_show_full = cfg.get('Players Display - Show Full Name', False)
        self._temp_name_type = cfg.get('Players Display - Name Type', 'Player Name')
        self._temp_color = cfg.get('Players Display - Color', (1, 1, 1))
        self._temp_rainbow = cfg.get('Players Display - Rainbow', False)
        self._temp_show_id = cfg.get('Players Display - Show Client ID', True)
        self._temp_style = cfg.get('Players Display - Style', 'box')
        
        self._root_widget = cw(
            parent=gsw('overlay_stack'),
            size=(self._width, self._height),
            transition='in_scale',
            stack_offset=(-250.0, -20.0),
            color=(0.25, 0.25, 0.25)
        )
        
        # ═══════════════════════════════════════════════════
        # HEADER
        # ═══════════════════════════════════════════════════
        
        # Back button
        bw(
            parent=self._root_widget,
            position=(9.6, 626.3),
            size=(135.0, 120.0),
            label='«',
            color=(1.2, 0.0, 0.0),
            textcolor=(1.5, 1.5, 1.5),
            text_scale=2,
            scale=0.75,
            on_activate_call=self._close
        )
        
        # Settings title
        tw(
            parent=self._root_widget,
            position=(188.3, 661.9),
            size=(100, 30),
            text='Settings',
            color=(0.75, 0.75, 0.75),
            scale=2
        )
        
        tw(
            parent=self._root_widget,
            position=(318.3, 651.9),
            size=(100, 30),
            text='Customize Your Players List.',
            color=(0.55, 0.55, 0.55),
            scale=0.85,
            shadow=0.4
        )
        
        # Apply button
        bw(
            parent=self._root_widget,
            position=(877.9, 639.1),
            size=(185.0, 100.0),
            label='Apply',
            color=(0.0, 0.89, 0.0),
            textcolor=(1, 1, 1),
            on_activate_call=self._apply_changes
        )
        
        # ═══════════════════════════════════════════════════
        # MAIN SCROLL AREA
        # ═══════════════════════════════════════════════════
        
        scroll = sw(
            parent=self._root_widget,
            position=(86.8, 61.7),
            size=(1000.0, 569.0),
            border_opacity=1.25
        )
        
        # ═══════════════════════════════════════════════════
        # SHOW PLAYER SECTION
        # ═══════════════════════════════════════════════════
        
        tw(
            parent=self._root_widget,
            position=(111.4, 581.4),
            size=(100, 30),
            text='Show Player',
            scale=1.25,
            color=(0.85, 0.85, 0.85)
        )
        
        # Separator line
        bui.imagewidget(
            texture=bui.gettexture('white'),
            opacity=0.6,
            position=(94.3, 480.9),
            size=(975.0, 4.0),
            parent=self._root_widget
        )
        
        # Name type label
        tw(
            parent=self._root_widget,
            position=(95, 535),
            size=(0, 0),
            text='Name Type:',
            color=(0.85, 0.85, 0.85),
            h_align='left',
            v_align='center',
            scale=0.8
        )
        
        # Popup menu for name type selection
        PopupMenu(
            parent=self._root_widget,
            position=(95, 487),
            choices=['Account Name', 'Player Name'],
            current_choice=self._temp_name_type,
            on_value_change_call=self._set_name_type,
            button_size=(185, 45)
        )
        
        # Vertical separator 1
        bui.imagewidget(
            texture=bui.gettexture('white'),
            opacity=0.45,
            position=(275.8, 483.6),
            size=(4.0, 90.0),
            parent=self._root_widget
        )
        
        # Full Name checkbox (shows both names)
        cbw(
            parent=self._root_widget,
            position=(288.0, 513.1),
            size=(100, 30),
            text='Full Name',
            color=(0.0, 0.89, 0.0),
            scale=1.2,
            textcolor=(1, 1, 1),
            value=self._temp_show_full,
            on_value_change_call=self._on_full_name_change
        )
        
        # Vertical separator 2
        bui.imagewidget(
            texture=bui.gettexture('white'),
            opacity=0.45,
            position=(495.8, 483.6),
            size=(4.0, 90.0),
            parent=self._root_widget
        )
        
        # Client ID checkbox
        cbw(
            parent=self._root_widget,
            position=(509.9, 510.8),
            size=(100, 30),
            text='Client ID',
            textcolor=(1, 1, 1.0),
            color=(0.05, 0.78, 0.05),
            scale=1.25,
            value=self._temp_show_id,
            on_value_change_call=self._on_client_id_change
        )
        
        # ═══════════════════════════════════════════════════
        # COLOR SECTION
        # ═══════════════════════════════════════════════════
        
        tw(
            parent=self._root_widget,
            position=(108.3, 431.9),
            size=(100, 30),
            text='Color',
            color=(0.75, 0.75, 0.75),
            scale=1.35
        )
        
        # Separator line
        bui.imagewidget(
            texture=bui.gettexture('white'),
            opacity=0.6,
            position=(94.3, 336.9),
            size=(975.0, 2.5),
            parent=self._root_widget
        )
        
        # Color display button
        self._color_display = bw(
            parent=self._root_widget,
            position=(97.0, 341.5),
            size=(85.0, 85.0),
            label='',
            color=self._temp_color,
            enable_sound=False
        )
        
        # Vertical separator
        bui.imagewidget(
            texture=bui.gettexture('white'),
            opacity=0.45,
            position=(192.8, 338.6),
            size=(5.0, 80.0),
            parent=self._root_widget
        )
        
        # Pick button
        bw(
            parent=self._root_widget,
            position=(198.6, 343.3),
            size=(160.0, 80.0),
            label='Pick',
            button_type='square',
            color=(0.0, 0.0, 0.3555),
            textcolor=(0.9, 0.9, 1),
            on_activate_call=self._open_color_picker
        )
        
        # Vertical separator
        bui.imagewidget(
            texture=bui.gettexture('white'),
            opacity=0.45,
            position=(362.8, 338.6),
            size=(5.0, 80.0),
            parent=self._root_widget
        )
        
        # Rainbow checkbox
        cbw(
            parent=self._root_widget,
            position=(378.0, 353.1),
            size=(100, 30),
            text='Rainbow',
            color=(0.0, 0.89, 0.0),
            scale=1.2,
            textcolor=(1, 1, 1),
            value=self._temp_rainbow,
            on_value_change_call=self._on_rainbow_change
        )
        
        # ═══════════════════════════════════════════════════
        # DESIGN SECTION
        # ═══════════════════════════════════════════════════
        
        tw(
            parent=self._root_widget,
            position=(108.3, 301.9),
            size=(100, 30),
            text='Design',
            color=(0.75, 0.75, 0.75),
            scale=1.35
        )
        
        # Design buttons (3 styles)
        self._design_btns = []
        
        # Box style
        btn1 = bw(
            parent=self._root_widget,
            position=(84.2, 63.8),
            size=(350.0, 225.0),
            label='BOX Style',
            button_type='square',
            color=(0.1, 1.2, 0.1) if self._temp_style == 'box' else (0.75, 0.85, 0.75),
            on_activate_call=lambda: self._set_style('box')
        )
        self._design_btns.append(btn1)
        
        # Simple style
        btn2 = bw(
            parent=self._root_widget,
            position=(417.2, 63.8),
            size=(350.0, 225.0),
            label='Simple Style',
            button_type='square',
            color=(0.1, 1.2, 0.1) if self._temp_style == 'simple' else (0.75, 0.85, 0.75),
            on_activate_call=lambda: self._set_style('simple')
        )
        self._design_btns.append(btn2)
        
        # Minimal style
        btn3 = bw(
            parent=self._root_widget,
            position=(744.2, 63.8),
            size=(350.0, 225.0),
            label='Minimal Style',
            button_type='square',
            color=(0.1, 1.2, 0.1) if self._temp_style == 'minimal' else (0.75, 0.85, 0.75),
            on_activate_call=lambda: self._set_style('minimal')
        )
        self._design_btns.append(btn3)
        
        # ═══════════════════════════════════════════════════
        # RESULT SECTION (Preview)
        # ═══════════════════════════════════════════════════
        
        result_container = cw(
            parent=self._root_widget,
            position=(1147.2, 121.9),
            size=(450.0, 500.0),
            color=(0.25, 0.25, 0.25)
        )
        
        tw(
            parent=self._root_widget,
            position=(1328.3, 581.9),
            size=(100, 30),
            text='Result',
            color=(0.75, 0.75, 0.75),
            scale=1.55
        )
        
        # Preview text widget
        self._preview_text = tw(
            parent=result_container,
            position=(225, 350),
            size=(0, 0),
            text=self._generate_preview_text(),
            color=self._temp_color,
            h_align='center',
            v_align='center',
            scale=0.5,
            maxwidth=400
        )
        
        # Start preview update loop
        self._update_preview()
        
        cw(edit=self._root_widget, on_cancel_call=self._close)
    
    def _generate_preview_text(self):
        """Generate preview text based on current settings"""
        player_count = 3  # Sample count
        
        # Get icon
        icon_text = f"{PLAYERS_ICON} " if PLAYERS_ICON else ""
        
        """Generate preview text based on current settings"""
        player_count = 3  # Sample count
        
        if self._temp_style == 'box':
            header = "╔═══════════════════╗\n"
            header += f"║       PLAYERS ({player_count})  ║\n"
            header += "╠═══════════════════╣\n\n"
            footer = "\n\n╚═══════════════════╝"
        elif self._temp_style == 'simple':
            header = "━━━━━━━━━━━━━━━━━━━\n"
            header += f" PLAYERS ({player_count})\n"
            header += "━━━━━━━━━━━━━━━━━━━\n\n"
            footer = "\n\n━━━━━━━━━━━━━━━━━━━"
        else:  # minimal
            header = f" PLAYERS ({player_count})\n\n"
            footer = ""
        
        # Sample names
        player_name = "YT!Drap"
        account_name = "Drap"
        
        # Build player line based on settings
        if self._temp_show_full:
            # Full name: show both
            name_part = f"{player_name} | {account_name}"
        else:
            # Show based on name type
            if self._temp_name_type == 'Account Name':
                name_part = account_name
            else:
                name_part = player_name
        
        # Add client ID if enabled
        if self._temp_show_id:
            player_line = f"  • {name_part} [#42]"
        else:
            player_line = f"  • {name_part}"
        
        return header + player_line + footer
    
    def _update_preview(self):
        """Update preview with rainbow effect if enabled"""
        if not hasattr(self, '_preview_text') or not self._preview_text.exists():
            return
        
        # Update preview text
        tw(edit=self._preview_text, text=self._generate_preview_text())
        
        # Update color (rainbow or static)
        if self._temp_rainbow:
            # Smooth rainbow loop
            if not hasattr(self, '_rainbow_hue'):
                self._rainbow_hue = 0.0
            
            self._rainbow_hue = (self._rainbow_hue + 0.02) % 1.0
            color = hsv_to_rgb(self._rainbow_hue, 1.0, 1.0)
            tw(edit=self._preview_text, color=color)
        else:
            tw(edit=self._preview_text, color=self._temp_color)
        
        # Schedule next update
        babase.apptimer(0.05, babase.WeakCall(self._update_preview))
    
    def _set_name_type(self, name_type: str):
        """Set name type"""
        self._temp_name_type = name_type
    
    def _set_style(self, style: str):
        """Set design style and update button colors"""
        self._temp_style = style
        
        # Update all design buttons
        for idx, btn in enumerate(self._design_btns):
            if self.DESIGNS[idx] == style:
                bw(edit=btn, color=(0.1, 1.2, 0.1))
            else:
                bw(edit=btn, color=(0.75, 0.85, 0.75))
    
    def _on_full_name_change(self, value: bool):
        self._temp_show_full = value
    
    def _on_client_id_change(self, value: bool):
        self._temp_show_id = value
    
    def _on_rainbow_change(self, value: bool):
        self._temp_rainbow = value
    
    def _on_color_selected(self, color: tuple):
        self._temp_color = color
        bw(edit=self._color_display, color=color)
    
    def _open_color_picker(self):
        ColorPickerWindow(self._on_color_selected, self)
    
    def _apply_changes(self):
        """Apply all changes and save to config"""
        cfg = babase.app.config
        cfg['Players Display - Show Full Name'] = self._temp_show_full
        cfg['Players Display - Name Type'] = self._temp_name_type
        cfg['Players Display - Color'] = self._temp_color
        cfg['Players Display - Rainbow'] = self._temp_rainbow
        cfg['Players Display - Show Client ID'] = self._temp_show_id
        cfg['Players Display - Style'] = self._temp_style
        cfg.commit()
        
        bui.screenmessage('Settings Applied!', color=(0, 1, 0))
        bui.getsound('cashRegister').play()
    
    def _close(self):
        cw(edit=self._root_widget, transition='out_scale')


class PlayersDisplay:
    """Main display class"""
    
    def __init__(self):
        self.container = None
        self.rainbow_hue = 0.0
        self.current_players = {}  # Track: {client_id: (player_name, account_name)}
        
    def on_app_running(self):
        self._update_loop()
    
    def _update_loop(self):
        self._update_display()
        
        # Check if rainbow mode is enabled
        cfg = babase.app.config
        is_rainbow = cfg.get('Players Display - Rainbow', False)
        
        # Use faster loop for smooth rainbow, slower for normal updates
        delay = 0.05 if is_rainbow else 0.5
        babase.apptimer(delay, babase.WeakCall(self._update_loop))
    
    def _get_display_color(self):
        cfg = babase.app.config
        
        if cfg.get('Players Display - Rainbow', False):
            # Smooth rainbow loop with smaller increment
            self.rainbow_hue = (self.rainbow_hue + 0.01) % 1.0
            return hsv_to_rgb(self.rainbow_hue, 1.0, 1.0)
        else:
            return cfg.get('Players Display - Color', (0.7, 0.7, 0.7))
    
    def _show_message(self, message: str, color: tuple, duration: float = 1.0):
        """Show a temporary message with fade in/out animation"""
        try:
            activity = bs.get_foreground_host_activity()
            if activity is None:
                return
            
            with activity.context:
                # Create message node
                msg_node = bs.newnode(
                    'text',
                    attrs={
                        'text': message,
                        'scale': 0.65,
                        'color': color,
                        'h_attach': 'right',
                        'v_attach': 'top',
                        'h_align': 'left',
                        'v_align': 'top',
                        'position': (-240, -270),  # Below the main list
                        'flatness': 0.0,
                        'shadow': 1.2,
                        'opacity': 0.0  # Start invisible
                    }
                )
                
                # Fade in animation (0.2 seconds)
                bs.animate(msg_node, 'opacity', {
                    0.0: 0.0,
                    0.2: 0.95
                })
                
                # Fade out animation (starts after duration)
                bs.animate(msg_node, 'opacity', {
                    duration: 0.95,
                    duration + 0.3: 0.0
                })
                
                # Delete node after animations complete
                bs.timer(duration + 0.4, msg_node.delete)
                
        except Exception:
            pass
    
    def _check_player_changes(self, new_players: dict):
        """Check for players joining or leaving
        new_players: {client_id: (player_name, account_name)}
        """
        new_ids = set(new_players.keys())
        old_ids = set(self.current_players.keys())
        
        # Players who joined
        joined = new_ids - old_ids
        for player_id in joined:
            player_name, account_name = new_players[player_id]
            message = f"{account_name} joined the server"
            color = self._get_display_color()
            self._show_message(message, color, duration=1.0)
        
        # Players who left
        left = old_ids - new_ids
        for player_id in left:
            player_name, account_name = self.current_players[player_id]
            message = f"{player_name} left the server"
            color = (1.2, 0.2, 0.2)  # Glowing red
            self._show_message(message, color, duration=1.0)
        
        # Update current players
        self.current_players = new_players.copy()
    
    def _update_display(self):
        try:
            activity = bs.get_foreground_host_activity()
        except Exception:
            activity = None
        
        if activity is None:
            if self.container is not None:
                try:
                    self.container.delete()
                except Exception:
                    pass
                self.container = None
            return
        
        cfg = babase.app.config
        show_full = cfg.get('Players Display - Show Full Name', False)
        name_type = cfg.get('Players Display - Name Type', 'Player Name')
        show_client_id = cfg.get('Players Display - Show Client ID', True)
        style = cfg.get('Players Display - Style', 'box')
        
        player_names = []
        new_players_data = {}  # {client_id: (player_name, account_name)}
        
        for p in activity.players:
            try:
                # Get both player name and account name
                player_name = p.getname(full=True)
                
                try:
                    account_name = p.sessionplayer.inputdevice.get_v1_account_name(full=True)
                    if not account_name:
                        account_name = player_name
                except Exception:
                    account_name = player_name
                
                # Get client ID
                try:
                    client_id = p.sessionplayer.inputdevice.client_id
                except Exception:
                    client_id = id(p)  # Fallback to object id
                
                # Store for tracking
                new_players_data[client_id] = (player_name, account_name)
                
                # Build name based on settings
                if show_full:
                    # Full name: show both names
                    if player_name != account_name:
                        name = f"{player_name} | {account_name}"
                    else:
                        name = player_name
                else:
                    # Show based on name type
                    if name_type == 'Account Name':
                        name = account_name
                    else:
                        name = player_name
                
                # Add client ID if enabled
                if show_client_id:
                    try:
                        player_names.append(f"  • {name} [#{client_id}]")
                    except Exception:
                        player_names.append(f"  • {name}")
                else:
                    player_names.append(f"  • {name}")
                    
            except Exception:
                continue
        
        # Check for player changes (join/leave)
        self._check_player_changes(new_players_data)
        
        # Get player count
        player_count = len(player_names)
        
        # Get icon
        icon_text = f"{PLAYERS_ICON} " if PLAYERS_ICON else ""
        
        # Different styles with player count
        if style == 'box':
            header = "╔═══════════════════╗\n"
            header += f"║  PLAYERS ({player_count})       ║\n"
            header += "╠═══════════════════╣\n\n"
            footer = "\n\n╚═══════════════════╝"
        elif style == 'simple':
            header = "━━━━━━━━━━━━━━━━━━━\n"
            header += f"{icon_text}PLAYERS ({player_count})\n"
            header += "━━━━━━━━━━━━━━━━━━━\n\n"
            footer = "\n\n━━━━━━━━━━━━━━━━━━━"
        else:  # minimal
            header = f" PLAYERS ({player_count})\n\n"
            footer = ""
        
        if player_names:
            players_str = "\n".join(player_names)
        else:
            players_str = "     ⏳ Waiting...\n     No players yet"
        
        final_text = header + players_str + footer
        current_color = self._get_display_color()
        
        try:
            with activity.context:
                if self.container is None or not self.container.exists():
                    self.container = bs.newnode(
                        'text',
                        attrs={
                            'text': final_text,
                            'scale': 0.7,
                            'color': current_color,
                            'h_attach': 'right',
                            'v_attach': 'top',
                            'h_align': 'left',
                            'v_align': 'top',
                            'position': (-240, -90),
                            'flatness': 0.0,
                            'shadow': 1.2,
                            'opacity': 0.95
                        }
                    )
                else:
                    self.container.text = final_text
                    self.container.color = current_color
        except Exception:
            pass

# My First Cool Mod ,WooHoo.
# ba_meta export babase.Plugin
class CoolList(babase.Plugin):
    """Main plugin class"""
    
    def __init__(self):
        cfg = babase.app.config
        
        if 'Players Display - Show Full Name' not in cfg:
            cfg['Players Display - Show Full Name'] = False  # Default to single name
        if 'Players Display - Name Type' not in cfg:
            cfg['Players Display - Name Type'] = 'Player Name'  # Default to player name
        if 'Players Display - Color' not in cfg:
            cfg['Players Display - Color'] = (1, 1, 1)
        if 'Players Display - Rainbow' not in cfg:
            cfg['Players Display - Rainbow'] = False
        if 'Players Display - Show Client ID' not in cfg:
            cfg['Players Display - Show Client ID'] = True
        if 'Players Display - Style' not in cfg:
            cfg['Players Display - Style'] = 'box'
        
        cfg.commit()
        
        self.display = PlayersDisplay()
        self.display.on_app_running()
    
    def has_settings_ui(self) -> bool:
        return True
    
    def show_settings_ui(self, source_widget: Any) -> None:
        SettingsWindow(source_widget)
