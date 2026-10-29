# ba_meta require api 9
import babase
import bascenev1 as bs
import math
import random

from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.actor.powerupbox import PowerupBox, PowerupBoxFactory

# Safely import all alien plugin modules
try:
    import xlr8
    import heatblast
    import fourarms
    import cannonball
    import goop
except ImportError as e:
    print(f"OMNITRIX CORE: Failed to load alien modules. Error: {e}")

class OmnitrixManager:
    def __init__(self, spaz: Spaz):
        self.spaz = spaz
        self.active = True
        self.state = "HUMAN" 
        self.battery = 100.0
        self.alien_index = 0
        
        self.aliens = ["XLR8", "Fourarms", "Heatblast", "Cannonball", "Goop"]
        self.current_alien = "Human"
        
        self.power_active = False
        self.power_end_time = 0.0
        
        self.cooldown_timers = {
            "XLR8": -999.0,
            "Fourarms": -999.0,
            "Heatblast": -999.0,
            "Cannonball": -999.0,
            "Goop": -999.0
        }
        
        self.is_recharging = False 
        self.recharge_end_time = 0.0
        
        self.last_punch = 0.0
        self.last_pickup = 0.0
        self.last_jump = 0.0
        self.last_bomb = 0.0
        
        self.jump_held = False 
        self.double_tap_window = 0.4 
        
        self.last_pos = None
        self.last_angles = []
        self.aura_light = None
        
        # UI Fade Trackers
        self.instruction_opacity = 1.0
        self.idle_time = 0.0
        
        self.update_timer = bs.Timer(0.03, babase.WeakCallStrict(self.update), repeat=True)

        # Top Text Node (Battery & Alien Name)
        self.text_node = bs.newnode('math', owner=self.spaz.node, attrs={
            'input1': (0, 1.3, 0), 'operation': 'add'})
        self.spaz.node.connectattr('torso_position', self.text_node, 'input2')
        self.battery_text = bs.newnode('text', owner=self.spaz.node, attrs={
            'text': '', 'in_world': True, 'color': (0, 1, 0),
            'scale': 0.015, 'h_align': 'center'})
        self.text_node.connectattr('output', self.battery_text, 'position')
        
        # Bottom Text Node (Dynamic Instructions)
        self.info_node = bs.newnode('math', owner=self.spaz.node, attrs={
            'input1': (0, -0.6, 0), 'operation': 'add'})
        self.spaz.node.connectattr('torso_position', self.info_node, 'input2')
        self.info_text = bs.newnode('text', owner=self.spaz.node, attrs={
            'text': '', 'in_world': True, 'color': (1, 1, 1),
            'opacity': 1.0, 'scale': 0.012, 'h_align': 'center'})
        self.info_node.connectattr('output', self.info_text, 'position')
        
    def _save_original_meshes(self):
        if hasattr(self, 'orig_head_mesh'): return
        self.orig_color = getattr(self.spaz.node, 'color', (1, 1, 1))
        self.orig_highlight = getattr(self.spaz.node, 'highlight', (1, 1, 1))
        self.orig_head_mesh = self.spaz.node.head_mesh
        self.orig_torso_mesh = self.spaz.node.torso_mesh
        self.orig_pelvis_mesh = self.spaz.node.pelvis_mesh
        self.orig_upper_arm_mesh = self.spaz.node.upper_arm_mesh
        self.orig_forearm_mesh = self.spaz.node.forearm_mesh
        self.orig_upper_leg_mesh = self.spaz.node.upper_leg_mesh
        self.orig_lower_leg_mesh = self.spaz.node.lower_leg_mesh
        self.orig_toes_mesh = self.spaz.node.toes_mesh
        self.orig_color_tex = self.spaz.node.color_texture
        self.orig_color_mask_tex = self.spaz.node.color_mask_texture
        
        self.orig_hockey = getattr(self.spaz.node, 'hockey', False)

    def _apply_mesh(self, name):
        n = self.spaz.node
        if not n: return
        def safe_tex(attr, tex_name):
            try: setattr(n, attr, bs.gettexture(tex_name))
            except Exception: pass
        def safe_mesh(attr, mesh_name):
            try: setattr(n, attr, bs.getmesh(mesh_name))
            except Exception: pass
        safe_tex('color_texture', name + 'Color') 
        safe_tex('color_mask_texture', name + 'ColorMask')
        safe_mesh('head_mesh', name + 'Head')
        safe_mesh('torso_mesh', name + 'Torso')
        safe_mesh('pelvis_mesh', name + 'Pelvis')
        safe_mesh('upper_arm_mesh', name + 'UpperArm')
        safe_mesh('forearm_mesh', name + 'ForeArm')
        safe_mesh('upper_leg_mesh', name + 'UpperLeg')
        safe_mesh('lower_leg_mesh', name + 'LowerLeg')
        safe_mesh('toes_mesh', name + 'Toes')

    def _apply_aura(self, color, intensity, radius):
        if self.aura_light and self.aura_light.exists():
            self.aura_light.delete()
            self.aura_light = None
        if not self.spaz.node: return
        self.aura_light = bs.newnode('light', owner=self.spaz.node, attrs={
            'color': color, 'intensity': intensity, 'radius': radius, 'volume_intensity_scale': 0.1
        })
        self.spaz.node.connectattr('torso_position', self.aura_light, 'position')

    def handle_punch(self):
        t = bs.time()
        if t - self.last_punch < self.double_tap_window:
            if self.state == "TRANSFORMED" and self.current_alien == "Fourarms":
                fourarms.handle_punch(self)
                self.last_punch = 0.0
                return True
        self.last_punch = t
        if self.state == "CORE_OPEN":
            self.alien_index = (self.alien_index + 1) % len(self.aliens)
            self.update_ui()
            return True
        return False

    def handle_pickup(self):
        t = bs.time()
        if t - self.last_pickup < self.double_tap_window:
            if self.state in ["HUMAN", "CORE_OPEN"]:
                self.toggle_core()
                self.last_pickup = 0.0
                return True
            elif self.state == "TRANSFORMED":
                self.detransform()
                self.last_pickup = 0.0
                return True
        self.last_pickup = t
        return False

    def handle_jump(self):
        t = bs.time()
        if t - self.last_jump < self.double_tap_window:
            if self.state == "CORE_OPEN":
                self.transform()
                self.last_jump = 0.0
                return True
            elif self.state == "TRANSFORMED":
                if self.power_active:
                    self.deactivate_power()
                    self.last_jump = 0.0
                    return True
                else:
                    self.activate_power()
                    self.last_jump = 0.0
                    return True
        self.last_jump = t
        
        if self.state == "TRANSFORMED" and self.power_active:
            if self.current_alien == "Fourarms":
                fourarms.handle_jump(self)
                return True
        return False

    def handle_bomb(self):
        t = bs.time()
        if t - self.last_bomb < self.double_tap_window:
            if self.state == "TRANSFORMED" and self.current_alien == "Heatblast":
                heatblast.handle_bomb(self)
                self.last_bomb = 0.0
                return True
                
        self.last_bomb = t
        if self.state == "CORE_OPEN":
            self.alien_index = (self.alien_index - 1) % len(self.aliens)
            self.update_ui()
            return True

        if self.state == "TRANSFORMED":
            if self.current_alien == "Goop":
                goop.handle_bomb(self)
            return True
        return False

    def toggle_core(self):
        if self.is_recharging:
            if self.battery <= 8.0:
                bs.broadcastmessage("OMNITRIX RECHARGING (PLEASE WAIT)", color=(1, 0.5, 0), transient=True)
                bs.getsound('error').play(position=self.spaz.node.position)
                return
        if self.battery <= 8.0:
            bs.broadcastmessage("BATTERY LOW (UNDER 8%)", color=(1, 0, 0), transient=True)
            bs.getsound('error').play(position=self.spaz.node.position)
            return
        self.state = "CORE_OPEN" if self.state == "HUMAN" else "HUMAN"
        bs.getsound('click01').play(position=self.spaz.node.position)
        self.update_ui()

    def transform(self):
        if self.battery <= 8.0:
            bs.broadcastmessage("BATTERY LOW! (UNDER 8%)", color=(1, 0, 0), transient=True)
            bs.getsound('error').play(position=self.spaz.node.position)
            self.state = "HUMAN"
            self.update_ui()
            return

        self.state = "TRANSFORMED"
        self.current_alien = self.aliens[self.alien_index]
        bs.getsound('shieldUp').play(position=self.spaz.node.position)
        
        if self.spaz.node:
            self._save_original_meshes()
            
            if self.current_alien == "Fourarms":
                fourarms.equip(self)
            elif self.current_alien == "XLR8":
                xlr8.equip(self)
            elif self.current_alien == "Heatblast":
                heatblast.equip(self)
            elif self.current_alien == "Cannonball":
                cannonball.equip(self)
            elif self.current_alien == "Goop":
                goop.equip(self)
                    
        self.update_ui()

    def detransform(self):
        self.state = "HUMAN"
        self.is_recharging = True
        self.recharge_end_time = bs.time() + 1.0 
        self.current_alien = "Human"
        self.deactivate_power_effects()
        
        if self.spaz.node:
            self.spaz.node.color = getattr(self, 'orig_color', (1,1,1))
            if hasattr(self, 'orig_hockey'):
                self.spaz.node.hockey = self.orig_hockey
            if hasattr(self.spaz.node, 'highlight'):
                self.spaz.node.highlight = getattr(self, 'orig_highlight', (1,1,1))
            if hasattr(self, 'orig_head_mesh'):
                self.spaz.node.head_mesh = self.orig_head_mesh
                self.spaz.node.torso_mesh = self.orig_torso_mesh
                self.spaz.node.pelvis_mesh = self.orig_pelvis_mesh
                self.spaz.node.upper_arm_mesh = self.orig_upper_arm_mesh
                self.spaz.node.forearm_mesh = self.orig_forearm_mesh
                self.spaz.node.upper_leg_mesh = self.orig_upper_leg_mesh
                self.spaz.node.lower_leg_mesh = self.orig_lower_leg_mesh
                self.spaz.node.toes_mesh = self.orig_toes_mesh
                self.spaz.node.color_texture = self.orig_color_tex
                self.spaz.node.color_mask_texture = self.orig_color_mask_tex
                
            bs.getsound('shieldDown').play(position=self.spaz.node.position)
        self.update_ui()

    def activate_power(self):
        t = bs.time()
        if t < self.cooldown_timers[self.current_alien]:
            rem_cd = int(math.ceil(self.cooldown_timers[self.current_alien] - t))
            bs.broadcastmessage(f"{self.current_alien} COOLDOWN: {rem_cd}s", color=(1, 0, 0), transient=True)
            bs.getsound('error').play(position=self.spaz.node.position)
            return
            
        self.power_active = True
        self.power_end_time = t + 10.0
        self.cooldown_timers[self.current_alien] = t + 4.0 
        
        bs.broadcastmessage(f"{self.current_alien} POWER ACTIVATED!", color=(0, 1, 0), transient=True)
        bs.getsound('sparkle01').play(position=self.spaz.node.position)
        
        if self.current_alien == "XLR8":
            xlr8.activate_power(self)
        elif self.current_alien == "Cannonball":
            cannonball.activate_power(self)

    def deactivate_power(self):
        if not self.power_active: return
        self.deactivate_power_effects()
        bs.broadcastmessage(f"{self.current_alien} POWER DEACTIVATED!", color=(1, 0.5, 0), transient=True)
        bs.getsound('shieldDown').play(position=self.spaz.node.position)

    def deactivate_power_effects(self):
        self.power_active = False
        if self.aura_light and self.aura_light.exists():
            self.aura_light.delete()
            self.aura_light = None
            
        if self.state == "TRANSFORMED" and self.current_alien == "Heatblast":
            heatblast.apply_aura(self)

    def update(self):
        if not self.spaz.node:
            self.update_timer = None
            return
            
        t = bs.time()
        
        if self.is_recharging and t >= self.recharge_end_time:
            if self.battery > 8.0:
                self.is_recharging = False
                bs.getsound('ding').play(position=self.spaz.node.position)
                self.update_ui() 
        
        if self.state == "TRANSFORMED":
            self.battery -= 0.033 
            if self.battery <= 8.0:
                self.battery_text.color = (1, 0, 0)
                if int(t * 5) % 2 == 0:
                    self.spaz.node.color = (1, 0, 0)
                else:
                    self.spaz.node.color = (0.2, 0.2, 0.2)
            if self.battery <= 0:
                self.battery = 0
                self.detransform()
                
            if self.current_alien == "Heatblast" and random.random() < 0.06:
                bs.emitfx(position=self.spaz.node.position, velocity=(0, 2, 0), count=1, scale=1.0, spread=0.2, chunk_type='spark')
        else:
            if self.battery < 100.0:
                self.battery = min(100.0, self.battery + 0.075)
                if self.battery == 100.0:
                    self.update_ui()
                
        if self.power_active and t >= self.power_end_time:
            self.deactivate_power_effects()
            bs.broadcastmessage(f"{self.current_alien} POWER EXPIRED! (COOLDOWN 4s)", color=(1, 0.5, 0), transient=True)
                
        # --- ALIEN PHYSICS DELEGATION ---
        pos = self.spaz.node.position
        vel = self.spaz.node.velocity
        move_lr = getattr(self.spaz.node, 'move_left_right', 0.0)
        move_ud = getattr(self.spaz.node, 'move_up_down', 0.0)
        input_mag = math.hypot(move_lr, move_ud)
        
        # Passive Aliens
        if self.current_alien == "Goop":
            goop.update_physics(self, pos, vel, input_mag, move_lr, move_ud)
        elif self.current_alien == "Cannonball":
            cannonball.update_physics(self, pos, vel, input_mag, move_lr, move_ud)
        elif self.current_alien == "XLR8":
            xlr8.update_physics(self, pos, vel, input_mag, move_lr, move_ud)
            
        # Active-Only Aliens
        elif self.power_active:
            if self.current_alien == "Heatblast":
                heatblast.update_physics(self, pos, vel, input_mag, move_lr, move_ud)
            elif self.current_alien == "Fourarms":
                fourarms.update_physics(self, pos, vel, input_mag, move_lr, move_ud)

        self.update_ui(input_mag)

    def update_ui(self, input_mag=0.0):
        # 1. Update Battery HUD
        if self.battery_text: 
            if self.is_recharging:
                self.battery_text.text = f"RECHARGING... {int(self.battery)}%"
                if self.battery > 8.0:
                    if int(bs.time() * 5) % 2 == 0:
                        self.battery_text.color = (1, 0, 0)
                    else:
                        self.battery_text.color = (0, 1, 0)
                else:
                    self.battery_text.color = (1, 0.5, 0)
            elif self.state == "HUMAN":
                self.battery_text.text = f"OMNITRIX READY\nBATTERY: {int(self.battery)}%"
                self.battery_text.color = (0, 1, 0)
            elif self.state == "CORE_OPEN":
                self.battery_text.text = f"< {self.aliens[self.alien_index]} >"
                self.battery_text.color = (0, 1, 0)
            elif self.state == "TRANSFORMED":
                self.battery_text.text = f"{self.current_alien}\nBATTERY: {int(self.battery)}%"

        # 2. Update Instructions HUD with Fading Logic
        if not hasattr(self, 'info_text') or not self.info_text: return
        
        # Determine Fade Opacity
        if input_mag > 0.1:
            self.idle_time = 0.0
            # Fade out over exactly 1 second (subtracting 0.03 every 0.03s tick)
            self.instruction_opacity = max(0.0, self.instruction_opacity - 0.03)
        else:
            self.idle_time += 0.03
            # Wait 0.5 seconds before fading back in
            if self.idle_time >= 0.5:
                # Fade in smoothly over ~0.3 seconds
                self.instruction_opacity = min(1.0, self.instruction_opacity + 0.1)
                
        # Determine Text & Base Color
        target_text = ""
        target_color = (1, 1, 1)
            
        if self.is_recharging:
            target_text = ""
        elif self.state == "HUMAN":
            target_text = "DOUBLE PICKUP TO OPEN OMNITRIX CORE"
            target_color = (1, 1, 1)
        elif self.state == "CORE_OPEN":
            target_text = "DOUBLE JUMP TO TRANSFORM\nPUNCH/BOMB TO CYCLE"
            target_color = (0, 1, 1)
        elif self.state == "TRANSFORMED":
            if self.current_alien in ["XLR8", "Cannonball"]:
                if self.power_active:
                    target_text = "DOUBLE JUMP TO DEACTIVATE POWER\nDOUBLE PICKUP TO DETRANSFORM"
                    target_color = (1, 0, 0)
                else:
                    target_text = "DOUBLE JUMP TO ACTIVATE POWERS\nDOUBLE PICKUP TO DETRANSFORM"
                    target_color = (0, 1, 0)
            elif self.current_alien == "Fourarms":
                target_text = "HOLD JUMP FOR SUPER LEAP\nDOUBLE PUNCH TO THROW ROCK\nDOUBLE PICKUP TO DETRANSFORM"
                target_color = (0, 1, 0)
            elif self.current_alien == "Heatblast":
                target_text = "DOUBLE BOMB TO THROW FIREBALL\nDOUBLE PICKUP TO DETRANSFORM"
                target_color = (1, 0.5, 0)
            elif self.current_alien == "Goop":
                target_text = "DOUBLE BOMB TO THROW SLIME\nDOUBLE PICKUP TO DETRANSFORM"
                target_color = (0.4, 0.9, 0.1)
            else:
                target_text = "DOUBLE PICKUP TO DETRANSFORM"
                target_color = (1, 1, 1)

        # Apply Text and dynamically control the Opacity parameter
        self.info_text.text = target_text
        self.info_text.color = target_color
        self.info_text.opacity = self.instruction_opacity

def equip_omnitrix(spaz: Spaz):
    if not hasattr(spaz, 'omnitrix_manager'):
        spaz.omnitrix_manager = OmnitrixManager(spaz)
        bs.getsound('powerup01').play(position=spaz.node.position)
        bs.emitfx(position=spaz.node.position, count=20, scale=2.0, chunk_type='spark')


# ba_meta export babase.Plugin
class OmnitrixPlugin(babase.Plugin):
    def on_app_running(self):
        print("=== OMNITRIX CORE ENGINE LOADED SUCCESSFULLY ===")

        _old_factory_init = PowerupBoxFactory.__init__
        def _new_factory_init(self, *args, **kwargs):
            _old_factory_init(self, *args, **kwargs)
            dist = list(self._powerupdist)
            for _ in range(5): 
                dist.append('omnitrix')
            self._powerupdist = tuple(dist)
        PowerupBoxFactory.__init__ = _new_factory_init

        # Hot-reload injection for the drop table so it spawns instantly
        try:
            factory = PowerupBoxFactory.get()
            if 'omnitrix' not in factory._powerupdist:
                dist = list(factory._powerupdist)
                for _ in range(5): 
                    dist.append('omnitrix')
                factory._powerupdist = tuple(dist)
        except Exception:
            pass

        _old_powerup_init = PowerupBox.__init__
        def _new_powerup_init(self, position=(0, 1, 0), poweruptype='triple_bombs', expire=True):
            fake_type = 'health' if poweruptype == 'omnitrix' else poweruptype
            _old_powerup_init(self, position, fake_type, expire)
            
            if poweruptype == 'omnitrix':
                self.poweruptype = 'omnitrix'
                if self.node:
                    light = bs.newnode('light', owner=self.node, attrs={
                        'color': (0.1, 1.0, 0.1), # Very strong green glow around the box
                        'volume_intensity_scale': 0.5,
                        'intensity': 2.5,
                        'radius': 0.25
                    })
                    self.node.connectattr('position', light, 'position')
                    
        PowerupBox.__init__ = _new_powerup_init

        # --- GLOBAL INPUT INTERCEPTORS ---
        _old_punch = Spaz.on_punch_press
        def _new_punch(self):
            if hasattr(self, 'omnitrix_manager') and self.omnitrix_manager.handle_punch():
                return
            _old_punch(self)
        Spaz.on_punch_press = _new_punch

        _old_pickup = Spaz.on_pickup_press
        def _new_pickup(self):
            if hasattr(self, 'omnitrix_manager') and self.omnitrix_manager.handle_pickup():
                return
            _old_pickup(self)
        Spaz.on_pickup_press = _new_pickup

        _old_jump = Spaz.on_jump_press
        def _new_jump(self):
            if hasattr(self, 'omnitrix_manager'):
                self.omnitrix_manager.jump_held = True 
                if self.omnitrix_manager.handle_jump():
                    return
            _old_jump(self)
        Spaz.on_jump_press = _new_jump
        
        _old_jump_release = Spaz.on_jump_release
        def _new_jump_release(self):
            if hasattr(self, 'omnitrix_manager'):
                self.omnitrix_manager.jump_held = False
            _old_jump_release(self)
        Spaz.on_jump_release = _new_jump_release

        _old_bomb = Spaz.on_bomb_press
        def _new_bomb(self):
            if hasattr(self, 'omnitrix_manager') and self.omnitrix_manager.handle_bomb():
                return
            _old_bomb(self)
        Spaz.on_bomb_press = _new_bomb

        _old_spaz_handlemessage = Spaz.handlemessage
        def _new_spaz_handlemessage(self, msg):
            if isinstance(msg, bs.PowerupMessage):
                if msg.poweruptype == 'omnitrix':
                    equip_omnitrix(self)
                    msg.poweruptype = 'health' 
                    
            if isinstance(msg, bs.HitMessage):
                if hasattr(self, 'omnitrix_manager') and getattr(self.omnitrix_manager, 'current_alien', None) == "Fourarms":
                    if msg.hit_type == 'punch':
                        return None 
                        
            return _old_spaz_handlemessage(self, msg)
        Spaz.handlemessage = _new_spaz_handlemessage
