import math
import random
import pygame
from game.config import *
from game.utils import clamp, distance, angle_between
from game.weapons import Bullet


class Enemy:
    def __init__(self, enemy_type, x=None, y=None, difficulty=1.0):
        self.type = enemy_type
        self.x = x if x is not None else random.randint(50, SCREEN_WIDTH - 50)
        self.y = y if y is not None else -50
        self.vx = 0
        self.vy = 0
        self.alive = True
        self.age = 0
        self.fire_timer = 0
        self.spawn_animation = 500
        self._init_stats(difficulty)
        self._init_ai()

    def _init_stats(self, difficulty):
        stats = {
            'drone': {'health': 20, 'speed': 180, 'damage': 10, 'score': 50, 'width': 24, 'height': 24,
                      'fire_rate': 0, 'color': (200, 100, 100)},
            'kamikaze': {'health': 15, 'speed': 320, 'damage': 35, 'score': 75, 'width': 20, 'height': 28,
                         'fire_rate': 0, 'color': (255, 80, 0)},
            'fighter': {'health': 40, 'speed': 150, 'damage': 12, 'score': 100, 'width': 32, 'height': 32,
                        'fire_rate': 1500, 'color': (220, 60, 60)},
            'bomber': {'health': 80, 'speed': 80, 'damage': 20, 'score': 150, 'width': 44, 'height': 36,
                       'fire_rate': 2000, 'color': (150, 50, 150)},
            'shield_cruiser': {'health': 180, 'speed': 60, 'damage': 15, 'score': 250, 'width': 56, 'height': 48,
                               'fire_rate': 1200, 'color': (80, 150, 200), 'shield': True},
            'stealth_recon': {'health': 30, 'speed': 220, 'damage': 18, 'score': 200, 'width': 28, 'height': 26,
                              'fire_rate': 1000, 'color': (100, 100, 120), 'stealth': True},
            'sniper': {'health': 35, 'speed': 50, 'damage': 40, 'score': 180, 'width': 30, 'height': 34,
                       'fire_rate': 3000, 'color': (100, 200, 100)},
            'tank': {'health': 250, 'speed': 40, 'damage': 25, 'score': 300, 'width': 52, 'height': 52,
                     'fire_rate': 1800, 'color': (130, 130, 140)},
            'mother_ship': {'health': 400, 'speed': 30, 'damage': 20, 'score': 500, 'width': 72, 'height': 60,
                            'fire_rate': 800, 'color': (180, 50, 180)},
        }
        s = stats[self.type]
        self.max_health = int(s['health'] * difficulty)
        self.health = self.max_health
        self.speed = s['speed']
        self.damage = int(s['damage'] * difficulty)
        self.score = s['score']
        self.width = s['width']
        self.height = s['height']
        self.fire_rate = s['fire_rate']
        self.color = s['color']
        self.has_shield = s.get('shield', False)
        self.shield_health = 80 if self.has_shield else 0
        self.max_shield = self.shield_health
        self.is_stealth = s.get('stealth', False)
        self.visibility = 0.0 if self.is_stealth else 1.0
        self.wobble = random.random() * math.pi * 2

    def _init_ai(self):
        self.ai_state = 'enter'
        self.ai_timer = 0
        self.target_x = self.x
        self.target_y = self.y
        self.pattern_phase = 0

    @property
    def rect(self):
        return pygame.Rect(self.x - self.width / 2, self.y - self.height / 2,
                           self.width, self.height)

    def take_damage(self, damage):
        if self.has_shield and self.shield_health > 0:
            self.shield_health -= damage
            if self.shield_health <= 0:
                self.shield_health = 0
                self.has_shield = False
            return True
        self.health -= damage
        if self.health <= 0:
            self.alive = False
        return True

    def update(self, dt, players, particle_system, current_time):
        if not self.alive:
            return []
        self.age += dt
        if self.spawn_animation > 0:
            self.spawn_animation -= dt
            self.y += self.speed * 0.3 * dt / 1000
            return []
        if self.is_stealth:
            target_vis = 0.0
            for p in players:
                if p.alive and distance((self.x, self.y), (p.x, p.y)) < 250:
                    target_vis = 0.8
                    break
            self.visibility += (target_vis - self.visibility) * dt / 300
        self.wobble += dt / 200
        bullets = []
        if self.type == 'drone':
            bullets = self._ai_drone(dt, players)
        elif self.type == 'kamikaze':
            bullets = self._ai_kamikaze(dt, players)
        elif self.type == 'fighter':
            bullets = self._ai_fighter(dt, players, current_time)
        elif self.type == 'bomber':
            bullets = self._ai_bomber(dt, players, current_time)
        elif self.type == 'shield_cruiser':
            bullets = self._ai_shield_cruiser(dt, players, current_time)
        elif self.type == 'stealth_recon':
            bullets = self._ai_stealth_recon(dt, players, current_time)
        elif self.type == 'sniper':
            bullets = self._ai_sniper(dt, players, current_time)
        elif self.type == 'tank':
            bullets = self._ai_tank(dt, players, current_time)
        elif self.type == 'mother_ship':
            bullets = self._ai_mother_ship(dt, players, current_time)
        self.x = clamp(self.x, self.width / 2, SCREEN_WIDTH - self.width / 2)
        if self.y > SCREEN_HEIGHT + 100 or self.x < -100 or self.x > SCREEN_WIDTH + 100:
            self.alive = False
        return bullets

    def _ai_drone(self, dt, players):
        if self.y < 100:
            self.vy = self.speed
        else:
            self.vy = self.speed * 0.3
            self.vx = math.sin(self.wobble) * self.speed * 0.5
        self.x += self.vx * dt / 1000
        self.y += self.vy * dt / 1000
        return []

    def _ai_kamikaze(self, dt, players):
        target = self._find_closest_player(players)
        if target:
            angle = angle_between((self.x, self.y), (target.x, target.y))
            self.vx = math.cos(angle) * self.speed
            self.vy = math.sin(angle) * self.speed
        self.x += self.vx * dt / 1000
        self.y += self.vy * dt / 1000
        return []

    def _ai_fighter(self, dt, players, current_time):
        self.ai_timer += dt
        if self.ai_state == 'enter':
            self.vy = self.speed
            if self.y > 150:
                self.ai_state = 'strafe'
                self.ai_timer = 0
                self.target_x = self.x + random.choice([-1, 1]) * 200
        elif self.ai_state == 'strafe':
            self.vy = self.speed * 0.2
            dx = self.target_x - self.x
            self.vx = clamp(dx * 3, -self.speed, self.speed)
            if abs(dx) < 20 or self.ai_timer > 2000:
                self.ai_state = 'strafe'
                self.ai_timer = 0
                self.target_x = random.randint(100, SCREEN_WIDTH - 100)
        self.x += self.vx * dt / 1000
        self.y += self.vy * dt / 1000
        return self._shoot_at_player(players, current_time, 400)

    def _ai_bomber(self, dt, players, current_time):
        self.vy = self.speed
        self.vx = math.sin(self.wobble * 0.5) * 40
        self.x += self.vx * dt / 1000
        self.y += self.vy * dt / 1000
        bullets = []
        if self.fire_rate > 0 and current_time - self.fire_timer > self.fire_rate:
            self.fire_timer = current_time
            for angle_offset in [-0.4, 0, 0.4]:
                angle = math.pi / 2 + angle_offset
                bullets.append(Bullet(
                    self.x, self.y + self.height / 2,
                    math.cos(angle) * 280,
                    math.sin(angle) * 280,
                    self.damage, 'enemy', (255, 100, 200), is_player=False, radius=5
                ))
        return bullets

    def _ai_shield_cruiser(self, dt, players, current_time):
        if self.y < 120:
            self.vy = self.speed
        else:
            self.vy = self.speed * 0.1
            self.vx = math.sin(self.wobble * 0.3) * 30
        self.x += self.vx * dt / 1000
        self.y += self.vy * dt / 1000
        bullets = []
        if self.fire_rate > 0 and current_time - self.fire_timer > self.fire_rate:
            self.fire_timer = current_time
            for i in range(3):
                angle = math.pi / 2 + (i - 1) * 0.25
                bullets.append(Bullet(
                    self.x, self.y + self.height / 2,
                    math.cos(angle) * 320,
                    math.sin(angle) * 320,
                    self.damage, 'enemy', (100, 200, 255), is_player=False, radius=4
                ))
        return bullets

    def _ai_stealth_recon(self, dt, players, current_time):
        target = self._find_closest_player(players)
        if target:
            dx = target.x - self.x
            self.vx = clamp(dx * 2, -self.speed, self.speed)
        if self.y < 80:
            self.vy = self.speed
        else:
            self.vy = math.sin(self.wobble) * 50
        self.x += self.vx * dt / 1000
        self.y += self.vy * dt / 1000
        return self._shoot_at_player(players, current_time, 450)

    def _ai_sniper(self, dt, players, current_time):
        if self.y < 100:
            self.vy = self.speed
        else:
            self.vy = 0
        self.x += self.vx * dt / 1000
        self.y += self.vy * dt / 1000
        bullets = []
        if self.fire_rate > 0 and current_time - self.fire_timer > self.fire_rate:
            target = self._find_closest_player(players)
            if target:
                self.fire_timer = current_time
                angle = angle_between((self.x, self.y), (target.x, target.y))
                bullets.append(Bullet(
                    self.x, self.y,
                    math.cos(angle) * 700,
                    math.sin(angle) * 700,
                    self.damage, 'enemy', (150, 255, 100), is_player=False, radius=3
                ))
        return bullets

    def _ai_tank(self, dt, players, current_time):
        if self.y < 150:
            self.vy = self.speed
        else:
            self.vy = self.speed * 0.05
            self.vx = math.sin(self.wobble * 0.2) * 20
        self.x += self.vx * dt / 1000
        self.y += self.vy * dt / 1000
        bullets = []
        if self.fire_rate > 0 and current_time - self.fire_timer > self.fire_rate:
            self.fire_timer = current_time
            for i in range(5):
                angle = math.pi / 2 + (i - 2) * 0.2
                bullets.append(Bullet(
                    self.x, self.y + self.height / 2,
                    math.cos(angle) * 250,
                    math.sin(angle) * 250,
                    self.damage, 'enemy', (200, 200, 200), is_player=False, radius=5
                ))
        return bullets

    def _ai_mother_ship(self, dt, players, current_time):
        if self.y < 100:
            self.vy = self.speed
        else:
            self.vy = 0
            self.vx = math.sin(self.wobble * 0.15) * 40
        self.x += self.vx * dt / 1000
        self.y += self.vy * dt / 1000
        bullets = []
        if self.fire_rate > 0 and current_time - self.fire_timer > self.fire_rate:
            self.fire_timer = current_time
            for i in range(8):
                angle = math.pi * 2 * i / 8 + self.wobble * 0.5
                bullets.append(Bullet(
                    self.x, self.y,
                    math.cos(angle) * 200,
                    math.sin(angle) * 200,
                    self.damage, 'enemy', (255, 50, 255), is_player=False, radius=4
                ))
        return bullets

    def _find_closest_player(self, players):
        best = None
        best_dist = float('inf')
        for p in players:
            if not p.alive:
                continue
            d = distance((self.x, self.y), (p.x, p.y))
            if d < best_dist:
                best_dist = d
                best = p
        return best

    def _shoot_at_player(self, players, current_time, speed):
        if self.fire_rate == 0:
            return []
        if current_time - self.fire_timer < self.fire_rate:
            return []
        target = self._find_closest_player(players)
        if not target:
            return []
        self.fire_timer = current_time
        angle = angle_between((self.x, self.y), (target.x, target.y))
        return [Bullet(
            self.x, self.y + self.height / 2,
            math.cos(angle) * speed,
            math.sin(angle) * speed,
            self.damage, 'enemy', (255, 80, 80), is_player=False, radius=4
        )]

    def draw(self, surface):
        if not self.alive:
            return
        alpha = int(255 * self.visibility) if self.is_stealth else 255
        if self.spawn_animation > 0:
            alpha = int(255 * (1 - self.spawn_animation / 500))
        surf = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
        color = (self.color[0], self.color[1], self.color[2], alpha)
        self._draw_shape(surf, (self.width + 10) / 2, (self.height + 10) / 2, color)
        surface.blit(surf, (self.x - (self.width + 10) / 2, self.y - (self.height + 10) / 2))
        if self.has_shield and self.shield_health > 0:
            shield_alpha = int(150 * (self.shield_health / self.max_shield))
            s = pygame.Surface((self.width + 30, self.height + 30), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 180, 255, shield_alpha),
                               ((self.width + 30) / 2, (self.height + 30) / 2),
                               int((self.width + 20) / 2), 3)
            surface.blit(s, (self.x - (self.width + 30) / 2, self.y - (self.height + 30) / 2))

    def _draw_shape(self, surf, cx, cy, color):
        if self.type == 'drone':
            pygame.draw.polygon(surf, color, [
                (cx, cy - self.height / 2),
                (cx + self.width / 2, cy),
                (cx, cy + self.height / 2),
                (cx - self.width / 2, cy),
            ])
            pygame.draw.circle(surf, (255, 255, 255), (int(cx), int(cy)), 5)
        elif self.type == 'kamikaze':
            pygame.draw.polygon(surf, color, [
                (cx, cy - self.height / 2),
                (cx + self.width / 3, cy + self.height / 2),
                (cx, cy + self.height / 3),
                (cx - self.width / 3, cy + self.height / 2),
            ])
            glow = (255, 150, 0)
            pygame.draw.circle(surf, glow, (int(cx), int(cy)), 6)
        elif self.type == 'fighter':
            pygame.draw.polygon(surf, color, [
                (cx, cy - self.height / 2),
                (cx + self.width / 2, cy + self.height / 4),
                (cx + self.width / 4, cy + self.height / 2),
                (cx - self.width / 4, cy + self.height / 2),
                (cx - self.width / 2, cy + self.height / 4),
            ])
        elif self.type == 'bomber':
            pygame.draw.ellipse(surf, color, (cx - self.width / 2, cy - self.height / 2,
                                              self.width, self.height))
            pygame.draw.rect(surf, (80, 20, 80),
                             (cx - self.width / 2 - 4, cy - 4, 8, 8))
            pygame.draw.rect(surf, (80, 20, 80),
                             (cx + self.width / 2 - 4, cy - 4, 8, 8))
        elif self.type == 'shield_cruiser':
            pygame.draw.rect(surf, color, (cx - self.width / 2, cy - self.height / 2,
                                           self.width, self.height), border_radius=8)
            pygame.draw.rect(surf, (200, 220, 255),
                             (cx - 8, cy - self.height / 2 + 6, 16, self.height - 12),
                             border_radius=4)
        elif self.type == 'stealth_recon':
            pygame.draw.polygon(surf, color, [
                (cx, cy - self.height / 2),
                (cx + self.width / 2, cy),
                (cx + self.width / 3, cy + self.height / 2),
                (cx - self.width / 3, cy + self.height / 2),
                (cx - self.width / 2, cy),
            ])
        elif self.type == 'sniper':
            pygame.draw.polygon(surf, color, [
                (cx, cy - self.height / 2),
                (cx + self.width / 2, cy - self.height / 4),
                (cx + self.width / 4, cy + self.height / 2),
                (cx - self.width / 4, cy + self.height / 2),
                (cx - self.width / 2, cy - self.height / 4),
            ])
            pygame.draw.line(surf, (150, 255, 100),
                             (cx, cy - self.height / 2), (cx, cy + self.height / 2), 2)
        elif self.type == 'tank':
            pygame.draw.rect(surf, color, (cx - self.width / 2, cy - self.height / 2,
                                           self.width, self.height), border_radius=4)
            pygame.draw.rect(surf, (80, 80, 90),
                             (cx - self.width / 2 + 4, cy - self.height / 2 + 4,
                              self.width - 8, self.height - 8), border_radius=4)
            pygame.draw.circle(surf, (255, 50, 50), (int(cx), int(cy)), 8)
        elif self.type == 'mother_ship':
            pygame.draw.ellipse(surf, color, (cx - self.width / 2, cy - self.height / 3,
                                              self.width, self.height * 2 / 3))
            pygame.draw.polygon(surf, (100, 30, 100), [
                (cx - self.width / 2, cy),
                (cx, cy + self.height / 2),
                (cx + self.width / 2, cy),
            ])
            pygame.draw.circle(surf, (255, 200, 255), (int(cx), int(cy - self.height / 6)), 10)
