import random
import math
import pygame
from game.config import *
from game.utils import clamp, random_color_variation


class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'max_life', 'size', 'color', 'shrink', 'gravity']

    def __init__(self, x, y, vx, vy, life, size, color, shrink=True, gravity=0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color
        self.shrink = shrink
        self.gravity = gravity

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt / 1000
        self.y += self.vy * dt / 1000
        self.vy += self.gravity * dt / 1000
        if self.shrink:
            self.size = max(0, self.size * (self.life / self.max_life))
        return self.life > 0

    def draw(self, surface):
        if self.life <= 0 or self.size < 0.5:
            return
        alpha = int(255 * (self.life / self.max_life))
        temp_surf = pygame.Surface((int(self.size * 2) + 2, int(self.size * 2) + 2), pygame.SRCALPHA)
        color = (self.color[0], self.color[1], self.color[2], alpha)
        pygame.draw.circle(temp_surf, color,
                           (int(self.size) + 1, int(self.size) + 1),
                           max(1, int(self.size)))
        surface.blit(temp_surf, (self.x - self.size - 1, self.y - self.size - 1))


class ParticleSystem:
    def __init__(self, max_particles=MAX_PARTICLES):
        self.particles = []
        self.max_particles = max_particles

    def emit(self, x, y, count=10, color=(255, 255, 255), speed_range=(50, 200),
             life_range=(300, 800), size_range=(2, 5), shrink=True, gravity=0, spread=360, angle=0):
        spread_rad = math.radians(spread)
        base_angle = math.radians(angle)
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            a = base_angle + random.uniform(-spread_rad / 2, spread_rad / 2)
            speed = random.uniform(*speed_range)
            life = random.randint(*life_range)
            size = random.uniform(*size_range)
            c = random_color_variation(color, 40)
            self.particles.append(Particle(
                x, y,
                math.cos(a) * speed,
                math.sin(a) * speed,
                life, size, c, shrink, gravity
            ))

    def explosion(self, x, y, size='medium', color=None):
        params = {
            'small': {'count': 15, 'speed': (80, 200), 'life': (200, 500), 'size': (2, 4)},
            'medium': {'count': 35, 'speed': (100, 350), 'life': (300, 800), 'size': (3, 7)},
            'large': {'count': 80, 'speed': (150, 500), 'life': (500, 1200), 'size': (4, 10)},
            'boss': {'count': 200, 'speed': (200, 700), 'life': (800, 2000), 'size': (5, 15)},
        }
        p = params.get(size, params['medium'])
        if color is None:
            color = (255, 180, 60)
        self.emit(x, y, count=p['count'], color=color,
                  speed_range=p['speed'], life_range=p['life'], size_range=p['size'])
        self.emit(x, y, count=p['count'] // 2, color=(255, 255, 200),
                  speed_range=(p['speed'][0] // 2, p['speed'][1] // 2),
                  life_range=(p['life'][0] + 100, p['life'][1] + 200),
                  size_range=(p['size'][0] + 1, p['size'][1] + 2))

    def thrust(self, x, y, angle, color=None):
        if color is None:
            color = (100, 200, 255)
        for _ in range(2):
            if len(self.particles) >= self.max_particles:
                break
            a = math.radians(angle) + random.uniform(-0.3, 0.3)
            speed = random.uniform(100, 250)
            self.particles.append(Particle(
                x, y,
                math.cos(a) * speed,
                math.sin(a) * speed,
                random.randint(150, 350),
                random.uniform(2, 4),
                random_color_variation(color, 50),
                shrink=True
            ))

    def hit_spark(self, x, y, color=(255, 255, 150)):
        self.emit(x, y, count=6, color=color,
                  speed_range=(50, 200), life_range=(100, 300), size_range=(1, 3),
                  spread=180)

    def trail(self, x, y, color=(200, 100, 255)):
        if len(self.particles) < self.max_particles:
            self.particles.append(Particle(
                x + random.uniform(-2, 2), y + random.uniform(-2, 2),
                random.uniform(-20, 20), random.uniform(-20, 20),
                random.randint(200, 500),
                random.uniform(2, 4),
                random_color_variation(color, 30),
                shrink=True
            ))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)
