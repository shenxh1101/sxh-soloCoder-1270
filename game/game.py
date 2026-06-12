import random
import math
import copy
from game.config import *
from game.utils import StarField, circle_rect_collide, rects_collide
from game.particles import ParticleSystem
from game.player import Player
from game.enemies import Enemy
from game.boss import Boss
from game.weapons import Bullet
from game.audio import SoundManager
from game.difficulty import DifficultyManager
from game.score import HighScoreManager, ReplayManager, BestiaryManager
from game.ui import UIManager
from game.input import InputManager


class GameState:
    MENU = 'menu'
    PLAYING = 'playing'
    PAUSED = 'paused'
    GAME_OVER = 'game_over'
    HIGHSCORES = 'highscores'
    REPLAYS = 'replays'
    REPLAY_PLAYING = 'replay_playing'
    ENTER_NAME = 'enter_name'
    WAVE_NOTIFY = 'wave_notify'
    BOSS_INTRO = 'boss_intro'
    CUSTOMIZE = 'customize'
    HANGAR = 'hangar'
    UPGRADE_SELECT = 'upgrade_select'
    BESTIARY = 'bestiary'


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('太空射击 - 复古街机版')
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MENU
        self.menu_options = ['开始游戏', '双人合作', '机库', '敌人图鉴', '高分榜', '回放', '退出']
        self.menu_idx = 0
        self.hangar_idx = 0
        self.hangar_options = ['颜色', '外形', '初始武器', '默认升级路线', '返回']
        self.hangar_sub_idx = [0, 0, 0, 0]
        self.highscore_options = ['返回']
        self.highscore_idx = 0
        self.replay_options = ['返回']
        self.replay_idx = 0
        self.customize_idx = 0
        self.customize_options = ['颜色', '外形', '初始武器', '确认']
        self.bestiary_idx = 0
        self.bestiary_tab = 0
        self.bestiary_tabs = ['敌人', 'Boss']
        self.ship_colors = [
            ((0, 220, 255), '科技蓝'),
            ((255, 165, 0), '烈焰橙'),
            ((80, 255, 120), '翠绿'),
            ((255, 100, 200), '粉晶'),
            ((255, 255, 100), '金黄'),
            ((200, 150, 255), '紫晶'),
        ]
        self.ship_color_idx = 0
        self.ship_shapes = ['经典战机', '重型战机', '轻型战机', '三角战机']
        self.ship_shape_idx = 0
        self.start_weapon_idx = 0
        self.start_weapons = ['laser', 'shotgun', 'missile', 'plasma']
        self.start_upgrade_idx = 0
        self.start_upgrade_options = ['均衡强化', '火力优先', '速度优先', '防御优先']
        self.upgrade_options_current = []
        self.upgrade_select_idx = 0
        self.starfield = StarField()
        self.particles = ParticleSystem()
        self.audio = SoundManager()
        self.difficulty = DifficultyManager()
        self.highscores = HighScoreManager()
        self.replays = ReplayManager()
        self.bestiary = BestiaryManager()
        self.ui = UIManager()
        self.input = InputManager()
        self.players = []
        self.enemies = []
        self.enemy_bullets = []
        self.boss = None
        self.powerups = []
        self.spawn_timer = 0
        self.wave_notify_timer = 0
        self.boss_intro_timer = 0
        self.two_player_mode = False
        self.player_name_input = ''
        self.last_score = 0
        self.last_wave = 1
        self.replay_overlay_timer = 0
        self._prev_state = GameState.MENU
        self._init_powerup_drop_chance()

    def _init_powerup_drop_chance(self):
        self.powerup_chance = 0.08

    def reset_game(self, two_player=False):
        self.two_player_mode = two_player
        p1 = Player(1)
        p1.color = self.ship_colors[self.ship_color_idx][0]
        p1.shape_type = self.ship_shape_idx
        start_wep = self.start_weapons[self.start_weapon_idx]
        p1.current_weapon_idx = p1.weapon_order.index(start_wep)
        self._apply_start_upgrades(p1)
        self.players = [p1]
        if two_player:
            p2 = Player(2)
            p2.color = (255 - self.ship_colors[self.ship_color_idx][0][0],
                        255 - self.ship_colors[self.ship_color_idx][0][1],
                        255 - self.ship_colors[self.ship_color_idx][0][2])
            p2.shape_type = self.ship_shape_idx
            p2.current_weapon_idx = p2.weapon_order.index(start_wep)
            self._apply_start_upgrades(p2)
            self.players.append(p2)
        self.enemies = []
        self.enemy_bullets = []
        self.powerups = []
        self.boss = None
        self.difficulty = DifficultyManager()
        self.difficulty.enemies_in_wave = 5
        self.spawn_timer = 0
        self.replay_overlay_timer = 0
        if self.difficulty.wave % WAVE_BOSS_INTERVAL == 0:
            self.boss = Boss(self.difficulty.wave)
            self.bestiary.record_boss(self.boss.name)
            self.state = GameState.BOSS_INTRO
            self.boss_intro_timer = 3000
            self.audio.play_boss_intro()
        else:
            self.wave_notify_timer = 2000
            self.state = GameState.WAVE_NOTIFY
        if not self.replays.replaying:
            self.replays.start_recording()

    def _apply_start_upgrades(self, player):
        route = self.start_upgrade_idx
        if route == 0:
            player.apply_upgrade('weapon_upgrade')
        elif route == 1:
            player.apply_upgrade('weapon_upgrade')
            player.apply_upgrade('damage_up')
        elif route == 2:
            player.apply_upgrade('speed_up')
            player.apply_upgrade('heat_down')
        elif route == 3:
            player.apply_upgrade('shield_up')
            player.apply_upgrade('damage_up')

    def start_new_wave(self):
        self.difficulty.start_new_wave()
        self.enemies = []
        self.enemy_bullets = []
        self.powerups = []
        self.spawn_timer = 0
        if self.difficulty.wave % WAVE_BOSS_INTERVAL == 0:
            self.boss = Boss(self.difficulty.wave)
            self.bestiary.record_boss(self.boss.name)
            self.state = GameState.BOSS_INTRO
            self.boss_intro_timer = 3000
            self.audio.play_boss_intro()
        else:
            self.boss = None
            self.difficulty.enemies_in_wave = 5 + self.difficulty.wave * 3
            self.wave_notify_timer = 2000
            self.state = GameState.WAVE_NOTIFY

    def _start_upgrade_select(self):
        all_opts = UPGRADE_OPTIONS[:]
        random.shuffle(all_opts)
        self.upgrade_options_current = all_opts[:3]
        self.upgrade_select_idx = 0
        self.state = GameState.UPGRADE_SELECT

    def _apply_upgrade_to_all(self, upgrade_id):
        for p in self.players:
            if p.alive:
                p.apply_upgrade(upgrade_id)
        self.audio.play_upgrade()

    def handle_upgrade_select_input(self):
        if self.input.is_key_pressed(pygame.K_LEFT) or self.input.is_key_pressed(pygame.K_a):
            self.upgrade_select_idx = (self.upgrade_select_idx - 1) % len(self.upgrade_options_current)
        if self.input.is_key_pressed(pygame.K_RIGHT) or self.input.is_key_pressed(pygame.K_d):
            self.upgrade_select_idx = (self.upgrade_select_idx + 1) % len(self.upgrade_options_current)
        if self.input.is_key_pressed(pygame.K_RETURN) or self.input.is_key_pressed(pygame.K_SPACE):
            if self.upgrade_options_current:
                self._apply_upgrade_to_all(self.upgrade_options_current[self.upgrade_select_idx]['id'])
            self.start_new_wave()

    def spawn_enemy(self):
        enemy_type = self.difficulty.pick_enemy_type()
        enemy = Enemy(enemy_type, difficulty=self.difficulty.difficulty_score)
        self.enemies.append(enemy)
        self.difficulty.enemies_spawned_in_wave += 1
        self.bestiary.record_encounter(enemy_type)

    def spawn_powerup(self, x, y):
        if random.random() > self.powerup_chance:
            return
        types = ['health', 'weapon_upgrade', 'life']
        weights = [50, 40, 10]
        total = sum(weights)
        r = random.randint(1, total)
        cumulative = 0
        ptype = 'health'
        for t, w in zip(types, weights):
            cumulative += w
            if r <= cumulative:
                ptype = t
                break
        self.powerups.append({
            'x': x, 'y': y,
            'type': ptype,
            'vy': 80,
            'bob': random.random() * math.pi * 2,
            'alive': True,
        })

    def handle_menu_input(self):
        if self.input.is_key_pressed(pygame.K_UP) or self.input.is_key_pressed(pygame.K_w):
            self.menu_idx = (self.menu_idx - 1) % len(self.menu_options)
        if self.input.is_key_pressed(pygame.K_DOWN) or self.input.is_key_pressed(pygame.K_s):
            self.menu_idx = (self.menu_idx + 1) % len(self.menu_options)
        if self.input.is_key_pressed(pygame.K_RETURN) or self.input.is_key_pressed(pygame.K_SPACE):
            if self.menu_idx == 0:
                self.reset_game(two_player=False)
            elif self.menu_idx == 1:
                self.reset_game(two_player=True)
            elif self.menu_idx == 2:
                self._prev_state = GameState.MENU
                self.state = GameState.HANGAR
                self.hangar_idx = 0
            elif self.menu_idx == 3:
                self._prev_state = GameState.MENU
                self.state = GameState.BESTIARY
                self.bestiary_idx = 0
                self.bestiary_tab = 0
            elif self.menu_idx == 4:
                self._prev_state = GameState.MENU
                self.state = GameState.HIGHSCORES
            elif self.menu_idx == 5:
                self._prev_state = GameState.MENU
                self.state = GameState.REPLAYS
                self._refresh_replay_list()
            elif self.menu_idx == 6:
                self.running = False

    def handle_hangar_input(self):
        if self.input.is_key_pressed(pygame.K_ESCAPE):
            self.state = self._prev_state
            return
        if self.input.is_key_pressed(pygame.K_UP) or self.input.is_key_pressed(pygame.K_w):
            self.hangar_idx = (self.hangar_idx - 1) % len(self.hangar_options)
        if self.input.is_key_pressed(pygame.K_DOWN) or self.input.is_key_pressed(pygame.K_s):
            self.hangar_idx = (self.hangar_idx + 1) % len(self.hangar_options)
        cur = self.hangar_idx
        if self.input.is_key_pressed(pygame.K_LEFT) or self.input.is_key_pressed(pygame.K_a):
            if cur == 0:
                self.ship_color_idx = (self.ship_color_idx - 1) % len(self.ship_colors)
            elif cur == 1:
                self.ship_shape_idx = (self.ship_shape_idx - 1) % len(self.ship_shapes)
            elif cur == 2:
                self.start_weapon_idx = (self.start_weapon_idx - 1) % len(self.start_weapons)
            elif cur == 3:
                self.start_upgrade_idx = (self.start_upgrade_idx - 1) % len(self.start_upgrade_options)
        if self.input.is_key_pressed(pygame.K_RIGHT) or self.input.is_key_pressed(pygame.K_d):
            if cur == 0:
                self.ship_color_idx = (self.ship_color_idx + 1) % len(self.ship_colors)
            elif cur == 1:
                self.ship_shape_idx = (self.ship_shape_idx + 1) % len(self.ship_shapes)
            elif cur == 2:
                self.start_weapon_idx = (self.start_weapon_idx + 1) % len(self.start_weapons)
            elif cur == 3:
                self.start_upgrade_idx = (self.start_upgrade_idx + 1) % len(self.start_upgrade_options)
        if (self.input.is_key_pressed(pygame.K_RETURN) or self.input.is_key_pressed(pygame.K_SPACE)):
            if cur == len(self.hangar_options) - 1:
                self.state = self._prev_state

    def handle_bestiary_input(self):
        if self.input.is_key_pressed(pygame.K_ESCAPE):
            self.state = self._prev_state
            return
        if self.input.is_key_pressed(pygame.K_TAB) or self.input.is_key_pressed(pygame.K_q):
            self.bestiary_tab = (self.bestiary_tab + 1) % 2
            self.bestiary_idx = 0
        if self.bestiary_tab == 0:
            items = ENEMY_TYPES
        else:
            items = BOSS_NAMES
        if self.input.is_key_pressed(pygame.K_UP) or self.input.is_key_pressed(pygame.K_w):
            self.bestiary_idx = (self.bestiary_idx - 1) % len(items)
        if self.input.is_key_pressed(pygame.K_DOWN) or self.input.is_key_pressed(pygame.K_s):
            self.bestiary_idx = (self.bestiary_idx + 1) % len(items)

    def handle_customize_input(self):
        if self.input.is_key_pressed(pygame.K_ESCAPE):
            self.state = GameState.MENU
            return
        if self.input.is_key_pressed(pygame.K_UP) or self.input.is_key_pressed(pygame.K_w):
            self.customize_idx = (self.customize_idx - 1) % len(self.customize_options)
        if self.input.is_key_pressed(pygame.K_DOWN) or self.input.is_key_pressed(pygame.K_s):
            self.customize_idx = (self.customize_idx + 1) % len(self.customize_options)
        if self.input.is_key_pressed(pygame.K_LEFT) or self.input.is_key_pressed(pygame.K_a):
            if self.customize_idx == 0:
                self.ship_color_idx = (self.ship_color_idx - 1) % len(self.ship_colors)
            elif self.customize_idx == 1:
                self.ship_shape_idx = (self.ship_shape_idx - 1) % len(self.ship_shapes)
            elif self.customize_idx == 2:
                self.start_weapon_idx = (self.start_weapon_idx - 1) % len(self.start_weapons)
        if self.input.is_key_pressed(pygame.K_RIGHT) or self.input.is_key_pressed(pygame.K_d):
            if self.customize_idx == 0:
                self.ship_color_idx = (self.ship_color_idx + 1) % len(self.ship_colors)
            elif self.customize_idx == 1:
                self.ship_shape_idx = (self.ship_shape_idx + 1) % len(self.ship_shapes)
            elif self.customize_idx == 2:
                self.start_weapon_idx = (self.start_weapon_idx + 1) % len(self.start_weapons)
        if self.input.is_key_pressed(pygame.K_RETURN) or self.input.is_key_pressed(pygame.K_SPACE):
            if self.customize_idx == len(self.customize_options) - 1:
                self.state = GameState.MENU

    def handle_highscore_input(self):
        if self.input.is_key_pressed(pygame.K_ESCAPE) or self.input.is_key_pressed(pygame.K_RETURN):
            self.state = GameState.MENU

    def handle_replay_input(self):
        if self.input.is_key_pressed(pygame.K_ESCAPE):
            self.state = GameState.MENU
            return
        replay_list = self.replays.list_replays()
        options = replay_list + ['返回']
        if self.input.is_key_pressed(pygame.K_UP) or self.input.is_key_pressed(pygame.K_w):
            self.replay_idx = (self.replay_idx - 1) % len(options)
        if self.input.is_key_pressed(pygame.K_DOWN) or self.input.is_key_pressed(pygame.K_s):
            self.replay_idx = (self.replay_idx + 1) % len(options)
        if self.input.is_key_pressed(pygame.K_RETURN) or self.input.is_key_pressed(pygame.K_SPACE):
            if self.replay_idx == len(options) - 1:
                self.state = GameState.MENU
            elif replay_list and self.replay_idx < len(replay_list):
                name = replay_list[self.replay_idx]
                if self.replays.load_replay(name):
                    self.players = [Player(1)]
                    self.enemies = []
                    self.enemy_bullets = []
                    self.boss = None
                    self.powerups = []
                    self.state = GameState.REPLAY_PLAYING

    def _refresh_replay_list(self):
        replay_list = self.replays.list_replays()
        self.replay_options = replay_list + ['返回']
        self.replay_idx = 0

    def handle_playing_input(self, dt):
        if self.input.is_key_pressed(pygame.K_ESCAPE):
            self.state = GameState.PAUSED
        if self.input.is_key_pressed(pygame.K_1):
            self.players[0].select_weapon(0)
        if self.input.is_key_pressed(pygame.K_2):
            self.players[0].select_weapon(1)
        if self.input.is_key_pressed(pygame.K_3):
            self.players[0].select_weapon(2)
        if self.input.is_key_pressed(pygame.K_4):
            self.players[0].select_weapon(3)
        if self.input.is_key_pressed(pygame.K_q):
            self.players[0].switch_weapon(-1)
        if self.input.is_key_pressed(pygame.K_e):
            self.players[0].switch_weapon(1)
        p1_keys = self.input.get_player_keys(1)
        current_time = pygame.time.get_ticks()
        for i, player in enumerate(self.players):
            if not player.alive:
                continue
            keys = p1_keys if i == 0 else self.input.get_player_keys(2)
            player.update(dt, keys, self.enemies, self.enemy_bullets, self.particles, current_time)
            new_bullets = player.fire(current_time)
            if new_bullets:
                player.bullets.extend(new_bullets)
                self.audio.play_shoot(player.current_weapon.type)
        if not self.replays.replaying:
            self._record_replay_frame()

    def handle_paused_input(self):
        if self.input.is_key_pressed(pygame.K_ESCAPE):
            self.state = GameState.PLAYING

    def handle_enter_name_input(self):
        for event in self._text_events:
            if event.type == pygame.TEXTINPUT:
                if len(self.player_name_input) < 10:
                    self.player_name_input += event.text
        if self.input.is_key_pressed(pygame.K_BACKSPACE):
            self.player_name_input = self.player_name_input[:-1]
        if self.input.is_key_pressed(pygame.K_RETURN) and self.player_name_input.strip():
            rank = self.highscores.add_score(
                self.player_name_input.strip()[:10], self.last_score, self.last_wave
            )
            self.player_name_input = ''
            self.state = GameState.HIGHSCORES

    def _record_replay_frame(self):
        frame = {
            'time': pygame.time.get_ticks(),
            'players': [],
            'enemies': [],
            'player_bullets': [],
            'enemy_bullets': [],
            'boss': None,
            'score': sum(p.score for p in self.players),
            'wave': self.difficulty.wave,
            'explosions': [],
        }
        for p in self.players:
            frame['players'].append({
                'x': p.x, 'y': p.y, 'alive': p.alive,
                'health': p.health, 'weapon': p.weapon_order[p.current_weapon_idx],
                'weapon_level': p.current_weapon.level,
                'shape_type': getattr(p, 'shape_type', 0),
                'color': list(p.color),
            })
            for b in p.bullets:
                if b.alive:
                    frame['player_bullets'].append({
                        'x': b.x, 'y': b.y, 'radius': b.radius,
                        'color': list(b.color), 'weapon_type': b.weapon_type,
                    })
        for e in self.enemies:
            frame['enemies'].append({
                'x': e.x, 'y': e.y, 'type': e.type, 'alive': e.alive,
                'health': e.health, 'max_health': e.max_health,
            })
        for b in self.enemy_bullets:
            if b.alive:
                frame['enemy_bullets'].append({
                    'x': b.x, 'y': b.y, 'radius': b.radius,
                    'color': list(b.color), 'weapon_type': b.weapon_type,
                })
        if self.boss and self.boss.alive:
            frame['boss'] = {
                'x': self.boss.x, 'y': self.boss.y,
                'health': self.boss.health, 'max_health': self.boss.max_health,
                'phase': self.boss.phase, 'name': self.boss.name,
                'weakpoint_active': self.boss.weakpoint_active,
            }
        self.replays.record_frame(frame)

    def check_collisions(self):
        all_player_bullets = []
        for p in self.players:
            all_player_bullets.extend(p.bullets)
        for bullet in all_player_bullets:
            if not bullet.alive or not bullet.is_player:
                continue
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if id(enemy) in bullet.hit_enemies:
                    continue
                if circle_rect_collide(bullet.x, bullet.y, bullet.radius, enemy.rect):
                    enemy.take_damage(bullet.damage)
                    bullet.hit_enemies.add(id(enemy))
                    for player in self.players:
                        if player.alive:
                            player.add_score(enemy.score // 5)
                    self.difficulty.on_damage_dealt(bullet.damage)
                    self.particles.hit_spark(bullet.x, bullet.y, bullet.color)
                    self.audio.play_hit()
                    if bullet.pierce > 0:
                        bullet.pierce -= 1
                    else:
                        bullet.alive = False
                    if not enemy.alive:
                        for player in self.players:
                            if player.alive:
                                player.add_score(enemy.score)
                        explosion_size = 'medium'
                        if enemy.type in ('tank', 'mother_ship', 'shield_cruiser'):
                            explosion_size = 'large'
                        elif enemy.type in ('drone', 'kamikaze'):
                            explosion_size = 'small'
                        self.particles.explosion(enemy.x, enemy.y, explosion_size, enemy.color)
                        self.audio.play_explosion(explosion_size)
                        self.spawn_powerup(enemy.x, enemy.y)
                        self.difficulty.on_enemy_killed()
                        self.bestiary.record_kill(enemy.type)
                    break
            if not bullet.alive:
                continue
            if self.boss and self.boss.alive and not self.boss.entrance:
                if circle_rect_collide(bullet.x, bullet.y, bullet.radius, self.boss.rect):
                    was_weak = self.boss.take_damage(bullet.damage, bullet.x, bullet.y)
                    self.difficulty.on_damage_dealt(bullet.damage)
                    spark_color = (255, 255, 0) if was_weak else bullet.color
                    self.particles.hit_spark(bullet.x, bullet.y, spark_color)
                    self.audio.play_hit()
                    if was_weak:
                        for player in self.players:
                            if player.alive:
                                player.add_score(100)
                    if bullet.pierce > 0:
                        bullet.pierce -= 1
                    else:
                        bullet.alive = False
                    if self.boss.update_phase():
                        self.particles.explosion(self.boss.x, self.boss.y, 'large', COLORS['boss'])
                        self.audio.play_explosion('large')
                        self.audio.play_warning()
                    if not self.boss.alive:
                        for player in self.players:
                            if player.alive:
                                player.add_score(2000)
                        for _ in range(5):
                            self.particles.explosion(
                                self.boss.x + random.randint(-50, 50),
                                self.boss.y + random.randint(-30, 30),
                                'boss', COLORS['boss']
                            )
                        self.audio.play_explosion('boss')
                        self.bestiary.record_boss_kill(self.boss.name)
                        self.difficulty.wave_complete = True
                        self.boss = None
        for player in self.players:
            if not player.alive:
                continue
            for bullet in self.enemy_bullets:
                if not bullet.alive:
                    continue
                if circle_rect_collide(bullet.x, bullet.y, bullet.radius, player.rect):
                    if player.take_damage(bullet.damage):
                        self.difficulty.on_player_damage_taken(bullet.damage)
                        self.particles.explosion(player.x, player.y, 'small', (255, 100, 100))
                        self.audio.play_hit()
                    bullet.alive = False
        for player in self.players:
            if not player.alive:
                continue
            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if rects_collide(player.rect, enemy.rect):
                    if player.take_damage(enemy.damage):
                        self.difficulty.on_player_damage_taken(enemy.damage)
                    if enemy.type == 'kamikaze':
                        enemy.alive = False
                        self.particles.explosion(enemy.x, enemy.y, 'medium', enemy.color)
                        self.audio.play_explosion('medium')
                        self.difficulty.on_enemy_killed()
        for player in self.players:
            if not player.alive:
                continue
            if self.boss and self.boss.alive and not self.boss.entrance:
                if rects_collide(player.rect, self.boss.rect):
                    player.take_damage(30)
                    self.difficulty.on_player_damage_taken(30)
        for player in self.players:
            if not player.alive:
                continue
            for pu in self.powerups:
                if not pu['alive']:
                    continue
                d = math.hypot(player.x - pu['x'], player.y - pu['y'])
                if d < 30:
                    pu['alive'] = False
                    self._apply_powerup(player, pu['type'])
                    self.audio.play_upgrade()

    def _apply_powerup(self, player, ptype):
        if ptype == 'health':
            player.health = min(player.max_health, player.health + 30)
            self.particles.emit(player.x, player.y, 20, (80, 255, 120),
                                (50, 150), (300, 600), (2, 5))
        elif ptype == 'weapon_upgrade':
            if player.upgrade_current_weapon():
                self.particles.emit(player.x, player.y, 30, (255, 220, 0),
                                    (80, 200), (400, 800), (3, 6))
        elif ptype == 'life':
            player.lives = min(5, player.lives + 1)
            self.particles.emit(player.x, player.y, 40, (255, 100, 200),
                                (100, 250), (500, 1000), (3, 7))

    def update_dodge_slowmo(self):
        for p in self.players:
            if p.alive and p.check_dodge(self.enemies, self.enemy_bullets):
                self.audio.play_dodge()

    def get_global_time_scale(self):
        scale = 1.0
        for p in self.players:
            if p.alive:
                scale = min(scale, p.get_time_scale())
        return scale

    def update(self, dt):
        self.input.clear_pressed()
        self._text_events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.TEXTINPUT:
                self._text_events.append(event)
            else:
                self.input.process_event(event)
        if self.state == GameState.MENU:
            self.handle_menu_input()
            self.starfield.update(dt)
        elif self.state == GameState.CUSTOMIZE:
            self.handle_customize_input()
            self.starfield.update(dt)
        elif self.state == GameState.HIGHSCORES:
            self.handle_highscore_input()
        elif self.state == GameState.REPLAYS:
            self.handle_replay_input()
        elif self.state == GameState.ENTER_NAME:
            self.handle_enter_name_input()
        elif self.state == GameState.WAVE_NOTIFY:
            self.wave_notify_timer -= dt
            if self.wave_notify_timer <= 0:
                self.state = GameState.PLAYING
        elif self.state == GameState.BOSS_INTRO:
            self.boss_intro_timer -= dt
            if self.boss_intro_timer <= 0:
                self.state = GameState.PLAYING
        elif self.state == GameState.PAUSED:
            self.handle_paused_input()
        elif self.state == GameState.REPLAY_PLAYING:
            self._handle_replay_playing(dt)
        elif self.state == GameState.PLAYING:
            self.handle_playing_input(dt)
            time_scale = self.get_global_time_scale()
            scaled_dt = dt * time_scale
            self.starfield.update(scaled_dt)
            self.particles.update(scaled_dt)
            self.audio.update(dt)
            total_enemies = len([e for e in self.enemies if e.alive])
            intensity = min(1.0, total_enemies / 12 + (0.6 if self.boss and self.boss.alive else 0))
            self.audio.set_intensity(intensity)
            current_time = pygame.time.get_ticks()
            if (not self.boss or not self.boss.alive) and self.difficulty.wave % WAVE_BOSS_INTERVAL != 0:
                self.spawn_timer += dt
                if self.spawn_timer >= self.difficulty.current_spawn_rate:
                    self.spawn_timer = 0
                    if self.difficulty.enemies_in_wave > len([e for e in self.enemies if e.alive]):
                        self.spawn_enemy()
            for enemy in self.enemies:
                if enemy.alive:
                    try:
                        new_bullets = enemy.update(scaled_dt, self.players, self.particles, current_time)
                        self.enemy_bullets.extend(new_bullets)
                    except Exception:
                        pass
                if enemy.y > SCREEN_HEIGHT + 50 and enemy.alive:
                    enemy.alive = False
                    self.difficulty.on_enemy_escaped()
            self.enemies = [e for e in self.enemies if e.alive]
            if self.boss and self.boss.alive:
                try:
                    boss_bullets = self.boss.update(scaled_dt, self.players, current_time, self.particles)
                    self.enemy_bullets.extend(boss_bullets)
                except Exception:
                    pass
            for b in self.enemy_bullets:
                try:
                    b.update(scaled_dt)
                except Exception:
                    b.alive = False
            self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]
            for p in self.players:
                for b in p.bullets:
                    try:
                        b.update(scaled_dt, self.enemies, self.players)
                    except Exception:
                        b.alive = False
                p.bullets = [b for b in p.bullets if b.alive]
            try:
                self.check_collisions()
            except Exception:
                pass
            self.update_dodge_slowmo()
            for pu in self.powerups:
                if pu['alive']:
                    pu['y'] += pu['vy'] * scaled_dt / 1000
                    pu['bob'] += scaled_dt / 200
                    if pu['y'] > SCREEN_HEIGHT + 30:
                        pu['alive'] = False
            self.powerups = [p for p in self.powerups if p['alive']]
            alive_players = [p for p in self.players if p.alive]
            if not alive_players:
                self.last_score = sum(p.score for p in self.players)
                self.last_wave = self.difficulty.wave
                self.replays.stop_recording()
                self.replays.save_replay()
                if self.highscores.is_high_score(self.last_score):
                    self.player_name_input = ''
                    self.state = GameState.ENTER_NAME
                else:
                    self.state = GameState.GAME_OVER
            elif self.difficulty.wave_complete:
                self._start_upgrade_select()
        elif self.state == GameState.UPGRADE_SELECT:
            self.handle_upgrade_select_input()
            self.starfield.update(dt)
        elif self.state == GameState.HANGAR:
            self.handle_hangar_input()
            self.starfield.update(dt)
        elif self.state == GameState.BESTIARY:
            self.handle_bestiary_input()
            self.starfield.update(dt)
        elif self.state == GameState.GAME_OVER:
            if self.input.is_key_pressed(pygame.K_RETURN) or self.input.is_key_pressed(pygame.K_ESCAPE):
                self.state = GameState.MENU

    def _handle_replay_playing(self, dt):
        if self.input.is_key_pressed(pygame.K_ESCAPE):
            self.replays.stop_replay()
            self.state = GameState.REPLAYS
            return
        frame = self.replays.get_next_frame()
        if frame is None:
            self.replays.stop_replay()
            self.replay_overlay_timer = 2000
            self.state = GameState.REPLAYS
            return
        self._update_replay_from_frame(frame)
        self.starfield.update(dt * 0.5)
        self.particles.update(dt * 0.5)
        self.replay_overlay_timer += dt

    def _update_replay_from_frame(self, frame):
        if 'players' in frame:
            for i, pf in enumerate(frame['players']):
                if i < len(self.players):
                    p = self.players[i]
                    p.x = pf.get('x', p.x)
                    p.y = pf.get('y', p.y)
                    p.alive = pf.get('alive', True)
                    p.health = pf.get('health', 100)
                    if 'color' in pf:
                        p.color = tuple(pf['color'])
                    if 'shape_type' in pf:
                        p.shape_type = pf['shape_type']
                    if 'weapon' in pf and hasattr(p, 'weapon_order'):
                        try:
                            p.current_weapon_idx = p.weapon_order.index(pf['weapon'])
                        except (ValueError, AttributeError):
                            pass
        if 'enemies' in frame:
            self.enemies = []
            for ef in frame['enemies']:
                if ef.get('alive', True):
                    try:
                        e = Enemy(ef.get('type', 'drone'), ef.get('x', 0), ef.get('y', 0))
                        e.spawn_animation = 0
                        e.health = ef.get('health', e.max_health)
                        e.max_health = ef.get('max_health', e.max_health)
                        self.enemies.append(e)
                    except Exception:
                        pass
        if 'player_bullets' in frame:
            for i, p in enumerate(self.players):
                p.bullets = []
            for idx, bf in enumerate(frame['player_bullets']):
                pidx = idx % max(1, len(self.players))
                if pidx < len(self.players):
                    try:
                        b = Bullet(
                            bf.get('x', 0), bf.get('y', 0),
                            0, 0, 0,
                            bf.get('weapon_type', 'laser'),
                            tuple(bf.get('color', (255, 255, 255))),
                            True, bf.get('radius', 3)
                        )
                        self.players[pidx].bullets.append(b)
                    except Exception:
                        pass
        if 'enemy_bullets' in frame:
            self.enemy_bullets = []
            for bf in frame['enemy_bullets']:
                try:
                    b = Bullet(
                        bf.get('x', 0), bf.get('y', 0),
                        0, 0, 0,
                        bf.get('weapon_type', 'laser'),
                        tuple(bf.get('color', (255, 100, 100))),
                        False, bf.get('radius', 3)
                    )
                    self.enemy_bullets.append(b)
                except Exception:
                    pass
        if 'boss' in frame and frame['boss']:
            if not self.boss or not self.boss.alive:
                try:
                    self.boss = Boss(5)
                    self.boss.entrance = False
                except Exception:
                    pass
            if self.boss:
                self.boss.x = frame['boss'].get('x', self.boss.x)
                self.boss.y = frame['boss'].get('y', self.boss.y)
                self.boss.health = frame['boss'].get('health', self.boss.health)
                self.boss.max_health = frame['boss'].get('max_health', self.boss.max_health)
                self.boss.phase = frame['boss'].get('phase', 0)
                self.boss.name = frame['boss'].get('name', self.boss.name)
                self.boss.weakpoint_active = frame['boss'].get('weakpoint_active', False)
        else:
            self.boss = None
        if 'score' in frame:
            self.last_score = frame['score']
        if 'wave' in frame:
            self.last_wave = frame['wave']

    def draw(self):
        self.screen.fill(COLORS['bg'])
        self.starfield.draw(self.screen)
        if self.state in (GameState.PLAYING, GameState.PAUSED, GameState.WAVE_NOTIFY,
                          GameState.BOSS_INTRO, GameState.GAME_OVER, GameState.ENTER_NAME,
                          GameState.REPLAY_PLAYING):
            for p in self.powerups:
                if p['alive']:
                    offset = math.sin(p['bob']) * 5
                    color = (80, 255, 120) if p['type'] == 'health' else \
                            (255, 220, 0) if p['type'] == 'weapon_upgrade' else (255, 100, 200)
                    pygame.draw.circle(self.screen, color,
                                       (int(p['x']), int(p['y'] + offset)), 12)
                    pygame.draw.circle(self.screen, (255, 255, 255),
                                       (int(p['x']), int(p['y'] + offset)), 12, 2)
                    letter = 'H' if p['type'] == 'health' else 'U' if p['type'] == 'weapon_upgrade' else 'L'
                    self.ui.draw_text(self.screen, letter, p['x'], p['y'] + offset - 6,
                                      (0, 0, 0), self.ui.font_small, center=True)
            for enemy in self.enemies:
                enemy.draw(self.screen)
            if self.boss and self.boss.alive:
                self.boss.draw(self.screen)
            for bullet in self.enemy_bullets:
                bullet.draw(self.screen, self.particles)
            for p in self.players:
                for b in p.bullets:
                    b.draw(self.screen, self.particles)
            self.particles.draw(self.screen)
            for player in self.players:
                player.draw(self.screen)
            for i, player in enumerate(self.players):
                self.ui.draw_player_hud(self.screen, player, is_p2=(i == 1))
            if self.state == GameState.REPLAY_PLAYING:
                total_score = self.last_score
                max_combo = 0
                max_mult = 1.0
                wave = self.last_wave
            else:
                total_score = sum(p.score for p in self.players)
                max_combo = max((p.combo for p in self.players), default=0)
                max_mult = max((p.score_multiplier for p in self.players), default=1.0)
                wave = self.difficulty.wave
            self.ui.draw_score(self.screen, total_score, max_combo, max_mult, wave)
            if self.boss and self.boss.alive:
                self.ui.draw_boss_health(self.screen, self.boss)
            for p in self.players:
                if p.alive and p.slowmo_active:
                    self.ui.draw_slowmo_indicator(self.screen, True, p.slowmo_timer, SLOWMO_DURATION)
                    break
            if self.state == GameState.REPLAY_PLAYING:
                pygame.draw.rect(self.screen, (0, 0, 0, 150), (0, 0, 180, 40))
                self.ui.draw_text(self.screen, '回 放 中  [ESC 退出]',
                                  10, 12, (255, 200, 100), self.ui.font_small)
        if self.state == GameState.MENU:
            self.ui.draw_menu(self.screen, '太空射击', self.menu_options, self.menu_idx)
            self.ui.draw_controls(self.screen, 40, SCREEN_HEIGHT - 140, is_p2=False)
            if self.input.get_joystick_count() > 0:
                self.ui.draw_text(self.screen, f'检测到 {self.input.get_joystick_count()} 个手柄',
                                  SCREEN_WIDTH - 200, SCREEN_HEIGHT - 40, (100, 255, 100))
        elif self.state == GameState.HIGHSCORES:
            scores = self.highscores.get_top_scores(10)
            self.ui.draw_highscores(self.screen, scores, SCREEN_WIDTH // 2, 100)
            self.ui.draw_text(self.screen, '按 ESC 返回',
                              SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60,
                              COLORS['ui'], self.ui.font_small, center=True)
        elif self.state == GameState.REPLAYS:
            replay_list = self.replays.list_replays()
            options = replay_list + ['返回']
            self.ui.draw_menu(self.screen, '回放', options, self.replay_idx,
                              center_y=SCREEN_HEIGHT // 2 - 50)
        elif self.state == GameState.UPGRADE_SELECT:
            self._draw_upgrade_select()
        elif self.state == GameState.HANGAR:
            self._draw_hangar()
        elif self.state == GameState.BESTIARY:
            self._draw_bestiary()
        elif self.state == GameState.CUSTOMIZE:
            cx = SCREEN_WIDTH // 2
            cy = 100
            self.ui.draw_text_with_shadow(self.screen, '飞船自定义', cx, cy,
                                           (0, 220, 255), self.ui.font_large, center=True)
            preview_x = cx
            preview_y = 300
            preview_color = self.ship_colors[self.ship_color_idx][0]
            preview_surf = pygame.Surface((120, 140), pygame.SRCALPHA)
            tmp_player = Player(1)
            tmp_player.color = preview_color
            tmp_player.shape_type = self.ship_shape_idx
            tmp_player.width = 72
            tmp_player.height = 80
            tmp_player._draw_ship_shape(preview_surf, 60, 70, preview_color)
            self.screen.blit(preview_surf, (preview_x - 60, preview_y - 70))
            pygame.draw.polygon(self.screen, (255, 180, 50), [
                (preview_x - 10, preview_y + 45),
                (preview_x, preview_y + 65 + int(math.sin(pygame.time.get_ticks() / 100) * 4)),
                (preview_x + 10, preview_y + 45),
            ])
            for i, opt in enumerate(self.customize_options):
                item_y = 420 + i * 45
                color = (255, 255, 255) if i == self.customize_idx else (150, 150, 180)
                if i == 0:
                    val = self.ship_colors[self.ship_color_idx][1]
                elif i == 1:
                    val = self.ship_shapes[self.ship_shape_idx]
                elif i == 2:
                    wp_names = {'laser': '激光炮', 'shotgun': '霰弹枪',
                                'missile': '追踪导弹', 'plasma': '等离子炮'}
                    val = wp_names.get(self.start_weapons[self.start_weapon_idx], '未知')
                else:
                    val = ''
                arrow = ' <' if i == self.customize_idx else '  '
                arrow2 = '> ' if i == self.customize_idx else '  '
                display = f'{arrow2}{opt}' + (f':  {val}' if i < 3 else '') + arrow
                self.ui.draw_text(self.screen, display, cx, item_y, color,
                                  self.ui.font_medium, center=True)
            self.ui.draw_text(self.screen, '按 ←/→ 更改选项  ↓/↑ 切换  ESC 或确认返回',
                              cx, SCREEN_HEIGHT - 60, (100, 150, 200), self.ui.font_small, center=True)
        elif self.state == GameState.WAVE_NOTIFY:
            self.ui.draw_wave_notification(self.screen, self.difficulty.wave)
        elif self.state == GameState.BOSS_INTRO:
            if self.boss:
                self.ui.draw_wave_notification(self.screen, self.difficulty.wave,
                                               is_boss=True, boss_name=self.boss.name)
        elif self.state == GameState.PAUSED:
            self.ui.draw_pause(self.screen)
        elif self.state == GameState.ENTER_NAME:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            self.ui.draw_text_with_shadow(self.screen, '新高分!',
                                           SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100,
                                           (255, 220, 100), self.ui.font_large, center=True)
            self.ui.draw_text(self.screen, f'得分: {self.last_score}  波次: {self.last_wave}',
                              SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40,
                              COLORS['ui'], self.ui.font_medium, center=True)
            self.ui.draw_text(self.screen, '输入名字:',
                              SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20,
                              COLORS['ui'], self.ui.font_medium, center=True)
            pygame.draw.rect(self.screen, (40, 40, 60),
                             (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 50, 300, 50),
                             border_radius=4)
            pygame.draw.rect(self.screen, (100, 100, 200),
                             (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 50, 300, 50), 2)
            self.ui.draw_text(self.screen, self.player_name_input + '_',
                              SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 65,
                              (255, 255, 255), self.ui.font_medium, center=True)
            self.ui.draw_text(self.screen, '按回车确认',
                              SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120,
                              (150, 150, 180), self.ui.font_small, center=True)
        elif self.state == GameState.GAME_OVER:
            is_hi = self.highscores.is_high_score(self.last_score)
            self.ui.draw_game_over(self.screen, self.last_score, self.last_wave, is_hi)
            self.ui.draw_text(self.screen, '按回车返回菜单',
                              SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120,
                              COLORS['ui'], self.ui.font_small, center=True)
        pygame.display.flip()

    def _draw_upgrade_select(self):
        cx = SCREEN_WIDTH // 2
        self.ui.draw_text_with_shadow(self.screen, '波次完成！选择强化', cx, 80,
                                       (255, 220, 100), self.ui.font_large, center=True)
        self.ui.draw_text(self.screen, f'即将进入第 {self.difficulty.wave + 1} 波',
                          cx, 130, (150, 200, 255), self.ui.font_small, center=True)
        n = len(self.upgrade_options_current)
        card_w = 220
        card_h = 280
        spacing = 40
        total_w = n * card_w + (n - 1) * spacing
        start_x = cx - total_w / 2 + card_w / 2
        for i, opt in enumerate(self.upgrade_options_current):
            x = start_x + i * (card_w + spacing)
            y = 200
            selected = (i == self.upgrade_select_idx)
            border_c = (255, 220, 100) if selected else (100, 100, 150)
            bg_c = (30, 30, 60) if selected else (20, 20, 40)
            pygame.draw.rect(self.screen, bg_c, (x - card_w / 2, y, card_w, card_h), border_radius=8)
            border_w = 3 if selected else 1
            pygame.draw.rect(self.screen, border_c, (x - card_w / 2, y, card_w, card_h), border_w, border_radius=8)
            icon_y = y + 50
            pygame.draw.circle(self.screen, (80, 255, 200), (int(x), int(icon_y)), 30)
            self.ui.draw_text(self.screen, opt['icon'], x, icon_y - 12,
                              (0, 0, 0), self.ui.font_large, center=True)
            name_y = y + 110
            self.ui.draw_text(self.screen, opt['name'], x, name_y,
                              (255, 255, 255), self.ui.font_medium, center=True)
            desc_y = y + 160
            desc_lines = self._wrap_text(opt['desc'], 180)
            for li, line in enumerate(desc_lines):
                self.ui.draw_text(self.screen, line, x, desc_y + li * 28,
                                  (200, 200, 220), self.ui.font_small, center=True)
            if selected:
                self.ui.draw_text(self.screen, '[ 空格 / 回车 确认 ]', x, y + card_h - 35,
                                  (255, 220, 100), self.ui.font_small, center=True)

    def _wrap_text(self, text, max_width):
        lines = []
        cur = ''
        for ch in text:
            cur += ch
            if len(cur) * 14 > max_width and ch in '，。、':
                lines.append(cur)
                cur = ''
        if cur:
            lines.append(cur)
        return lines

    def _draw_hangar(self):
        cx = SCREEN_WIDTH // 2
        self.ui.draw_text_with_shadow(self.screen, '机库', cx, 60,
                                       (0, 220, 255), self.ui.font_large, center=True)
        preview_x = cx - 200
        preview_y = 250
        preview_color = self.ship_colors[self.ship_color_idx][0]
        preview_surf = pygame.Surface((160, 180), pygame.SRCALPHA)
        tmp_player = Player(1)
        tmp_player.color = preview_color
        tmp_player.shape_type = self.ship_shape_idx
        tmp_player.width = 90
        tmp_player.height = 100
        tmp_player._draw_ship_shape(preview_surf, 80, 90, preview_color)
        self.screen.blit(preview_surf, (preview_x - 80, preview_y - 90))
        pygame.draw.polygon(self.screen, (255, 180, 50), [
            (preview_x - 14, preview_y + 55),
            (preview_x, preview_y + 85 + int(math.sin(pygame.time.get_ticks() / 100) * 6)),
            (preview_x + 14, preview_y + 55),
        ])
        stats = SHIP_SHAPE_STATS[self.ship_shape_idx]
        stat_y = preview_y + 120
        self.ui.draw_text(self.screen, f'生命: {int(100 * stats["health_mult"])}', preview_x, stat_y,
                          (180, 255, 180), self.ui.font_small, center=True)
        self.ui.draw_text(self.screen, f'速度: {int(380 * stats["speed_mult"])}', preview_x, stat_y + 24,
                          (255, 220, 150), self.ui.font_small, center=True)
        self.ui.draw_text(self.screen, f'伤害: {int(100 * stats["damage_mult"])}%', preview_x, stat_y + 48,
                          (255, 150, 150), self.ui.font_small, center=True)
        panel_x = cx + 120
        panel_y = 130
        for i, opt in enumerate(self.hangar_options):
            item_y = panel_y + i * 50
            color = (255, 255, 255) if i == self.hangar_idx else (150, 150, 180)
            if i == 0:
                val = self.ship_colors[self.ship_color_idx][1]
            elif i == 1:
                val = self.ship_shapes[self.ship_shape_idx]
            elif i == 2:
                wp_names = {'laser': '激光炮', 'shotgun': '霰弹枪',
                            'missile': '追踪导弹', 'plasma': '等离子炮'}
                val = wp_names.get(self.start_weapons[self.start_weapon_idx], '未知')
            elif i == 3:
                val = self.start_upgrade_options[self.start_upgrade_idx]
            else:
                val = ''
            arrow_l = '< ' if i == self.hangar_idx else '  '
            arrow_r = ' >' if i == self.hangar_idx else '  '
            display = f'{arrow_l}{opt}' + (f': {val}' if i < 4 else '') + arrow_r
            self.ui.draw_text(self.screen, display, panel_x, item_y, color,
                              self.ui.font_medium, center=True)
        self.ui.draw_text(self.screen, '按 ←/→ 更改  ↓/↑ 切换  ESC 返回',
                          cx, SCREEN_HEIGHT - 50, (100, 150, 200), self.ui.font_small, center=True)
        route_desc = [
            '均衡强化：初始武器 +1级',
            '火力优先：武器+伤害',
            '速度优先：速度+散热',
            '防御优先：护盾+伤害',
        ]
        self.ui.draw_text(self.screen, '升级路线效果：', panel_x, panel_y + 230,
                          (200, 200, 255), self.ui.font_small, center=True)
        self.ui.draw_text(self.screen, route_desc[self.start_upgrade_idx], panel_x, panel_y + 255,
                          (255, 220, 150), self.ui.font_small, center=True)

    def _draw_bestiary(self):
        cx = SCREEN_WIDTH // 2
        self.ui.draw_text_with_shadow(self.screen, '敌人图鉴', cx, 60,
                                       (255, 100, 100), self.ui.font_large, center=True)
        for i, tab in enumerate(self.bestiary_tabs):
            tx = cx - 80 + i * 160
            ty = 110
            selected = (i == self.bestiary_tab)
            color = (255, 255, 255) if selected else (120, 120, 150)
            bg = (60, 40, 80) if selected else (30, 30, 50)
            pygame.draw.rect(self.screen, bg, (tx - 60, ty - 20, 120, 40), border_radius=6)
            self.ui.draw_text(self.screen, tab, tx, ty - 8, color, self.ui.font_medium, center=True)
        self.ui.draw_text(self.screen, '按 Tab 切换', cx, 160,
                          (150, 150, 180), self.ui.font_small, center=True)
        if self.bestiary_tab == 0:
            items = ENEMY_TYPES
            info_map = ENEMY_INFO
            data_map = self.bestiary.get_enemy_data()
        else:
            items = BOSS_NAMES
            info_map = BOSS_INFO
            data_map = self.bestiary.get_boss_data()
        list_x = 100
        list_y = 200
        item_h = 40
        for i, key in enumerate(items):
            iy = list_y + i * item_h
            encountered = self.bestiary.is_encountered(key, is_boss=(self.bestiary_tab == 1))
            selected = (i == self.bestiary_idx)
            bg_c = (50, 50, 80) if selected else (30, 30, 50)
            name_color = (255, 255, 255) if encountered else (100, 100, 120)
            pygame.draw.rect(self.screen, bg_c, (list_x, iy, 280, item_h - 6), border_radius=4)
            if selected:
                pygame.draw.rect(self.screen, (255, 200, 100), (list_x, iy, 280, item_h - 6), 2, border_radius=4)
            display_name = info_map.get(key, {}).get('name', key) if encountered else '???'
            self.ui.draw_text(self.screen, display_name, list_x + 15, iy + 8,
                              name_color, self.ui.font_small)
            if encountered and key in data_map:
                kills = data_map[key].get('kills', 0)
                self.ui.draw_text(self.screen, f'击败: {kills}', list_x + 200, iy + 8,
                                  (150, 255, 150), self.ui.font_small)
        detail_x = 450
        detail_y = 200
        cur_key = items[self.bestiary_idx] if items else ''
        encountered = self.bestiary.is_encountered(cur_key, is_boss=(self.bestiary_tab == 1))
        if encountered:
            info = info_map.get(cur_key, {})
            name = info.get('name', cur_key)
            desc = info.get('desc', '')
            self.ui.draw_text(self.screen, name, detail_x, detail_y,
                              (255, 220, 100), self.ui.font_medium)
            desc_lines = self._wrap_text(desc, 400)
            for li, line in enumerate(desc_lines):
                self.ui.draw_text(self.screen, line, detail_x, detail_y + 50 + li * 30,
                                  (200, 200, 220), self.ui.font_small)
            if cur_key in data_map:
                kills = data_map[cur_key].get('kills', 0)
                self.ui.draw_text(self.screen, f'总击败数: {kills}', detail_x, detail_y + 180,
                                  (150, 255, 150), self.ui.font_medium)
        else:
            self.ui.draw_text(self.screen, '未发现', detail_x, detail_y,
                              (100, 100, 120), self.ui.font_medium)
            self.ui.draw_text(self.screen, '在战斗中遇到后解锁', detail_x, detail_y + 40,
                              (100, 100, 120), self.ui.font_small)
        self.ui.draw_text(self.screen, '按 ESC 返回', cx, SCREEN_HEIGHT - 40,
                          (150, 150, 180), self.ui.font_small, center=True)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.update(dt)
            self.draw()
        pygame.quit()
