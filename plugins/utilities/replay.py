# Copyright 2025 - Solely by BrotherBoard
# Intended for personal use only
# Bug? Feedback? Telegram >> @BroBordd

"""
Replay v3.0 - Simple replay player

Experimental. Feedback is appreciated.
Adds a button to pause menu and watch menu.

Features:
- Common features (pause/play/seek/speed/replay)
- Press on progress bar to seek anywhere
- Advanced free camera target control
- Ability to zoom in/out anywhere in the 3D world
- Instant replay start with progressive duration scanning
- Stream-like buffering (like YouTube) which plays while loading
- Good UI with detailed toast pop ups
- Ability to show/hide UI
- Uses threading for non-blocking duration calculation
- Dynamic progress bar that grows with estimated duration
- Visual scan progress indicator with alternating % and time display
"""

from babase import Plugin
import bauiv1 as bui
from bauiv1 import CallPartial
import bascenev1 as bs
import _babase as _ba
import os
from time import strftime, gmtime, time
from random import uniform
from threading import Thread
from struct import unpack

class Replay:
    VER = '3.0'
    COL1 = (0.18, 0.18, 0.18)
    COL2 = (1, 1, 1)
    COL3 = (0, 1, 0)
    COL4 = (0, 1, 1)
    BUSY = False

    @classmethod
    def is_busy(cls, value=None):
        if value is None:
            return cls.BUSY
        cls.BUSY = value

    def __init__(self, source=None):
        self.selected = self.replay_name = self.buffer = None
        self.error = False
        self.huffman = _Huffman()
        self.parent = self.create_container(
            src=source.get_screen_space_center(),
            p=get_overlay_stack(),
            size=(400, 500),
            oac=lambda: (
                bui.containerwidget(self.parent, transition='out_scale' if source and source.exists() else 'out_left'),
                self.play_sound('laser'),
                self.transition_sound.stop()
            )
        )
        self.transition_sound = self.play_sound('powerup01')
        self.create_text(
            p=self.parent,
            h_align='center',
            text='Replay',
            pos=(175, 460),
            scale=2
        )
        scroll_y = 360
        scroll_parent = bui.scrollwidget(
            parent=self.parent,
            size=(scroll_y, scroll_y),
            position=(25, 80)
        )
        self.replays_dir = bui.get_replays_dir()
        replays = [f for f in os.listdir(self.replays_dir) if f.endswith('.brp')]
        scroll_height = 30 * len(replays)
        scroll_content = bui.containerwidget(
            parent=scroll_parent,
            background=False,
            size=(scroll_y, scroll_height)
        )
        self.replay_widgets = []
        for idx, replay_file in enumerate(replays):
            widget = self.create_text(
                p=scroll_content,
                click_activate=True,
                selectable=True,
                pos=(0, scroll_height - 30 * idx - 30),
                text=replay_file,
                maxwidth=scroll_y,
                size=(scroll_y, 30),
                color=self.COL2,
                oac=CallPartial(self.highlight, idx, replay_file)
            )
            self.replay_widgets.append(widget)
        self.play_source = None
        for i in range(3):
            btn = self.create_button(
                p=self.parent,
                pos=(25 + 120 * i, 30),
                size=(120, 40),
                label=['Show', 'Copy', 'Run'][i],
                oac=CallPartial(self.execute, [self.show, self.copy, self.play][i]),
                icon=bui.gettexture(['folder', 'file', 'nextLevelIcon'][i])
            )
            if i == 2:
                self.play_source = btn

    def play_sound(self, name):
        sound = bui.getsound(name)
        sound.play()
        bui.apptimer(uniform(0.14, 0.17), sound.stop)
        return sound

    def get_replay_path(self):
        return os.path.join(self.replays_dir, self.replay_name)

    def copy(self):
        self.play_sound('dingSmallHigh')
        bui.clipboard_set_text(self.get_replay_path())
        bui.screenmessage('Copied replay path to clipboard!', color=self.COL3)

    def show(self):
        bui.getsound('ding').play()
        bui.screenmessage(self.get_replay_path(), color=self.COL3)

    def execute(self, func):
        if self.selected is None:
            show_warning('Select a replay!')
            return
        if bs.is_in_replay():
            show_warning('A replay is already running!')
            return
        return func()

    def highlight(self, idx, name):
        if self.selected == idx:
            self.play_source = self.replay_widgets[idx]
            self.play()
            return
        self.selected = idx
        self.replay_name = name
        [bui.textwidget(w, color=self.COL2) for w in self.replay_widgets]
        bui.textwidget(self.replay_widgets[idx], color=self.COL3)

    def play(self):
        """Start replay immediately without waiting for duration calculation"""
        if self.is_busy():
            return
        self.is_busy(True)
        bui.getsound('deek').play()
        
        # Start replay immediately
        bs.set_replay_speed_exponent(0)
        bui.fade_screen(1)
        
        # Create player with unknown duration
        Player(path=self.get_replay_path(), duration=None)
        self.is_busy(False)

    def load(self):
        src = self.play_source.get_screen_space_center()
        if self.play_source.get_widget_type() == 'text':
            src = (src[0] - 170, src[1])
        self.parent_container = container = self.create_container(
            src=src,
            size=(300, 200),
            p=get_overlay_stack()
        )
        self.create_text(
            p=container,
            text='Player',
            pos=(125, 150),
            h_align='center',
            scale=1.4
        )
        bui.spinnerwidget(
            parent=container,
            size=60,
            position=(75, 100)
        )
        self.status_text = self.create_text(
            p=container,
            text='Reading...',
            pos=(115, 87)
        )
        self.progress_text = self.create_text(
            p=container,
            pos=(125, 30),
            maxwidth=240,
            text=f'{self.replay_name} with total of {os.path.getsize(self.get_replay_path())} bytes\nstreaming bytes to pybrp_stream',
            h_align='center'
        )
        self.progress_text2 = self.create_text(
            p=container,
            maxwidth=240,
            pos=(30, 20),
            v_align='bottom'
        )
        self.progress = [0, 1]
        bui.apptimer(0.5, Thread(target=self.calculate).start)
        bui.apptimer(0.5, self.update_progress)
        self.wait_for_calculation(self.finish_calculation)

    def update_progress(self):
        current, total = self.progress
        bui.apptimer(0.1, self.update_progress) if (current != total) and (not self.error) else 0
        if not current:
            return
        percent = current / total * 100
        bar = '\u2588' * int(percent) + '\u2591' * int(100 - percent)
        if not self.error:
            try:
                bui.textwidget(self.progress_text, text=bar)
                bui.textwidget(self.progress_text2, text=f'{current} of {total} bytes read')
            except:
                return

    def calculate(self):
        try:
            self.buffer = get_replay_duration(self.huffman, self.get_replay_path(), self.progress)
        except:
            self.buffer = 0

    def finish_calculation(self, duration):
        bui.textwidget(self.status_text, text='Starting...' if duration else 'Wait what?')
        bui.textwidget(self.progress_text2, text=f'result was {duration} milleseconds') if duration else duration
        if not duration:
            self.error = True
            bui.textwidget(self.progress_text, text='pybrp returned zero duration, error?\nclosing this window in 5 seconds')
            bui.textwidget(self.progress_text2, text='')
        bui.apptimer(1 if duration else 5, CallPartial(self.start_player, duration))

    def wait_for_calculation(self, callback, iterations=60):
        if not iterations:
            self.buffer = None
            callback(None)
            return
        if self.buffer is not None:
            result = self.buffer
            self.buffer = None
            callback(result)
            return
        bui.apptimer(0.5, CallPartial(self.wait_for_calculation, callback, iterations - 1))

    def start_player(self, duration):
        if duration == 0:
            show_warning("Couldn't load replay!")
            bui.containerwidget(self.parent_container, transition='out_scale')
            self.is_busy(False)
            return
        bs.set_replay_speed_exponent(0)
        bui.fade_screen(1)
        Player(path=self.get_replay_path(), duration=duration)
        self.is_busy(False)

    def create_button(self, p=None, oac=None, pos=None, **kwargs):
        return bui.buttonwidget(
            parent=p,
            color=self.COL1,
            textcolor=self.COL2,
            on_activate_call=oac,
            position=pos,
            button_type='square',
            enable_sound=False,
            **kwargs
        )

    def create_container(self, p=None, pos=None, src=None, oac=None, **kwargs):
        return bui.containerwidget(
            color=self.COL1,
            parent=p,
            position=pos,
            scale_origin_stack_offset=src,
            transition='in_scale',
            on_outside_click_call=oac,
            **kwargs
        )

    def create_text(self, color=None, oac=None, p=None, pos=None, **kwargs):
        return bui.textwidget(
            parent=p,
            position=pos,
            color=color or self.COL2,
            on_activate_call=oac,
            **kwargs
        )

class Player:
    TICK = 0.01
    COL0 = (0.5, 0, 0)
    COL1 = (1, 0, 0)
    COL2 = (0.5, 0.5, 0)
    COL3 = (1, 1, 0)
    COL4 = (0, 0.5, 0)
    COL5 = (0, 1, 0)
    COL6 = (0, 0.5, 0.5)
    COL7 = (0, 1, 1)
    COL8 = (0.6, 0.6, 0.6)
    COL9 = (8, 0, 0)
    COL10 = (0.5, 0.25, 0)
    COL11 = (1, 0.5, 0)
    COL12 = (0.5, 0.25, 0.5)
    COL13 = (1, 0.5, 1)
    COL14 = (0.5, 0.5, 0.5)
    COL15 = (1, 1, 1)
    COL16 = (0.1, 0.2, 0.4)
    COL17 = (1, 1.7, 2)
    COL18 = (0.45, 0.45, 0.45)
    COL19 = (1, 0.8, 0)

    def __init__(self, path, duration):
        self.path = path
        self.duration_ms = duration  # Will be None initially
        self.duration_sec = None if duration is None else duration / 1000
        self.scanning = duration is None
        self.scan_progress = [0, 1]
        self.estimated_duration = 10.0  # Start with 10 second estimate
        self.confirmed_duration_sec = 0
        self.paused = self.ui_hidden = self.camera_on = self.cinema_mode = self.manual_zoom = False
        self.camera_look = None
        self.replay_time = self.start_time = self.progress_val = 0
        self.camera_zoom = 1
        [setattr(self, attr, []) for attr in ['ui_widgets', 'camera_widgets', 'hide_widgets', 'cinema_widgets', 'cinema_ui_widgets']]
        
        # Start replay immediately
        bs.new_replay_session(path)
        
        width, height = bui.get_virtual_screen_size()
        self.bar_height = 80
        self.parent = bui.containerwidget(
            size=(width, self.bar_height),
            stack_offset=(0, -height / 2 + self.bar_height / 2),
            background=False
        )
        self.background = bui.imagewidget(
            parent=self.parent,
            texture=bui.gettexture('black'),
            size=(width + 3, self.bar_height + 5),
            position=(0, -2),
            opacity=0.4
        )

        self.create_ui()
        self.create_hide_button()
        self.speed = 1
        self.start_focus()
        self.play()

        if self.scanning:
            self.huffman = _Huffman()
            self.scan_cycle = 0  # For alternating display
            Thread(target=self.calculate_duration).start()
            self.scan_timer = bui.AppTimer(0.1, self.update_scan_progress, repeat=True)

    def calculate_duration(self):
        """Calculate duration in background thread with reduced load"""
        import time as pytime
        
        try:
            total_ms = 0
            last_yield = pytime.time()
            
            with open(self.path, 'rb') as f:
                f.seek(0, 2)
                file_size = f.tell()
                self.scan_progress[1] = file_size
                f.seek(6)
                
                while True:
                    current_pos = f.tell()
                    self.scan_progress[0] = current_pos
                    
                    # Yield control every 10ms to prevent freezing
                    current_time = pytime.time()
                    if current_time - last_yield > 0.01:
                        pytime.sleep(0.005)  # Small sleep to reduce CPU load
                        last_yield = current_time
                    
                    b_data = f.read(1)
                    if not b_data:
                        break
                    
                    b1, comp_len = b_data[0], 0
                    if b1 < 254:
                        comp_len = b1
                    elif b1 == 254:
                        comp_len = int.from_bytes(f.read(2), 'little')
                    else:
                        comp_len = int.from_bytes(f.read(4), 'little')
                    
                    if comp_len == 0:
                        continue
                    
                    raw_msg = self.huffman.decompress(f.read(comp_len))
                    
                    if not raw_msg or raw_msg[0] != 1:
                        continue
                    
                    sub_off = 1
                    while sub_off + 2 <= len(raw_msg):
                        sub_size_bytes = raw_msg[sub_off:sub_off+2]
                        if len(sub_size_bytes) < 2:
                            break
                        sub_size = int.from_bytes(sub_size_bytes, 'little')
                        sub_off += 2
                        if sub_off + sub_size > len(raw_msg):
                            break
                        sub_data = raw_msg[sub_off:sub_off+sub_size]
                        if len(sub_data) >= 2 and sub_data[0] == 0:
                            total_ms += sub_data[1]
                        sub_off += sub_size
                    
                    # Update confirmed duration (this is safe to seek to!)
                    self.confirmed_duration_sec = total_ms / 1000
                    
                    # Update estimated duration based on progress
                    if current_pos > 1000:  # After reading at least 1KB
                        progress_percent = current_pos / file_size
                        if progress_percent > 0:
                            estimated_total_ms = total_ms / progress_percent
                            self.estimated_duration = max(10.0, estimated_total_ms / 1000)
            
            self.scan_progress[0] = self.scan_progress[1]
            self.duration_ms = total_ms
            self.duration_sec = total_ms / 1000
            
        except Exception as e:
            self.duration_ms = 0
            self.duration_sec = 0
        finally:
            self.scanning = False
    
    def update_scan_progress(self):
        """Update duration text with scan progress - alternates between % and estimated time"""
        if not self.scanning:
            self.scan_timer = None
            # Fade out loading bar
            if hasattr(self, 'loading_bar') and self.loading_bar.exists():
                bui.imagewidget(self.loading_bar, opacity=0)
            if self.main_bar.exists():
                bui.imagewidget(self.main_bar, opacity=0.6)
            
            # Update to show final duration with normal color
            if hasattr(self, 'duration_time_text') and self.duration_time_text.exists():
                bui.textwidget(
                    self.duration_time_text,
                    text=format_time(self.duration_sec),
                    color=self.COL6
                )
            return
        
        # Show scanning progress
        if hasattr(self, 'duration_time_text') and self.duration_time_text.exists():
            current, total = self.scan_progress
            if total > 0:
                percent = int((current / total) * 100)
                
                # Cycle between showing percentage and estimated time
                self.scan_cycle += 1
                show_percent = (self.scan_cycle // 10) % 2 == 0  # Switch every second
                
                if show_percent:
                    # Show scan percentage
                    bui.textwidget(
                        self.duration_time_text,
                        text=f'Scan {percent}%',
                        color=self.COL6
                    )
                else:
                    # Show estimated duration in orange
                    est_mins = int(self.estimated_duration // 60)
                    est_secs = int(self.estimated_duration % 60)
                    bui.textwidget(
                        self.duration_time_text,
                        text=format_time(self.estimated_duration),
                        color=self.COL19  # Orange color
                    )
                
                # Update loading bar width based on scan progress
                if hasattr(self, 'loading_bar') and self.loading_bar.exists():
                    loading_width = (current / total) * self.progress_width
                    bui.imagewidget(self.loading_bar, size=(loading_width, 5))

    def create_hide_button(self):
        widgets = self.hide_widgets.append
        self.hide_icons = ['\u25bc', '\u25b2']
        self.hide_button = self.create_button(
            p=self.parent,
            pos=(20, 15),
            size=(50, 50),
            oac=self.toggle_hide,
            color=self.COL10
        )
        widgets(self.hide_button)
        self.hide_text = bui.textwidget(
            parent=self.parent,
            text=self.hide_icons[self.ui_hidden],
            position=(44, 30),
            scale=2,
            shadow=0.4,
            color=self.COL11
        )
        widgets(self.hide_text)
        widgets(bui.imagewidget(
            parent=self.parent,
            position=(18, 13),
            size=(54, 54),
            color=self.COL10,
            texture=bui.gettexture('white'),
            opacity=0.4
        ))

    def destroy_hide_button(self):
        [w.delete() for w in self.hide_widgets]
        self.hide_widgets.clear()

    def create_ui(self):
        """Modified to handle unknown duration initially"""
        self.ui_visible = True
        widgets = self.ui_widgets.append
        width, height = bui.get_virtual_screen_size()
        bar_height = self.bar_height
        parent = self.parent

        # Exit button
        widgets(self.create_button(
            p=parent,
            pos=(width - 65, 15),
            size=(50, 50),
            color=self.COL0,
            oac=self.exit
        ))
        color = self.COL1
        widgets(bui.imagewidget(
            parent=parent,
            texture=bui.gettexture('crossOut'),
            color=(color[0] * 10, color[1] * 10, color[2] * 10),
            position=(width - 60, 20),
            size=(40, 40)
        ))

        # Speed buttons
        for i in range(2):
            arrow = ['FAST_FORWARD_BUTTON', 'REWIND_BUTTON'][i]
            pos = (width - 130 - 260 * i, 15)
            widgets(self.create_button(
                p=parent,
                pos=pos,
                size=(50, 50),
                color=self.COL2,
                oac=CallPartial(self.change_speed, [1, -1][i]),
                repeat=True
            ))
            widgets(bui.textwidget(
                parent=parent,
                text=bui.charstr(getattr(bui.SpecialChar, arrow)),
                color=self.COL3,
                position=(pos[0] - 2, pos[1] + 13),
                h_align='center',
                v_align='center',
                scale=1.8,
                shadow=0.3
            ))

        # Seek buttons
        for i in range(2):
            arrow = ['RIGHT_ARROW', 'LEFT_ARROW'][i]
            pos = (width - 195 - 130 * i, 15)
            widgets(self.create_button(
                p=parent,
                pos=pos,
                size=(50, 50),
                color=self.COL4,
                oac=CallPartial(self.seek, [1, -1][i]),
                repeat=True
            ))
            widgets(bui.textwidget(
                parent=parent,
                text=bui.charstr(getattr(bui.SpecialChar, arrow)),
                color=self.COL5,
                position=(pos[0] - 1, pos[1] + 12),
                h_align='center',
                v_align='center',
                scale=1.7,
                shadow=0.2
            ))

        # Pause button
        pos = (width - 260, 15)
        widgets(self.create_button(
            p=parent,
            pos=pos,
            size=(50, 50),
            color=self.COL6,
            oac=self.toggle_pause
        ))
        self.pause_text = bui.textwidget(
            parent=parent,
            color=self.COL7,
            position=(pos[0] + 12, pos[1] + 11),
            scale=1.5,
            shadow=0.3
        )
        widgets(self.pause_text)
        self.toggle_pause(dry=True)

        # Restart button
        pos = (width - 455, 15)
        widgets(self.create_button(
            p=parent,
            pos=pos,
            size=(50, 50),
            color=self.COL12,
            oac=self.restart
        ))
        color = self.COL13
        scale = 1.5
        widgets(bui.imagewidget(
            parent=parent,
            texture=bui.gettexture('replayIcon'),
            color=(color[0] * scale, color[1] * scale, color[2] * scale),
            position=(pos[0] + 2, pos[1] + 1),
            size=(47, 47),
        ))

        # Progress bar
        pos = (285, bar_height / 2 - 2)
        self.progress_width = width - 790
        self.main_bar = bui.imagewidget(
            parent=parent,
            texture=bui.gettexture('white'),
            size=(self.progress_width, 5),
            position=pos,
            opacity=0.2 if self.scanning else 0.6,
            color=self.COL8
        )
        widgets(self.main_bar)

        # Secondary progress bar
        self.loading_bar = bui.imagewidget(
            parent=parent,
            texture=bui.gettexture('white'),
            size=(0, 5),
            position=pos,
            opacity=0.5,
            color=self.COL18
        )
        widgets(self.loading_bar)

        # Nub
        self.nub_pos = (pos[0] - 24, pos[1] - 22)
        self.nub = bui.imagewidget(
            parent=parent,
            texture=bui.gettexture('nub'),
            size=(50, 50),
            position=self.nub_pos,
            opacity=0.4,
            color=self.COL9
        )
        widgets(self.nub)

        # Time displays
        self.current_time_text = bui.textwidget(
            parent=parent,
            position=(155, 40),
            color=self.COL7,
            text=format_time(self.replay_time - self.start_time),
            maxwidth=100
        )
        widgets(self.current_time_text)
        
        # Duration display - alternates between scan% and estimated time while scanning
        self.duration_time_text = bui.textwidget(
            parent=parent,
            position=(155, 11),
            text='Scan 0%' if self.scanning else format_time(self.duration_sec),
            color=self.COL6,
            maxwidth=100
        )
        widgets(self.duration_time_text)

        # Seekbar sensors
        sensor_x, sensor_y = (285, 15)
        sensor_count = 100
        tile_width = self.progress_width / sensor_count
        for i in range(sensor_count):
            widgets(bui.buttonwidget(
                label='',
                parent=parent,
                position=(sensor_x + tile_width * i, sensor_y),
                size=(tile_width, 50),
                texture=bui.gettexture('empty'),
                enable_sound=False,
                on_activate_call=CallPartial(self.jump, i / sensor_count),
                selectable=False
            ))

        # Camera button
        widgets(self.create_button(
            p=self.parent,
            pos=(85, 15),
            size=(50, 50),
            color=self.COL14,
            oac=self.toggle_camera
        ))
        color = self.COL15
        scale = 1.5
        widgets(bui.imagewidget(
            parent=self.parent,
            texture=bui.gettexture('achievementOutline'),
            position=(88, 18),
            color=(color[0] * scale, color[1] * scale, color[2] * scale),
            size=(45, 45)
        ))

        # Info panel
        info_w, info_h = (443, 98)
        self.info_bg = bui.imagewidget(
            texture=bui.gettexture('white'),
            position=(width - 456, 100),
            parent=parent,
            size=(info_w, info_h),
            opacity=0
        )
        widgets(self.info_bg)
        self.info_title = bui.textwidget(
            position=(width - info_w + 182.5, info_h + 64),
            h_align='center',
            scale=1.2,
            parent=parent,
            maxwidth=info_w - 20
        )
        widgets(self.info_title)
        self.info_text = bui.textwidget(
            position=(width - info_w + 182.5, info_h + 10),
            h_align='center',
            parent=parent,
            maxwidth=info_w - 20
        )
        widgets(self.info_text)

    def create_camera_ui(self):
        widgets = self.camera_widgets.append
        cam_x, cam_y = (19, 100)
        self.camera_bg = bui.imagewidget(
            parent=self.parent,
            size=(235, 260),
            position=(cam_x, cam_y),
            texture=bui.gettexture('white'),
            color=self.COL14,
            opacity=0.05
        )
        widgets(self.camera_bg)

        self.camera_bg2 = bui.imagewidget(
            parent=self.parent,
            size=(235, 100),
            opacity=0.05,
            position=(cam_x, cam_y + 267),
            color=self.COL14,
            texture=bui.gettexture('white')
        )
        widgets(self.camera_bg2)
        self.fade_camera()
        widgets(bui.textwidget(
            parent=self.parent,
            h_align='center',
            v_align='center',
            text='To maintain animated\nsmooth camera, keep\nzoom at auto.',
            maxwidth=205,
            max_height=190,
            position=(cam_x + 92, cam_y + 300),
            color=self.COL15
        ))

        widgets(self.create_button(
            p=self.parent,
            label='Reset',
            color=self.COL14,
            textcolor=self.COL15,
            size=(205, 30),
            pos=(cam_x + 15, cam_y + 7),
            oac=self.reset_camera
        ))

        widgets(bui.imagewidget(
            parent=self.parent,
            size=(219, 2),
            position=(cam_x + 8, cam_y + 44),
            texture=bui.gettexture('white'),
            color=self.COL15,
            opacity=0.6
        ))

        widgets(self.create_button(
            p=self.parent,
            label='Look',
            pos=(cam_x + 15, cam_y + 53),
            color=self.COL14,
            textcolor=self.COL15,
            size=(205, 30),
            oac=self.look
        ))
        self.look_text = bui.textwidget(
            parent=self.parent,
            text=str(round_tuple(self.camera_look) if self.camera_look else 'players'),
            v_align='center',
            h_align='center',
            position=(cam_x + 92, cam_y + 90),
            color=self.COL14,
            maxwidth=205,
            max_height=40
        )
        widgets(self.look_text)
        widgets(bui.textwidget(
            parent=self.parent,
            text='Currently looking at:',
            v_align='center',
            h_align='center',
            position=(cam_x + 92, cam_y + 120),
            color=self.COL15,
            maxwidth=205,
            max_height=40
        ))

        widgets(bui.imagewidget(
            parent=self.parent,
            size=(219, 2),
            position=(cam_x + 8, cam_y + 154),
            texture=bui.gettexture('white'),
            color=self.COL15,
            opacity=0.6
        ))

        [widgets(self.create_button(
            p=self.parent,
            label=['-', '+'][i],
            pos=(cam_x + 13 + 113 * i, cam_y + 163),
            color=self.COL14,
            textcolor=self.COL15,
            size=(98, 30),
            repeat=True,
            oac=CallPartial(self.zoom, [1, -1][i])
        )) for i in [0, 1]]
        self.zoom_text = bui.textwidget(
            parent=self.parent,
            text=f'x{round(0.5 ** (self.camera_zoom - 1), 2)}' if self.camera_zoom != 1 else 'x1.0' if self.manual_zoom else 'auto',
            v_align='center',
            h_align='center',
            position=(cam_x + 92, cam_y + 200),
            color=self.COL14,
            maxwidth=205,
            max_height=40
        )
        widgets(self.zoom_text)
        widgets(bui.textwidget(
            parent=self.parent,
            text='Current zoom:',
            v_align='center',
            h_align='center',
            position=(cam_x + 92, cam_y + 227),
            color=self.COL15,
            maxwidth=205,
            max_height=40
        ))

    def zoom(self, direction):
        new_zoom = round(self.camera_zoom + direction * 0.05, 2)
        if self.camera_zoom == 1 and not self.manual_zoom:
            _ba.set_camera_manual(True)
            self.camera_pos = _ba.get_camera_position()
            self.camera_look = _ba.get_camera_target()
            bui.textwidget(self.look_text, text=str(round_tuple(self.camera_look)))
        if new_zoom == 1 and not self.manual_zoom:
            _ba.set_camera_manual(False)
            self.camera_look = None
            bui.textwidget(self.look_text, text='players')
        self.camera_zoom = new_zoom
        bui.textwidget(self.zoom_text, text=f'x{round(0.5 ** (new_zoom - 1), 2)}' if new_zoom != 1 else 'x1.0' if self.manual_zoom else 'auto')
        self.apply_zoom()

    def look(self):
        self.destroy_ui()
        self.destroy_hide_button()
        self.fade_hide_button(0.4, -0.1)
        self.look_backup = self.camera_look
        self.pos_backup = _ba.get_camera_position()
        self.manual_backup = self.manual_zoom
        self.create_cinema_sensors()
        self.create_cinema_ui()
        self.create_cinema_button()
        self.create_cinema_indicator()

    def update_look(self, dx, dy):
        origin = self.camera_look or _ba.get_camera_target()
        scale = 0.7 * self.camera_zoom
        self.camera_look = new_look = (origin[0] + dx * scale, origin[1] + dy * scale, origin[2])
        0 if self.cinema_mode else bui.textwidget(self.cinema_text, text=str(round_tuple(new_look)))
        self.camera_pos = _ba.get_camera_position()
        if self.camera_zoom != 1:
            self.manual_zoom = True
        self.camera_zoom = 1

    def start_focus(self):
        self.focus_timer = bui.AppTimer(0.01, self.focus, repeat=True)

    def focus(self):
        _ba.set_camera_target(*self.camera_look) if self.camera_look else 0

    def apply_zoom(self):
        if self.camera_zoom == 1 and not self.manual_zoom:
            return
        zoom = self.camera_zoom
        target_x, target_y, target_z = _ba.get_camera_target()
        pos_x, pos_y, pos_z = self.camera_pos
        new_pos_x = target_x + (pos_x - target_x) * zoom
        new_pos_y = target_y + (pos_y - target_y) * zoom
        new_pos_z = target_z + (pos_z - target_z) * zoom
        _ba.set_camera_position(new_pos_x, new_pos_y, new_pos_z)

    def stop_focus(self):
        self.focus_timer = None

    def save_cinema(self):
        self.exit_cinema()

    def exit_cinema(self):
        self.destroy_cinema()
        self.create_ui()
        self.create_hide_button()
        self.fade_hide_button(0, 0.1)
        self.update_progress_ui()

    def create_cinema_sensors(self):
        width, height = bui.get_virtual_screen_size()
        tile = 50
        cols = int(width / tile)
        rows = int(height / tile)
        half_cols = cols / 2
        half_rows = rows / 2
        [self.cinema_widgets.append(bui.buttonwidget(
            parent=self.parent,
            size=(tile, tile),
            position=(i * tile, j * tile),
            texture=bui.gettexture('empty'),
            enable_sound=False,
            on_activate_call=CallPartial(self.update_look, i - half_cols, j - half_rows),
            label='',
            repeat=True
        ))
        for i in range(cols)
        for j in range(rows)]

    def create_cinema_ui(self):
        widgets = self.cinema_ui_widgets.append
        widgets(bui.imagewidget(
            parent=self.parent,
            position=(0, 3),
            color=self.COL14,
            opacity=0.4,
            texture=bui.gettexture('white'),
            size=(232, 190)
        ))

        widgets(self.create_button(
            p=self.parent,
            pos=(14, 50),
            size=(204, 30),
            label='Target Players',
            color=self.COL14,
            textcolor=self.COL15,
            oac=self.target_players
        ))
        widgets(self.create_button(
            p=self.parent,
            pos=(10, 90),
            color=self.COL14,
            label='Cancel',
            size=(99, 30),
            textcolor=self.COL15,
            oac=self.cancel_cinema
        ))
        widgets(self.create_button(
            p=self.parent,
            pos=(123, 90),
            color=self.COL14,
            label='Save',
            size=(99, 30),
            textcolor=self.COL15,
            oac=self.save_cinema
        ))

        widgets(bui.textwidget(
            parent=self.parent,
            position=(90, 160),
            color=self.COL15,
            text='Currently looking at:',
            h_align='center',
            maxwidth=220
        ))
        self.cinema_text = bui.textwidget(
            parent=self.parent,
            position=(90, 130),
            color=self.COL14,
            h_align='center',
            text=str(round_tuple(self.camera_look) if self.camera_look else 'players')
        )
        widgets(self.cinema_text)

        widgets(bui.imagewidget(
            parent=self.parent,
            position=(0, 200),
            color=self.COL14,
            opacity=0.4,
            texture=bui.gettexture('white'),
            size=(232, 110)
        ))
        widgets(bui.textwidget(
            parent=self.parent,
            position=(90, 240),
            text='Longpress anywhere\nto look around. Tap on \nsomething to look at it.\nPause for calmer control!',
            h_align='center',
            v_align='center',
            maxwidth=225,
            max_height=105
        ))

        width, height = bui.get_virtual_screen_size()
        crosshair = 20
        [widgets(bui.imagewidget(
            parent=self.parent,
            position=(width / 2, height / 2 - crosshair / 2 + crosshair * 0.1) if i else (width / 2 - crosshair / 2, height / 2 + crosshair * 0.1),
            size=(3, crosshair * 1.15) if i else (crosshair * 1.15, 3),
            color=self.COL1,
            texture=bui.gettexture('white')
        )) for i in [0, 1]]

        offset = 60
        for j in range(2):
            widgets(bui.imagewidget(
                parent=self.parent,
                texture=bui.gettexture('white'),
                color=self.COL1,
                position=(width / 2 + [-offset, offset - crosshair][j], height / 2 + offset),
                size=(crosshair * 1.1, 3)
            ))

        for j in range(2):
            widgets(bui.imagewidget(
                parent=self.parent,
                texture=bui.gettexture('white'),
                color=self.COL1,
                position=(width / 2 + offset, height / 2 + [offset - crosshair, -offset + crosshair * 0.3][j]),
                size=(3, crosshair * +1.1)
            ))

        for j in range(2):
            widgets(bui.imagewidget(
                parent=self.parent,
                texture=bui.gettexture('white'),
                color=self.COL1,
                position=(width / 2 + [-offset, offset - crosshair][j], height / 2 - crosshair / 2 - offset + crosshair * 0.8),
                size=(crosshair * 1.1, 3)
            ))

        for j in range(2):
            widgets(bui.imagewidget(
                parent=self.parent,
                texture=bui.gettexture('white'),
                color=self.COL1,
                position=(width / 2 - offset, height / 2 + [offset - crosshair, -offset + crosshair * 0.3][j]),
                size=(3, crosshair * 1.1)
            ))

    def destroy_cinema_ui(self):
        [w.delete() for w in self.cinema_ui_widgets]

    def toggle_cinema_hide(self):
        if getattr(self, 'cinema_busy', 0):
            return
        self.cinema_mode = not self.cinema_mode
        self.cinema_busy = True
        if self.cinema_mode:
            self.animate_cinema(204, 14, -1)
            bui.buttonwidget(self.cinema_button, label=bui.charstr(bui.SpecialChar.UP_ARROW))
            self.destroy_cinema_ui()
        else:
            bui.buttonwidget(self.cinema_button, texture=bui.gettexture('white'))
            self.animate_cinema(36, 7, 1)
            bui.imagewidget(self.cinema_indicator, opacity=0)

    def create_cinema_indicator(self):
        self.cinema_indicator = bui.imagewidget(
            parent=self.parent,
            position=(7, 8),
            color=self.COL14,
            opacity=0,
            size=(36, 33),
            texture=bui.gettexture('white')
        )
        self.cinema_widgets.append(self.cinema_indicator)

    def create_cinema_button(self):
        self.cinema_button = self.create_button(
            p=self.parent,
            pos=(14, 10),
            color=self.COL14,
            label='Cinema Mode',
            size=(204, 30),
            textcolor=self.COL15,
            oac=self.toggle_cinema_hide
        )
        self.cinema_widgets.append(self.cinema_button)

    def animate_cinema(self, width_val, x_val, direction):
        width_val += (163 / 35) * direction
        x_val += 0.2 * direction
        bui.buttonwidget(self.cinema_button, size=(width_val, 30), position=(x_val, 10))
        if not (14 >= x_val >= 7):
            self.cinema_busy = False
            if self.cinema_mode:
                bui.buttonwidget(self.cinema_button, texture=bui.gettexture('empty'))
                bui.imagewidget(self.cinema_indicator, opacity=0.4)
            else:
                self.create_cinema_ui()
                self.cinema_button.delete()
                self.create_cinema_button()
                bui.buttonwidget(self.cinema_button, label='Cinema Mode')
            return
        bui.apptimer(0.004, CallPartial(self.animate_cinema, width_val, x_val, direction))

    def destroy_cinema(self):
        self.destroy_cinema_ui()
        [w.delete() for w in self.cinema_widgets]

    def get_all_widgets(self):
        return self.get_deletable_widgets() + self.hide_widgets + self.cinema_widgets

    def target_players(self):
        self.camera_look = None
        bui.textwidget(self.cinema_text, text='players')
        if self.camera_zoom != 1 or self.manual_zoom:
            self.camera_zoom = 1
            self.manual_zoom = False
            _ba.set_camera_manual(False)

    def cancel_cinema(self):
        self.camera_look = self.look_backup
        self.camera_pos = self.pos_backup
        self.manual_zoom = self.manual_backup
        if self.camera_zoom != 1 or self.manual_zoom:
            _ba.set_camera_manual(True)
            _ba.set_camera_position(*self.camera_pos)
        self.exit_cinema()

    def toggle_camera(self):
        if self.camera_on:
            self.camera_on = False
            [w.delete() for w in self.camera_widgets]
            self.camera_widgets.clear()
            self.fade_camera(0.4, -0.1)
        else:
            self.camera_on = True
            self.create_camera_ui()

    def reset_camera(self):
        _ba.set_camera_manual(False)
        self.camera_look = None
        self.manual_zoom = False
        self.camera_zoom = 1
        bui.textwidget(self.look_text, text='players')
        bui.textwidget(self.zoom_text, text='auto')

    def fade_camera(self, opacity=0, delta=0.1):
        if opacity > 0.4 or opacity < 0:
            if delta < 0:
                self.camera_bg.delete()
            return
        if not self.camera_bg.exists():
            return
        bui.imagewidget(self.camera_bg, opacity=opacity)
        bui.imagewidget(self.camera_bg2, opacity=opacity)
        bui.apptimer(0.02, CallPartial(self.fade_camera, opacity + delta, delta))

    def restart(self):
        self.loop()
        self.fix_pause()
        self.show_message('Replay', f'Version {Replay.VER} BETA', self.COL12, self.COL13)

    def destroy_ui(self):
        self.ui_visible = self.camera_on = False
        [w.delete() for w in self.get_deletable_widgets()]
        self.ui_widgets.clear()
        self.camera_widgets.clear()

    def get_deletable_widgets(self):
        return self.ui_widgets + self.camera_widgets

    def toggle_hide(self):
        if getattr(self, 'hide_busy', 0):
            return
        self.hide_busy = True
        if getattr(self, 'exit_timer', 0) and getattr(self, 'exit_ready', 0):
            self.exit_ready = self.exit_timer = False
        self.info_timer = None
        self.ui_hidden = hidden = not self.ui_hidden
        bui.textwidget(self.hide_text, text=self.hide_icons[hidden])
        if hidden:
            bui.apptimer(0.2, lambda: bui.buttonwidget(self.hide_button, texture=bui.gettexture('empty')))
            self.fade_hide_button(0.4, -0.05)
            self.destroy_ui()
        else:
            bui.buttonwidget(self.hide_button, texture=bui.gettexture('white'))
            self.fade_hide_button(0, 0.05)
            self.create_ui()
            self.update_progress_ui()
        bui.apptimer(0.21, CallPartial(setattr, self, 'hide_busy', 0))

    def fade_hide_button(self, opacity=0, delta=0.1):
        if opacity > 0.4 or opacity < 0:
            return
        if not self.background.exists():
            return
        bui.imagewidget(self.background, opacity=opacity)
        bui.apptimer(0.02, CallPartial(self.fade_hide_button, opacity + delta, delta))

    def show_message(self, title, text, color1, color2):
        if getattr(self, 'exit_timer', 0) and getattr(self, 'exit_ready', 0):
            self.exit_ready = self.exit_timer = False
        self.info_timer = None
        bui.imagewidget(self.info_bg, color=color1)
        bui.textwidget(self.info_title, text=title, color=color2)
        bui.textwidget(self.info_text, text=text, color=color2)
        self.fade_info()
        self.info_timer = bui.AppTimer(1.5, self.hide_message)

    def hide_message(self):
        self.fade_info(0.7, -0.1)
        [bui.textwidget(w, text='') for w in [self.info_title, self.info_text] if w.exists()]

    def fade_info(self, opacity=0, delta=0.1):
        if opacity > 0.7 or opacity < 0:
            return
        if not self.info_bg.exists():
            return
        bui.imagewidget(self.info_bg, opacity=opacity)
        bui.apptimer(0.02, CallPartial(self.fade_info, opacity + delta, delta))

    def toggle_pause(self, dry=False, silent=False):
        if not dry:
            self.paused = not self.paused
        icon = bui.charstr(getattr(bui.SpecialChar, ['PAUSE', 'PLAY'][self.paused] + '_BUTTON'))
        bui.textwidget(self.pause_text, text=icon)
        if not dry:
            if not silent:
                self.show_message(['Resume', 'Pause'][self.paused], os.path.basename(self.path) + f' of {os.path.getsize(self.path)} bytes', self.COL6, self.COL7)
            if self.paused:
                self.stop()
                bs.pause_replay()
            else:
                self.play()
                bs.resume_replay()

    def fix_pause(self):
        if not self.paused:
            return
        self.toggle_pause(silent=True)
        bui.apptimer(0.02, CallPartial(self.toggle_pause, silent=True))

    def update_clock(self):
        current = time()
        elapsed = current - self.real_time
        self.real_time = current
        self.replay_time += elapsed * self.speed

    def change_speed(self, direction):
        new_exp = bs.get_replay_speed_exponent() + direction
        bs.set_replay_speed_exponent(new_exp)
        self.speed = 2 ** new_exp
        label = 'Snail Mode' if self.speed == 0.0625 else 'Slow Motion' if self.speed < 1 else 'Quake Pro' if self.speed == 16 else 'Fast Motion' if self.speed > 1 else 'Normal Speed'
        self.show_message(label, f'Current exponent: x{self.speed}', self.COL2, self.COL3)

    def play(self):
        self.real_time = time()
        self.update_clock()
        self.start_progress_timer()
        self.clock_timer = bui.AppTimer(self.TICK, self.update_clock, repeat=True)

    def stop(self):
        self.clock_timer = None
        self.stop_progress_timer()

    def stop_progress_timer(self):
        self.progress_timer = None

    def start_progress_timer(self):
        self.progress_timer = bui.AppTimer(self.TICK, self.update_progress_ui, repeat=True)

    def seek(self, direction):
        """Seek with confirmed duration checking"""
        label = ['Forward by', 'Rewind by'][direction == -1]
        amount = direction * self.speed
        
        # Use estimated duration for calculating seek amount
        if self.scanning:
            seek_base = self.estimated_duration
        else:
            seek_base = self.duration_sec
        
        amount = (seek_base / 20) * amount
        new_time = (self.replay_time - self.start_time) + amount
        
        # Check if trying to seek beyond confirmed duration while scanning
        if self.scanning and new_time > self.confirmed_duration_sec:
            current, total = self.scan_progress
            percent = int((current / total) * 100) if total > 0 else 0
            self.show_message('Buffering...', f'{percent}% loaded', self.COL2, self.COL3)
            return
        
        # Use appropriate duration for loop check
        max_duration = self.confirmed_duration_sec if self.scanning else self.duration_sec
        
        if (new_time >= max_duration) or (new_time <= 0):
            self.loop()
        else:
            self.start_time = self.replay_time - new_time
            self.reset_replay()
            bs.seek_replay(new_time)
        
        self.real_time = time()
        self.fix_pause()
        amount = abs(round(amount, 2))
        self.show_message('Seek', label + f" {amount} second{['s', ''][amount == 1]}", self.COL4, self.COL5)
    
    def jump(self, percent):
        """Jump with WYSIWYG behavior - percent is based on ESTIMATED duration, checked against CONFIRMED"""
        # Calculate target time based on ESTIMATED duration (what user sees on bar)
        if self.scanning:
            target_time = self.estimated_duration * percent
        else:
            target_time = self.duration_sec * percent
        
        # Check if trying to jump beyond CONFIRMED duration while scanning
        if self.scanning and target_time > self.confirmed_duration_sec:
            current, total = self.scan_progress
            scan_percent = int((current / total) * 100) if total > 0 else 0
            self.show_message('Buffering...', f'{scan_percent}% loaded', self.COL2, self.COL3)
            return
        
        self.start_time = self.replay_time - target_time
        self.reset_replay()
        bs.seek_replay(target_time)
        self.real_time = time()
        self.fix_pause()

    def exit(self):
        if getattr(self, 'exit_ready', 0):
            self.confirm_exit()
            return
        self.show_message('Exit', 'Press again to confirm', self.COL0, self.COL1)
        self.exit_ready = True
        self.exit_timer = bui.AppTimer(1.5, CallPartial(setattr, self, 'exit_ready', False))

    def confirm_exit(self):
        bui.fade_screen(0, time=0.75, endcall=CallPartial(bui.fade_screen, 1, time=0.75))
        bui.getsound('deek').play()
        return_to_menu()
        self.stop()
        self.stop_focus()
        self.exit_timer = None
        _ba.set_camera_manual(False)

    def update_progress_ui(self):
        """Modified to handle scanning state with growing progress bar"""
        elapsed = self.replay_time - self.start_time
        
        # Determine the current max duration to check against
        if self.scanning:
            max_duration = self.estimated_duration
        elif self.duration_sec:
            max_duration = self.duration_sec
        else:
            max_duration = None
        
        # Check if elapsed exceeds duration and loop if needed
        if max_duration and elapsed >= max_duration:
            self.loop()
            elapsed = 0  # Reset elapsed after loop
        
        nub_x, nub_y = self.nub_pos
        
        # Calculate progress
        if self.scanning:
            # Use estimated duration for progress bar
            if elapsed < self.estimated_duration:
                progress = (elapsed / self.estimated_duration) * self.progress_width
            else:
                # Cap at 100% if somehow elapsed exceeds estimate
                progress = self.progress_width
        elif not self.duration_sec:
            # Fallback if scan failed
            progress = min(elapsed / max(elapsed, 1) * self.progress_width * 0.1, self.progress_width * 0.1)
        else:
            # Normal progress calculation, cap at 100%
            progress = min((elapsed / self.duration_sec) * self.progress_width, self.progress_width)
        
        try:
            bui.imagewidget(self.nub, position=(nub_x + progress, nub_y))
            bui.textwidget(self.current_time_text, text=format_time(elapsed))
        except ReferenceError:
            pass

    def reset_replay(self):
        bs.seek_replay(-10 ** 10)

    def loop(self):
        self.start_time = self.replay_time = 0
        self.reset_replay()

    def create_button(self, label='', p=None, oac=None, pos=None, texture='white', **kwargs):
        return bui.buttonwidget(
            parent=p,
            on_activate_call=oac,
            position=pos,
            label=label,
            texture=bui.gettexture(texture),
            enable_sound=False,
            **kwargs
        )

# Tools
def get_ui_scale(small, medium, large=None):
    scale = bui.app.ui_v1.uiscale
    return small if scale is bui.UIScale.SMALL else medium if scale is bui.UIScale.MEDIUM else (large or medium)
return_to_menu = lambda: bui.app.classic.return_to_main_menu_session_gracefully(reset_ui=False)
show_warning = lambda text: (bui.getsound('block').play() or 1) and bui.screenmessage(text, color=(1, 1, 0))
format_time = lambda seconds: strftime('%H:%M:%S', gmtime(seconds))
get_overlay_stack = lambda: bui.get_special_widget('overlay_stack')
round_tuple = lambda tup: type(tup)([round(val, 1) for val in tup])

# pybrp
Z = lambda _:[0]*_
G_FREQS = lambda: [
    101342,9667,3497,1072,0,3793,*Z(2),2815,5235,*Z(3),3570,*Z(3),
    1383,*Z(3),2970,*Z(2),2857,*Z(8),1199,*Z(30),
    1494,1974,*Z(12),1351,*Z(122),1475,*Z(65)
]
class _Huffman:
    class _N:
        def __init__(self):
            self.l,self.r,self.p,self.f=-1,-1,0,0
    def __init__(self):
        self.nodes=[self._N()for _ in range(511)]
        gf = G_FREQS()
        for i in range(256):self.nodes[i].f=gf[i]
        nc=256
        while nc<511:
            s1,s2=-1,-1
            i=0
            while self.nodes[i].p!=0:i+=1
            s1=i;i+=1
            while self.nodes[i].p!=0:i+=1
            s2=i;i+=1
            while i<nc:
                if self.nodes[i].p==0:
                    if self.nodes[s1].f>self.nodes[s2].f:
                        if self.nodes[i].f<self.nodes[s1].f:s1=i
                    elif self.nodes[i].f<self.nodes[s2].f:s2=i
                i+=1
            self.nodes[nc].f=self.nodes[s1].f+self.nodes[s2].f
            self.nodes[s1].p=self.nodes[s2].p=nc-255
            self.nodes[nc].r,self.nodes[nc].l=s1,s2
            nc+=1
    def decompress(self,src):
        if not src:return b''
        rem,comp=src[0]&15,src[0]>>7
        if not comp:return src
        out,ptr,l=bytearray(),src[1:],len(src)
        bl=((l-1)*8)-rem;bit=0
        while bit<bl:
            m_bit=(ptr[bit>>3]>>(bit&7))&1;bit+=1
            if m_bit:
                n=510
                while n>=256:
                    if bit>=bl:raise ValueError("Incomplete Huffman code")
                    p_bit=(ptr[bit>>3]>>(bit&7))&1;bit+=1
                    n=self.nodes[n].l if p_bit==0 else self.nodes[n].r
                out.append(n)
            else:
                if bit+8>bl:break
                bi,b_in_b=bit>>3,bit&7
                val=ptr[bi]if b_in_b==0 else(ptr[bi]>>b_in_b)|(ptr[bi+1]<<(8-b_in_b))
                out.append(val&255);bit+=8
        return bytes(out)
def get_replay_duration(_h, brp_path, progress):
    total_ms = 0
    with open(brp_path, 'rb') as f:
        f.seek(0,2)
        progress[1] = f.tell()
        f.seek(6)
        while True:
            progress[0] = f.tell()
            b_data = f.read(1)
            if not b_data:
                break
            b1, comp_len = b_data[0], 0
            if b1 < 254:
                comp_len = b1
            elif b1 == 254:
                comp_len = int.from_bytes(f.read(2), 'little')
            else:
                comp_len = int.from_bytes(f.read(4), 'little')
            if comp_len == 0:
                continue
            raw_msg = _h.decompress(f.read(comp_len))
            if not raw_msg or raw_msg[0] != 1:
                continue
            sub_off = 1
            while sub_off + 2 <= len(raw_msg):
                sub_size_bytes = raw_msg[sub_off:sub_off+2]
                if len(sub_size_bytes) < 2:
                    break
                sub_size = int.from_bytes(sub_size_bytes, 'little')
                sub_off += 2
                if sub_off + sub_size > len(raw_msg):
                    break
                sub_data = raw_msg[sub_off:sub_off+sub_size]
                if len(sub_data) >= 2 and sub_data[0] == 0:
                    total_ms += sub_data[1]
                sub_off += sub_size
    progress[0] = progress[1]
    return total_ms

# brobord collide grass
# ba_meta require api 9
# ba_meta export babase.Plugin
class byBordd(Plugin):
    has_settings_ui = lambda c=0: True
    show_settings_ui = lambda c=0, w=None: Replay(source=w)
    def __init__(self):
        from bauiv1lib.ingamemenu import InGameMenuWindow as ingame
        orig_refresh = getattr(ingame, '_refresh_in_game')
        setattr(ingame, '_refresh_in_game', lambda window, *args, **kwargs: (self.add_button(window), orig_refresh(window, *args, **kwargs))[1])
        from bauiv1lib.watch import WatchWindow as watch
        orig_init = getattr(watch, '__init__')
        setattr(watch, '__init__', lambda window, *args, **kwargs: (orig_init(window, *args, **kwargs), self.add_button(window, 1))[0])

    def add_button(self, window, watch_mode=0):
        if watch_mode:
            btn_x = window._width / 2 + get_ui_scale(window._scroll_width * -0.5 + 93, 0) + 100
            btn_y = window.yoffs - get_ui_scale(63, 10) - 25
        self.button = Replay.create_button(
            Replay,
            p=window._root_widget,
            label='Replay',
            pos=(btn_x, btn_y) if watch_mode else (-70, 0),
            icon=bui.gettexture('replayIcon'),
            iconscale=1.6 if watch_mode else 0.8,
            size=(140, 50) if watch_mode else (90, 35),
            oac=lambda: Replay(source=self.button),
            id='Replay'
        )
