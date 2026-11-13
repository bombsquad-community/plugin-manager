import bascenev1 as bs
import math
import random
from bascenev1lib.actor.bomb import Bomb

def apply_aura(manager):
    manager._apply_aura(color=(1.0, 0.4, 0.0), intensity=1.0, radius=0.2)

def equip(manager):
    manager._apply_mesh('bones')
    manager.spaz.node.color = (0.9, 0.0, 0.0) 
    if hasattr(manager.spaz.node, 'highlight'):
        manager.spaz.node.highlight = (1.0, 0.4, 0.0) 
    apply_aura(manager)
    
    # Enable hockey physics to prevent tripping/stumbling while surfing
    manager.spaz.node.hockey = True
    
    # Initialize Heatblast cooldown variables
    manager.hb_active_timer = 0.0
    manager.hb_cooldown_timer = 0.0
    manager.hb_is_cooling_down = False

def handle_bomb(manager):
    t = bs.time()

    # 1. Cooldown check (4 seconds)
    if getattr(manager, 'hb_is_cooling_down', False):
        if t < manager.hb_cooldown_timer:
            rem = int(math.ceil(manager.hb_cooldown_timer - t))
            bs.broadcastmessage(f"FIREBALL DEPLETED! Wait {rem}s", color=(1, 0, 0), transient=True)
            bs.getsound('error').play(position=manager.spaz.node.position)
            return
        else:
            manager.hb_is_cooling_down = False
            manager.hb_active_timer = 0.0

    # 2. Start 4-second active throwing window
    if getattr(manager, 'hb_active_timer', 0.0) == 0.0:
        manager.hb_active_timer = t + 4.0

    # 3. Trigger cooldown if active window expired
    if t > manager.hb_active_timer:
        manager.hb_is_cooling_down = True
        manager.hb_cooldown_timer = t + 4.0
        bs.broadcastmessage("FIREBALL DEPLETED! RECHARGING...", color=(1, 0, 0), transient=True)
        bs.getsound('error').play(position=manager.spaz.node.position)
        return

    # 4. Throw the Fireball
    pos = manager.spaz.node.position
    vel = manager.spaz.node.velocity
    
    speed = math.hypot(vel[0], vel[2])
    if speed > 0.1:
        dir_x = vel[0] / speed
        dir_z = vel[2] / speed
    else:
        dir_x, dir_z = 0.0, -1.0
        
    spawn_pos = (pos[0] + dir_x * 0.8, pos[1] + 0.6, pos[2] + dir_z * 0.8)
    spawn_vel = (dir_x * 12.0, 1.0, dir_z * 12.0)
    
    bs.emitfx(position=spawn_pos, velocity=spawn_vel, count=50, scale=2.0, spread=1.0, chunk_type='spark')
    b = Bomb(position=spawn_pos, velocity=spawn_vel, bomb_type='impact')
    b.autoretain()
    
    # Red punch texture + glowing yellow light
    if b.node:
        b.node.color_texture = bs.gettexture('powerupPunch')
        light = bs.newnode('light', owner=b.node, attrs={
            'color': (1.0, 1.0, 0.0),
            'radius': 0.15,
            'intensity': 1.5,
            'volume_intensity_scale': 0.1
        })
        b.node.connectattr('position', light, 'position')

def update_physics(manager, pos, vel, input_mag, move_lr, move_ud):
    node = manager.spaz.node
    if not node:
        return

    # 1. Hover Stabilization (Keeps character lifted and upright)
    target_y = 0.05
    current_y = pos[1]
    up_force = 160.0 + ((target_y - current_y) * 160.0) - (vel[1] * 90.0)
    if up_force < 0:
        up_force = 0.0
        
    node.handlemessage(
        'impulse', pos[0], pos[1], pos[2], vel[0], vel[1], vel[2],
        up_force, 0.0, 0.0, 0, 0.0, 1.0, 0.0
    )
        
    # 2. XLR8-Style Fire Surfing Dash
    if input_mag > 0.15:
        dir_x = move_lr / input_mag
        dir_z = -move_ud / input_mag
        
        surf_speed = 80.0 * min(1.0, input_mag)
        node.handlemessage(
            'impulse', pos[0], pos[1], pos[2], vel[0], vel[1], vel[2],
            surf_speed, 0.0, 0.0, 0, dir_x, 0.0, dir_z
        )
        
        # Ground fire trail
        if bs.time() % 0.08 < 0.04:
            bs.emitfx(
                position=(pos[0], pos[1] - 0.35, pos[2]),
                velocity=(-dir_x * 3.0, 0.5, -dir_z * 3.0),
                count=2,
                scale=1.4,
                spread=0.2,
                chunk_type='spark'
            )
