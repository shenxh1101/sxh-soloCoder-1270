import math
import random
import pygame
from game.config import *
from game.utils import clamp, angle_between, distance


class Bullet:
    def __init__(self, x, y, vx, vy, damage, weapon_type, color, is_player=True, radius=3,
                 homing=False, pierce=0, size_mult=1.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.weapon_type = weapon_type
        self.color = color
        self.is_player = is_player
        self.radius = radius * size_mult
        self.homing = homing
        self.pierce = pierce
        self.hit_enemies = set()
        self.alive = True
        self.age = 0
        self.max_age = 3000 if weapon_type == 'missile' else 2000
        self.trail_timer = 0
        self.trail_color = None
        self.prev_x = x
        self.prev_y = y

    def update(self, dt, enemies=None, players=None):
        self.prev_x = self.x
        self.prev_y = self.y
        self.age += dt
        if self.age > self.max_age:
            self.alive = False
            return
        if self.homing and self.is_player and enemies:
            target = self._find_target(enemies)
            if target:
                angle = angle_between((self.x, self.y), (target.x, target.y))
                current_angle = math.atan2(self.vy, self.vx)
                speed = math.hypot(self.vx, self.vy)
                diff = angle - current_angle
                while diff > math.pi:
                    diff -= 2 * math.pi
                while diff < -math.pi:
                    diff += 2 * math.pi
                turn = clamp(diff, -3.0 * dt / 1000, 3.0 * dt / 1000)
                new_angle = current_angle + turn
                self.vx = math.cos(new_angle) * speed
                self.vy = math.sin(new_angle) * speed
        self.x += self.vx * dt / 1000
        self.y += self.vy * dt / 1000
        if self.x < -50 or self.x > SCREEN_WIDTH + 50 or self.y < -50 or self.y > SCREEN_HEIGHT + 50:
            self.alive = False

    def _find_target(self, enemies):
        best = None
        best_dist = float('inf')
        for e in enemies:
            if not e.alive:
                continue
            d = distance((self.x, self.y), (e.x, e.y))
            if d < 300 and d < best_dist:
                best_dist = d
                best = e
        return best

    def draw(self, surface, particle_system=None):
        if not self.alive:
            return
        try:
            r = max(1, int(self.radius))
            if self.trail_color is not None:
                try:
                    dx = self.x - self.prev_x
                    dy = self.y - self.prev_y
                    dist = math.hypot(dx, dy)
                    seg_count = max(1, int(dist / 4))
                    for i in range(seg_count):
                        t = (seg_count - i) / seg_count
                        px = self.prev_x + dx * t
                        py = self.prev_y + dy * t
                        alpha = int(180 * t)
                        tc = (self.trail_color[0], self.trail_color[1], self.trail_color[2], alpha)
                        trail_surf = pygame.Surface((r * 4 + 2, r * 4 + 2), pygame.SRCALPHA)
                        pygame.draw.circle(trail_surf, tc,
                                          (trail_surf.get_width() // 2, trail_surf.get_height() // 2),
                                          max(1, int(r * 1.5 * t + 1)))
                        surface.blit(trail_surf, (px - trail_surf.get_width() // 2, py - trail_surf.get_height() // 2))
                except Exception:
                    pass
            if particle_system and self.weapon_type in ('missile', 'plasma'):
                self.trail_timer += 16
                if self.trail_timer > 20:
                    self.trail_timer = 0
                    try:
                        particle_system.trail(self.x, self.y, self.color)
                    except Exception:
                        pass
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), r)
            if self.weapon_type == 'laser':
                glow_w = max(4, r * 4 + 4)
                glow_surf = pygame.Surface((glow_w, glow_w), pygame.SRCALPHA)
                g = (self.color[0], self.color[1], self.color[2], 80)
                try:
                    pygame.draw.circle(glow_surf, g,
                                       (glow_w // 2, glow_w // 2),
                                       max(1, int(r * 2)))
                    surface.blit(glow_surf, (self.x - glow_w // 2, self.y - glow_w // 2))
                except Exception:
                    pass
            elif self.weapon_type == 'plasma':
                glow_w = max(6, r * 6 + 6)
                glow_surf = pygame.Surface((glow_w, glow_w), pygame.SRCALPHA)
                try:
                    for i in range(3):
                        alpha = 100 - i * 30
                        g = (self.color[0], self.color[1], self.color[2], max(0, alpha))
                        circle_r = max(1, int(r * (3 - i)))
                        pygame.draw.circle(glow_surf, g,
                                           (glow_w // 2, glow_w // 2), circle_r)
                    surface.blit(glow_surf, (self.x - glow_w // 2, self.y - glow_w // 2))
                except Exception:
                    pass
        except Exception:
            try:
                pygame.draw.circle(surface, self.color,
                                   (int(self.x), int(self.y)), max(1, int(self.radius)))
            except Exception:
                pass


class Weapon:
    def __init__(self, weapon_type):
        self.type = weapon_type
        self.level = 1
        self.heat = 0
        self.max_heat = 100
        self.overheated = False
        self.cooldown_rate = 30
        self.last_fire_time = 0
        self.charge_time = 0
        self.is_charging = False
        config = WEAPON_TYPES[weapon_type]
        self.name = config['name']
        self.base_damage = config['base_damage']
        self.base_fire_rate = config['base_fire_rate']
        self.base_heat = config['heat_per_shot']
        self.pellets = config.get('pellets', 1)

    def get_stats(self):
        mult = UPGRADE_MULTIPLIERS[self.level]
        return {
            'damage': self.base_damage * mult['damage'],
            'fire_rate': int(self.base_fire_rate * mult['fire_rate']),
            'heat': self.base_heat * mult['heat'],
        }

    def upgrade(self):
        if self.level < 3:
            self.level += 1
            return True
        return False

    def start_charging(self):
        if self.type == 'plasma':
            self.is_charging = True
            self.charge_time = 0

    def stop_charging(self):
        self.is_charging = False
        self.charge_time = 0

    def can_fire(self, current_time):
        if self.overheated:
            return False
        stats = self.get_stats()
        return current_time - self.last_fire_time >= stats['fire_rate']

    def update(self, dt):
        if self.is_charging and self.type == 'plasma':
            self.charge_time += dt
        if self.heat > 0:
            self.heat = max(0, self.heat - self.cooldown_rate * dt / 1000)
            if self.overheated and self.heat <= 20:
                self.overheated = False

    def fire(self, x, y, angle, current_time, is_player=True):
        if not self.can_fire(current_time):
            return []
        stats = self.get_stats()
        heat = stats['heat']
        if self.heat + heat > self.max_heat:
            self.overheated = True
            return []
        self.heat += heat
        self.last_fire_time = current_time
        bullets = []
        if self.type == 'laser':
            count = self.level
            spacing = 8 if count > 1 else 0
            for i in range(count):
                offset = (i - (count - 1) / 2) * spacing
                bx = x + math.cos(angle + math.pi / 2) * offset
                by = y + math.sin(angle + math.pi / 2) * offset
                bullets.append(Bullet(
                    bx, by,
                    math.cos(angle) * 900,
                    math.sin(angle) * 900,
                    stats['damage'], 'laser',
                    COLORS['laser'], is_player, radius=4,
                    pierce=self.level - 1
                ))
        elif self.type == 'shotgun':
            pellet_count = self.pellets + self.level - 1
            spread = 0.5 - self.level * 0.1
            for i in range(pellet_count):
                a = angle + random.uniform(-spread / 2, spread / 2)
                speed = random.uniform(700, 850)
                bullets.append(Bullet(
                    x, y,
                    math.cos(a) * speed,
                    math.sin(a) * speed,
                    stats['damage'], 'shotgun',
                    COLORS['shotgun'], is_player, radius=3
                ))
        elif self.type == 'missile':
            count = 1 + (self.level - 1)
            spacing = 15
            for i in range(count):
                offset = (i - (count - 1) / 2) * spacing
                bx = x + math.cos(angle + math.pi / 2) * offset
                by = y + math.sin(angle + math.pi / 2) * offset
                bullets.append(Bullet(
                    bx, by,
                    math.cos(angle) * 500,
                    math.sin(angle) * 500,
                    stats['damage'], 'missile',
                    COLORS['missile'], is_player, radius=5,
                    homing=True
                ))
        elif self.type == 'plasma':
            charge_mult = 1.0
            if self.is_charging:
                charge_mult = 1.0 + min(2.0, self.charge_time / 1000)
            size_mult = 1.0 + (charge_mult - 1) * 0.5
            bullets.append(Bullet(
                x, y,
                math.cos(angle) * 600,
                math.sin(angle) * 600,
                stats['damage'] * charge_mult, 'plasma',
                COLORS['plasma'], is_player, radius=8,
                size_mult=size_mult, pierce=2
            ))
            self.charge_time = 0
            self.is_charging = False
        return bullets
