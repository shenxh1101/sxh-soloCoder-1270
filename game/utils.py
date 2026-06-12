import math
import random
import pygame
from game.config import *


def clamp(value, min_val, max_val):
    return max(min_val, min(max_val, value))


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def angle_between(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def random_color_variation(base_color, variance=30):
    return tuple(
        clamp(c + random.randint(-variance, variance), 0, 255)
        for c in base_color
    )


def lerp(a, b, t):
    return a + (b - a) * t


def rects_collide(r1, r2):
    return (r1.x < r2.x + r2.width and
            r1.x + r1.width > r2.x and
            r1.y < r2.y + r2.height and
            r1.y + r1.height > r2.y)


def circle_rect_collide(cx, cy, radius, rect):
    closest_x = clamp(cx, rect.x, rect.x + rect.width)
    closest_y = clamp(cy, rect.y, rect.y + rect.height)
    return distance((cx, cy), (closest_x, closest_y)) < radius


class StarField:
    def __init__(self):
        self.layers = []
        for layer_idx in range(3):
            speed = 20 + layer_idx * 40
            count = 80 + layer_idx * 40
            stars = []
            for _ in range(count):
                stars.append({
                    'x': random.randint(0, SCREEN_WIDTH),
                    'y': random.randint(0, SCREEN_HEIGHT),
                    'size': 1 + layer_idx,
                    'brightness': 100 + layer_idx * 50,
                })
            self.layers.append({'stars': stars, 'speed': speed})

    def update(self, dt):
        for layer in self.layers:
            for star in layer['stars']:
                star['y'] += layer['speed'] * dt / 1000
                if star['y'] > SCREEN_HEIGHT:
                    star['y'] = 0
                    star['x'] = random.randint(0, SCREEN_WIDTH)

    def draw(self, surface):
        for layer in self.layers:
            for star in layer['stars']:
                c = star['brightness']
                pygame.draw.rect(surface, (c, c, min(c + 30, 255)),
                                 (star['x'], star['y'], star['size'], star['size']))
