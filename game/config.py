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

ENEMY_INFO = {
    'drone': {'name': '侦察无人机', 'desc': '最常见的敌人，直线俯冲，血量低但数量多。'},
    'kamikaze': {'name': '自杀无人机', 'desc': '高速直冲玩家，撞击伤害极高，优先击落。'},
    'fighter': {'name': '战斗机', 'desc': '标准敌方战机，发射直线子弹，机动性一般。'},
    'bomber': {'name': '轰炸机', 'desc': '缓慢但皮厚，发射多发扇形子弹。'},
    'shield_cruiser': {'name': '护盾巡洋舰', 'desc': '拥有能量护盾，需先击破护盾才能造成伤害。'},
    'stealth_recon': {'name': '隐形侦察机', 'desc': '大部分时间隐身，靠近时才显形，射速快。'},
    'sniper': {'name': '狙击艇', 'desc': '远距离高伤害单发狙击，注意躲避红色预警弹。'},
    'tank': {'name': '重型坦克', 'desc': '超高血量重甲单位，移动缓慢但火力凶猛。'},
    'mother_ship': {'name': '母舰', 'desc': '大型敌舰，持续释放子机和弹幕，是战场核心目标。'},
}

BOSS_INFO = {
    '毁灭者': {'desc': '初代Boss，三阶段攻击模式，血量越低越狂暴。弱点会周期性暴露。'},
    '虚空之眼': {'desc': '凝视你的深渊之眼，全屏幕弹幕攻击，找到间隙穿越。'},
    '黑暗领主': {'desc': '拥有召唤能力的Boss，会持续召唤小怪助战，优先清理召唤物。'},
    '湮灭者': {'desc': '全身武器化的战争机器，每阶段切换不同武器组。'},
    '死神': {'desc': '最终Boss，拥有所有Boss的攻击模式集合，真正的死亡考验。'},
}

BOSS_NAMES = ['毁灭者', '虚空之眼', '黑暗领主', '湮灭者', '死神']

UPGRADE_OPTIONS = [
    {'id': 'weapon_upgrade', 'name': '武器强化', 'desc': '当前武器等级 +1（最高3级）', 'icon': 'W'},
    {'id': 'shield_up', 'name': '能量护盾', 'desc': '最大生命 +25，并回满生命', 'icon': 'S'},
    {'id': 'speed_up', 'name': '机动强化', 'desc': '移动速度 +20%', 'icon': 'M'},
    {'id': 'heat_down', 'name': '散热系统', 'desc': '所有武器过热冷却速度 +30%', 'icon': 'H'},
    {'id': 'damage_up', 'name': '伤害增幅', 'desc': '所有武器伤害 +15%', 'icon': 'D'},
    {'id': 'multi_shot', 'name': '多重射击', 'desc': '主武器额外增加 1 发弹丸', 'icon': '+'},
]

SHIP_SHAPE_STATS = [
    {'name': '经典战机', 'health_mult': 1.0, 'speed_mult': 1.0, 'damage_mult': 1.0},
    {'name': '重型战机', 'health_mult': 1.3, 'speed_mult': 0.85, 'damage_mult': 1.1},
    {'name': '轻型战机', 'health_mult': 0.8, 'speed_mult': 1.25, 'damage_mult': 0.95},
    {'name': '三角战机', 'health_mult': 0.95, 'speed_mult': 1.1, 'damage_mult': 1.05},
]

MAX_PARTICLES = 3000
MAX_COMBO_TIME = 3000
SLOWMO_DURATION = 1500
DODGE_THRESHOLD = 40

HIGHSCORE_FILE = 'data/highscores.json'
REPLAY_DIR = 'data/replays/'
BESTIARY_FILE = 'data/bestiary.json'

WAVE_BOSS_INTERVAL = 5
DIFFICULTY_BASE_SPAWN_RATE = 1500
DIFFICULTY_MIN_SPAWN_RATE = 400
