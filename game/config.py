import pygame

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720
FPS = 60

COLORS = {
    'bg': (10, 10, 25),
    'star': (255, 255, 255),
    'player': (0, 220, 255),
    'player2': (255, 165, 0),
    'enemy': (255, 50, 80),
    'boss': (200, 0, 255),
    'laser': (0, 255, 200),
    'shotgun': (255, 220, 0),
    'missile': (255, 100, 0),
    'plasma': (150, 0, 255),
    'ui': (200, 200, 255),
    'warning': (255, 80, 80),
    'good': (80, 255, 120),
    'heat': (255, 140, 0),
}

WEAPON_TYPES = {
    'laser': {'name': '激光炮', 'base_damage': 10, 'base_fire_rate': 150, 'heat_per_shot': 8},
    'shotgun': {'name': '散射霰弹', 'base_damage': 6, 'base_fire_rate': 350, 'heat_per_shot': 15, 'pellets': 5},
    'missile': {'name': '追踪导弹', 'base_damage': 35, 'base_fire_rate': 700, 'heat_per_shot': 20},
    'plasma': {'name': '等离子炮', 'base_damage': 80, 'base_fire_rate': 1200, 'heat_per_shot': 40},
}

UPGRADE_MULTIPLIERS = {
    1: {'damage': 1.0, 'fire_rate': 1.0, 'heat': 1.0},
    2: {'damage': 1.6, 'fire_rate': 0.75, 'heat': 0.9},
    3: {'damage': 2.5, 'fire_rate': 0.55, 'heat': 0.75},
}

ENEMY_TYPES = [
    'drone', 'kamikaze', 'fighter', 'bomber', 'shield_cruiser',
    'stealth_recon', 'sniper', 'tank', 'mother_ship'
]

BOSS_NAMES = ['毁灭者', '虚空之眼', '黑暗领主', '湮灭者', '死神']

MAX_PARTICLES = 3000
MAX_COMBO_TIME = 3000
SLOWMO_DURATION = 1500
DODGE_THRESHOLD = 40

HIGHSCORE_FILE = 'data/highscores.json'
REPLAY_DIR = 'data/replays/'

WAVE_BOSS_INTERVAL = 5
DIFFICULTY_BASE_SPAWN_RATE = 1500
DIFFICULTY_MIN_SPAWN_RATE = 400
