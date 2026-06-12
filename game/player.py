import math
import random
import pygame
from game.config import *
from game.utils import clamp
from game.weapons import Weapon


class Player:
    def __init__(self, player_id=1):
        self.id = player_id
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT - 120
        self.width = 36
        self.height = 40
        self.speed = 380
        self.health = 100
        self.max_health = 100
        self.lives = 3
        self.invincible = False
        self.invincible_time = 0
        self.score = 0
        self.combo = 0
        self.combo_timer = 0
        self.current_weapon_idx = 0
        self.weapons = {
            'laser': Weapon('laser'),
            'shotgun': Weapon('shotgun'),
            'missile': Weapon('missile'),
            'plasma': Weapon('plasma'),
        }
        self.weapon_order = ['laser', 'shotgun', 'missile', 'plasma']
        self.color = COLORS['player'] if player_id == 1 else COLORS['player2']
        self.shape_type = 0
        self.damage_mult = 1.0
        self.speed_mult = 1.0
        self.heat_mult = 1.0
        self.upgrades = []
        self.extra_pellets = 0
        stats = SHIP_SHAPE_STATS[self.shape_type]
        self.max_health = int(100 * stats['health_mult'])
        self.health = self.max_health
        self.speed_mult = stats['speed_mult']
        self.damage_mult = stats['damage_mult']
        self.bullets = []
        self.is_firing = False
        self.thrust_angle = 270
        self.engine_flame = 0
        self.last_dodge_time = 0
        self.dodge_cooldown = 0
        self.slowmo_active = False
        self.slowmo_timer = 0
        self.score_multiplier = 1.0
        self.dodge_frame = 0
        self.alive = True

    @property
    def current_weapon(self):
        return self.weapons[self.weapon_order[self.current_weapon_idx]]

    @property
    def rect(self):
        return pygame.Rect(self.x - self.width / 2, self.y - self.height / 2,
                           self.width, self.height)

    def switch_weapon(self, direction=1):
        self.current_weapon_idx = (self.current_weapon_idx + direction) % len(self.weapon_order)
        self.current_weapon.stop_charging()

    def select_weapon(self, idx):
        if 0 <= idx < len(self.weapon_order):
            self.current_weapon.stop_charging()
            self.current_weapon_idx = idx

    def take_damage(self, damage):
        if self.invincible or not self.alive:
            return False
        self.health -= damage
        self.invincible = True
        self.invincible_time = 1500
        self.combo = 0
        self.combo_timer = 0
        if self.health <= 0:
            self.lives -= 1
            if self.lives <= 0:
                self.alive = False
            else:
                self.health = self.max_health
                self.invincible_time = 3000
                self.x = SCREEN_WIDTH / 2
                self.y = SCREEN_HEIGHT - 120
        return True

    def add_score(self, points):
        self.combo += 1
        self.combo_timer = MAX_COMBO_TIME
        self.score_multiplier = 1.0 + min(2.0, self.combo * 0.05)
        self.score += int(points * self.score_multiplier)

    def check_dodge(self, enemies, bullets):
        now = pygame.time.get_ticks()
        if now - self.last_dodge_time < 500:
            return False
        dodge_radius = DODGE_THRESHOLD
        for e in enemies:
            if not e.alive:
                continue
            dx = e.x - self.x
            dy = e.y - self.y
            dist = math.hypot(dx, dy)
            if dist < dodge_radius + max(e.width, e.height) / 2:
                speed = math.hypot(e.vx, e.vy)
                if speed > 150 and self._is_approaching(e):
                    self._trigger_dodge(now)
                    return True
        for b in bullets:
            if b.is_player or not b.alive:
                continue
            dx = b.x - self.x
            dy = b.y - self.y
            dist = math.hypot(dx, dy)
            if dist < dodge_radius + b.radius:
                speed = math.hypot(b.vx, b.vy)
                if speed > 300:
                    self._trigger_dodge(now)
                    return True
        return False

    def _is_approaching(self, entity):
        dx = self.x - entity.x
        dy = self.y - entity.y
        dot = dx * entity.vx + dy * entity.vy
        return dot > 0

    def _trigger_dodge(self, now):
        self.last_dodge_time = now
        self.slowmo_active = True
        self.slowmo_timer = SLOWMO_DURATION
        self.dodge_frame = 20
        self.score += 50

    def update(self, dt, keys, enemies, enemy_bullets, particle_system, current_time):
        try:
            if not self.alive:
                return
            time_scale = 0.3 if self.slowmo_active else 1.0
            effective_dt = dt * time_scale
            for w in self.weapons.values():
                w.update(effective_dt)
            if self.slowmo_active:
                self.slowmo_timer -= dt
                if self.slowmo_timer <= 0:
                    self.slowmo_active = False
            if self.dodge_frame > 0:
                self.dodge_frame -= 1
            if self.invincible:
                self.invincible_time -= dt
                if self.invincible_time <= 0:
                    self.invincible = False
            if self.combo_timer > 0:
                self.combo_timer -= dt
                if self.combo_timer <= 0:
                    self.combo = 0
                    self.score_multiplier = 1.0
            self.engine_flame = (self.engine_flame + dt / 50) % (math.pi * 2)
            if self.id == 1:
                move_x = 0
                move_y = 0
                if keys.get(pygame.K_LEFT) or keys.get(pygame.K_a):
                    move_x -= 1
                if keys.get(pygame.K_RIGHT) or keys.get(pygame.K_d):
                    move_x += 1
                if keys.get(pygame.K_UP) or keys.get(pygame.K_w):
                    move_y -= 1
                if keys.get(pygame.K_DOWN) or keys.get(pygame.K_s):
                    move_y += 1
                self.is_firing = keys.get(pygame.K_SPACE, False) or keys.get(pygame.K_z, False)
                if keys.get(pygame.K_x, False) or keys.get(pygame.K_LSHIFT, False):
                    self.current_weapon.start_charging()
                else:
                    if self.current_weapon.type == 'plasma' and self.current_weapon.is_charging:
                        self.is_firing = True
            else:
                move_x = 0
                move_y = 0
                if keys.get(pygame.K_j):
                    move_x -= 1
                if keys.get(pygame.K_l):
                    move_x += 1
                if keys.get(pygame.K_i):
                    move_y -= 1
                if keys.get(pygame.K_k):
                    move_y += 1
                self.is_firing = keys.get(pygame.K_RETURN, False)
            if move_x != 0 and move_y != 0:
                length = math.hypot(move_x, move_y)
                move_x /= length
                move_y /= length
            self.x += move_x * self.speed * effective_dt / 1000 * self.speed_mult
            self.y += move_y * self.speed * effective_dt / 1000 * self.speed_mult
            self.x = clamp(self.x, self.width / 2, SCREEN_WIDTH - self.width / 2)
            self.y = clamp(self.y, self.height / 2, SCREEN_HEIGHT - self.height / 2)
            if move_x != 0 or move_y != 0:
                self.thrust_angle = math.degrees(math.atan2(-move_y, -move_x)) + 90
                particle_system.thrust(
                    self.x - math.sin(math.radians(self.thrust_angle)) * 20,
                    self.y + math.cos(math.radians(self.thrust_angle)) * 20,
                    self.thrust_angle + 180,
                    self.color
                )
            else:
                particle_system.thrust(self.x, self.y + 20, 90, self.color)
        except Exception:
            pass

    def fire(self, current_time):
        if not self.alive:
            return []
        if self.is_firing:
            bullets = self.current_weapon.fire(
                self.x, self.y - self.height / 2, -math.pi / 2, current_time
            )
            for b in bullets:
                b.damage *= self.damage_mult
            return bullets
        return []

    def draw(self, surface):
        try:
            if not self.alive:
                return
            if self.invincible and (pygame.time.get_ticks() // 100) % 2 == 0:
                return
            if self.dodge_frame > 0:
                for i in range(3):
                    offset = (3 - i) * 8
                    alpha = 80 - i * 20
                    ghost_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
                    c = (self.color[0], self.color[1], self.color[2], alpha)
                    self._draw_ship_shape(ghost_surf, (self.width + 20) / 2, (self.height + 20) / 2, c)
                    surface.blit(ghost_surf, (self.x - (self.width + 20) / 2 - offset,
                                              self.y - (self.height + 20) / 2))
            ship_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            self._draw_ship_shape(ship_surf, (self.width + 20) / 2, (self.height + 20) / 2, self.color)
            surface.blit(ship_surf, (self.x - (self.width + 20) / 2, self.y - (self.height + 20) / 2))
            flame_len = 12 + math.sin(self.engine_flame) * 4
            flame_color = (255, 180 + int(50 * math.sin(self.engine_flame * 2)), 50)
            pygame.draw.polygon(surface, flame_color, [
                (self.x - 6, self.y + self.height / 2),
                (self.x, self.y + self.height / 2 + flame_len),
                (self.x + 6, self.y + self.height / 2),
            ])
        except Exception:
            pass

    def _draw_ship_shape(self, surf, cx, cy, color):
        w, h = self.width, self.height
        if self.shape_type == 0:
            points = [
                (cx, cy - h / 2),
                (cx + w / 2, cy + h / 2),
                (cx + w / 4, cy + h / 4),
                (cx, cy + h / 3),
                (cx - w / 4, cy + h / 4),
                (cx - w / 2, cy + h / 2),
            ]
            pygame.draw.polygon(surf, color, points)
            pygame.draw.polygon(surf, (255, 255, 255), points, 2)
        elif self.shape_type == 1:
            points = [
                (cx, cy - h / 2),
                (cx + w / 2 + 4, cy - h / 6),
                (cx + w / 2, cy + h / 2),
                (cx - w / 2, cy + h / 2),
                (cx - w / 2 - 4, cy - h / 6),
            ]
            pygame.draw.polygon(surf, color, points)
            pygame.draw.polygon(surf, (255, 255, 255), points, 2)
            pygame.draw.rect(surf, color, (cx - w / 3, cy - h / 8, w * 2 / 3, h / 3), border_radius=3)
        elif self.shape_type == 2:
            points = [
                (cx, cy - h / 2 - 4),
                (cx + w / 4, cy),
                (cx + w / 3, cy + h / 3),
                (cx, cy + h / 2),
                (cx - w / 3, cy + h / 3),
                (cx - w / 4, cy),
            ]
            pygame.draw.polygon(surf, color, points)
            pygame.draw.polygon(surf, (255, 255, 255), points, 2)
        elif self.shape_type == 3:
            points = [
                (cx, cy - h / 2),
                (cx + w / 2, cy + h / 2),
                (cx - w / 2, cy + h / 2),
            ]
            pygame.draw.polygon(surf, color, points)
            pygame.draw.polygon(surf, (255, 255, 255), points, 2)
            pygame.draw.line(surf, (255, 255, 255),
                             (cx, cy - h / 2 + 8), (cx, cy + h / 2 - 4), 2)
        cockpit_color = (200, 240, 255)
        pygame.draw.polygon(surf, cockpit_color, [
            (cx, cy - h / 3),
            (cx + 6, cy + h / 8),
            (cx - 6, cy + h / 8),
        ])

    def upgrade_current_weapon(self):
        return self.current_weapon.upgrade()

    def apply_upgrade(self, upgrade_id):
        self.upgrades.append(upgrade_id)
        if upgrade_id == 'weapon_upgrade':
            self.upgrade_current_weapon()
        elif upgrade_id == 'shield_up':
            self.max_health += 25
            self.health = self.max_health
        elif upgrade_id == 'speed_up':
            self.speed_mult *= 1.2
        elif upgrade_id == 'heat_down':
            for w in self.weapons.values():
                w.cooldown_rate *= 1.3
        elif upgrade_id == 'damage_up':
            self.damage_mult *= 1.15
        elif upgrade_id == 'multi_shot':
            self.extra_pellets += 1

    def get_time_scale(self):
        return 0.3 if self.slowmo_active else 1.0
