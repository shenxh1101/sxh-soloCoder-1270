import math
import random
import pygame
from game.config import *
from game.utils import clamp, distance, angle_between
from game.weapons import Bullet


class Boss:
    def __init__(self, wave_number):
        self.stage = (wave_number // WAVE_BOSS_INTERVAL) - 1
        self.name = BOSS_NAMES[self.stage % len(BOSS_NAMES)]
        self.x = SCREEN_WIDTH / 2
        self.y = -150
        self.target_y = 120
        self.width = 140 + self.stage * 20
        self.height = 100 + self.stage * 15
        self.max_health = 800 + self.stage * 400
        self.health = self.max_health
        self.alive = True
        self.phase = 0
        self.max_phase = 3
        self.current_attack = 0
        self.attack_timer = 0
        self.attack_duration = 0
        self.move_timer = 0
        self.target_x = self.x
        self.wobble = 0
        self.weakpoint_active = False
        self.weakpoint_timer = 0
        self.weakpoint_x = 0
        self.weakpoint_y = 0
        self.weakpoint_radius = 20
        self.entrance = True
        self.rage_mode = False
        self.color = COLORS['boss']

    @property
    def rect(self):
        return pygame.Rect(self.x - self.width / 2, self.y - self.height / 2,
                           self.width, self.height)

    def get_phase_thresholds(self):
        return [self.max_health * 0.75, self.max_health * 0.5, self.max_health * 0.25]

    def update_phase(self):
        thresholds = self.get_phase_thresholds()
        for i, t in enumerate(thresholds):
            if self.health <= t and self.phase <= i:
                self.phase = i + 1
                self.rage_mode = self.phase >= self.max_phase
                self.weakpoint_active = True
                self.weakpoint_timer = 3000
                return True
        return False

    def take_damage(self, damage, hit_x, hit_y):
        if self.entrance:
            return False
        actual_damage = damage
        if self.weakpoint_active:
            d = distance((hit_x, hit_y), (self.x + self.weakpoint_x, self.y + self.weakpoint_y))
            if d < self.weakpoint_radius + 15:
                actual_damage *= 3
        self.health -= actual_damage
        if self.health <= 0:
            self.alive = False
        return actual_damage > damage

    def update(self, dt, players, current_time, particle_system):
        if not self.alive:
            return []
        self.wobble += dt / 150
        bullets = []
        if self.entrance:
            self.y += 100 * dt / 1000
            if self.y >= self.target_y:
                self.y = self.target_y
                self.entrance = False
            return bullets
        if self.weakpoint_active:
            self.weakpoint_timer -= dt
            if self.weakpoint_timer <= 0:
                self.weakpoint_active = False
        if not self.weakpoint_active and random.random() < 0.002:
            self.weakpoint_active = True
            self.weakpoint_timer = 2000 + random.randint(0, 1500)
            self.weakpoint_x = random.randint(-self.width // 3, self.width // 3)
            self.weakpoint_y = random.randint(-self.height // 3, self.height // 3)
        self.move_timer += dt
        if self.move_timer > 2000 + random.randint(0, 1500):
            self.move_timer = 0
            self.target_x = random.randint(100, SCREEN_WIDTH - 100)
        dx = self.target_x - self.x
        self.x += clamp(dx * 2, -150, 150) * dt / 1000
        self.x = clamp(self.x, self.width / 2, SCREEN_WIDTH - self.width / 2)
        self.y = self.target_y + math.sin(self.wobble * 0.5) * 20
        phase_attack_rates = [1.0, 1.2, 1.5, 2.0]
        rate_mult = phase_attack_rates[min(self.phase, len(phase_attack_rates) - 1)]
        if self.rage_mode:
            rate_mult *= 1.3
        self.attack_timer += dt * rate_mult
        attacks = [
            self._attack_spread,
            self._attack_spiral,
            self._attack_laser_volley,
            self._attack_homing,
            self._attack_rain,
        ]
        if self.attack_timer > 2500:
            self.attack_timer = 0
            attack_idx = random.randint(0, min(self.phase + 1, len(attacks) - 1))
            bullets = attacks[attack_idx](players)
        return bullets

    def _attack_spread(self, players):
        bullets = []
        count = 8 + self.phase * 2
        for i in range(count):
            angle = math.pi / 2 + (i - count / 2) * 0.15
            speed = 250 + self.phase * 30
            bullets.append(Bullet(
                self.x, self.y + self.height / 2,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                15 + self.phase * 5, 'boss', (255, 100, 255),
                is_player=False, radius=6
            ))
        return bullets

    def _attack_spiral(self, players):
        bullets = []
        count = 16 + self.phase * 4
        for i in range(count):
            angle = math.pi * 2 * i / count + self.wobble
            speed = 200 + self.phase * 20
            bullets.append(Bullet(
                self.x, self.y,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                12 + self.phase * 4, 'boss', (200, 50, 255),
                is_player=False, radius=5
            ))
        return bullets

    def _attack_laser_volley(self, players):
        bullets = []
        target = self._find_closest_player(players)
        if not target:
            return bullets
        for i in range(3 + self.phase):
            angle = angle_between((self.x, self.y + self.height / 2), (target.x, target.y))
            angle += random.uniform(-0.1, 0.1)
            bullets.append(Bullet(
                self.x + random.randint(-20, 20), self.y + self.height / 2,
                math.cos(angle) * 600,
                math.sin(angle) * 600,
                20 + self.phase * 5, 'boss', (255, 50, 100),
                is_player=False, radius=4
            ))
        return bullets

    def _attack_homing(self, players):
        bullets = []
        count = 2 + self.phase
        for i in range(count):
            offset = (i - count / 2) * 30
            bullets.append(Bullet(
                self.x + offset, self.y + self.height / 2,
                0, 200,
                25 + self.phase * 5, 'missile', (255, 150, 0),
                is_player=False, radius=7, homing=True
            ))
        return bullets

    def _attack_rain(self, players):
        bullets = []
        count = 12 + self.phase * 3
        for i in range(count):
            bx = random.randint(50, SCREEN_WIDTH - 50)
            bullets.append(Bullet(
                bx, -20,
                random.uniform(-30, 30), 300 + random.randint(0, 100),
                10 + self.phase * 3, 'boss', (180, 100, 255),
                is_player=False, radius=5
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

    def draw(self, surface):
        if not self.alive:
            return
        surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
        cx, cy = (self.width + 20) / 2, (self.height + 20) / 2
        body_color = list(self.color)
        if self.rage_mode:
            body_color = [min(255, c + 50) for c in body_color]
            body_color[1] = max(0, body_color[1] - 50)
        body_color = tuple(body_color) + (255,)
        pygame.draw.ellipse(surf, body_color,
                            (cx - self.width / 2, cy - self.height / 2, self.width, self.height))
        pygame.draw.ellipse(surf, (100, 0, 150),
                            (cx - self.width / 2 + 10, cy - self.height / 2 + 10,
                             self.width - 20, self.height - 20), 4)
        core_color = (255, 100, 255) if not self.rage_mode else (255, 50, 50)
        core_size = 20 + int(math.sin(self.wobble * 2) * 5)
        pygame.draw.circle(surf, core_color, (int(cx), int(cy)), core_size)
        pygame.draw.circle(surf, (255, 200, 255), (int(cx), int(cy)), core_size // 2)
        side_w = 25
        side_h = 40
        pygame.draw.rect(surf, (150, 50, 180),
                         (cx - self.width / 2 - side_w, cy - side_h / 2, side_w, side_h),
                         border_radius=4)
        pygame.draw.rect(surf, (150, 50, 180),
                         (cx + self.width / 2, cy - side_h / 2, side_w, side_h),
                         border_radius=4)
        for i in range(4):
            cannon_y = cy - self.height / 4 + i * (self.height / 6)
            pygame.draw.rect(surf, (80, 30, 100),
                             (cx - 8, cannon_y, 16, 12))
        surface.blit(surf, (self.x - (self.width + 20) / 2, self.y - (self.height + 20) / 2))
        if self.weakpoint_active and not self.entrance:
            pulse = 0.6 + 0.4 * math.sin(self.wobble * 5)
            wx = self.x + self.weakpoint_x
            wy = self.y + self.weakpoint_y
            weak_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(weak_surf, (255, int(255 * pulse), 0, 200),
                               (30, 30), int(18 * pulse))
            pygame.draw.circle(weak_surf, (255, 255, 100, 255),
                               (30, 30), 10)
            pygame.draw.circle(weak_surf, (255, 255, 255, 255),
                               (30, 30), 5)
            surface.blit(weak_surf, (wx - 30, wy - 30))
            cross_size = 25
            pygame.draw.line(surface, (255, 255, 0),
                             (wx - cross_size, wy), (wx + cross_size, wy), 2)
            pygame.draw.line(surface, (255, 255, 0),
                             (wx, wy - cross_size), (wx, wy + cross_size), 2)
        if self.phase > 0:
            for i in range(self.phase):
                px = self.x - 30 + i * 20
                pygame.draw.circle(surface, (255, 200, 0), (int(px), int(self.y - self.height / 2 - 20)), 6)
