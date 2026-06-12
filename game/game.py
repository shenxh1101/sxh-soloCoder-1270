import random
import math
from game.config import *
from game.utils import StarField, circle_rect_collide, rects_collide
from game.particles import ParticleSystem
from game.player import Player
from game.enemies import Enemy
from game.boss import Boss
from game.weapons import Bullet
from game.audio import SoundManager
from game.difficulty import DifficultyManager
from game.score import HighScoreManager, ReplayManager
from game.ui import UIManager
from game.input import InputManager


class GameState:
    MENU = 'menu'
    PLAYING = 'playing'
    PAUSED = 'paused'
    GAME_OVER = 'game_over'
    HIGHSCORES = 'highscores'
    REPLAYS = 'replays'
    ENTER_NAME = 'enter_name'
    WAVE_NOTIFY = 'wave_notify'
    BOSS_INTRO = 'boss_intro'


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('太空射击 - 复古街机版')
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState.MENU
        self.menu_options = ['开始游戏', '双人合作', '高分榜', '回放', '退出']
        self.menu_idx = 0
        self.highscore_options = ['返回']
        self.highscore_idx = 0
        self.replay_options = ['返回']
        self.replay_idx = 0
        self.starfield = StarField()
        self.particles = ParticleSystem()
        self.audio = SoundManager()
        self.difficulty = DifficultyManager()
        self.highscores = HighScoreManager()
        self.replays = ReplayManager()
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
        self._init_powerup_drop_chance()

    def _init_powerup_drop_chance(self):
        self.powerup_chance = 0.08

    def reset_game(self, two_player=False):
        self.two_player_mode = two_player
        self.players = [Player(1)]
        if two_player:
            self.players.append(Player(2))
        self.enemies = []
        self.enemy_bullets = []
        self.powerups = []
        self.boss = None
        self.difficulty = DifficultyManager()
        self.difficulty.enemies_in_wave = 5
        self.spawn_timer = 0
        self.wave_notify_timer = 2000
        self.state = GameState.WAVE_NOTIFY
        self.replays.start_recording()

    def start_new_wave(self):
        self.difficulty.start_new_wave()
        if self.difficulty.should_spawn_boss():
            self.boss = Boss(self.difficulty.wave)
            self.state = GameState.BOSS_INTRO
            self.boss_intro_timer = 3000
            self.audio.play_boss_intro()
        else:
            self.wave_notify_timer = 2000
            self.state = GameState.WAVE_NOTIFY

    def spawn_enemy(self):
        enemy_type = self.difficulty.pick_enemy_type()
        enemy = Enemy(enemy_type, difficulty=self.difficulty.difficulty_score)
        self.enemies.append(enemy)
        self.difficulty.enemies_spawned_in_wave += 1

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
                self.state = GameState.HIGHSCORES
            elif self.menu_idx == 3:
                self.state = GameState.REPLAYS
                self._refresh_replay_list()
            elif self.menu_idx == 4:
                self.running = False

    def handle_highscore_input(self):
        if self.input.is_key_pressed(pygame.K_ESCAPE) or self.input.is_key_pressed(pygame.K_RETURN):
            self.state = GameState.MENU

    def handle_replay_input(self):
        if self.input.is_key_pressed(pygame.K_ESCAPE):
            self.state = GameState.MENU
        replay_list = self.replays.list_replays()
        options = replay_list + ['返回']
        if self.input.is_key_pressed(pygame.K_UP) or self.input.is_key_pressed(pygame.K_w):
            self.replay_idx = (self.replay_idx - 1) % len(options)
        if self.input.is_key_pressed(pygame.K_DOWN) or self.input.is_key_pressed(pygame.K_s):
            self.replay_idx = (self.replay_idx + 1) % len(options)
        if self.input.is_key_pressed(pygame.K_RETURN) or self.input.is_key_pressed(pygame.K_SPACE):
            if self.replay_idx == len(options) - 1:
                self.state = GameState.MENU
            elif replay_list:
                name = replay_list[self.replay_idx]
                if self.replays.load_replay(name):
                    self.reset_game(two_player=False)
                    self.state = GameState.PLAYING

    def _refresh_replay_list(self):
        replay_list = self.replays.list_replays()
        self.replay_options = replay_list + ['返回']
        self.replay_idx = 0

    def handle_playing_input(self):
        if self.input.is_key_pressed(pygame.K_ESCAPE):
            self.state = GameState.PAUSED
        p1_keys = self.input.get_player_keys(1)
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
        for i, player in enumerate(self.players):
            if not player.alive:
                continue
            keys = p1_keys if i == 0 else self.input.get_player_keys(2)
            current_time = pygame.time.get_ticks()
            player.update(16, keys, self.enemies, self.enemy_bullets, self.particles, current_time)
            new_bullets = player.fire(current_time)
            if new_bullets:
                for b in new_bullets:
                    self.players[i].bullets.append(b)
                self.audio.play_shoot(player.current_weapon.type)
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
            'boss': None,
            'score': sum(p.score for p in self.players),
            'wave': self.difficulty.wave,
        }
        for p in self.players:
            frame['players'].append({
                'x': p.x, 'y': p.y, 'alive': p.alive,
                'health': p.health, 'weapon': p.weapon_order[p.current_weapon_idx],
            })
        for e in self.enemies:
            frame['enemies'].append({
                'x': e.x, 'y': e.y, 'type': e.type, 'alive': e.alive,
            })
        if self.boss and self.boss.alive:
            frame['boss'] = {'x': self.boss.x, 'y': self.boss.y, 'health': self.boss.health}
        self.replays.record_frame(frame)

    def check_collisions(self):
        current_time = pygame.time.get_ticks()
        for player in self.players:
            if not player.alive:
                continue
            for bullet_list in [p.bullets for p in self.players]:
                for bullet in bullet_list:
                    if not bullet.alive or not bullet.is_player:
                        continue
                    for enemy in self.enemies:
                        if not enemy.alive:
                            continue
                        if id(enemy) in bullet.hit_enemies:
                            continue
                        if circle_rect_collide(bullet.x, bullet.y, bullet.radius, enemy.rect):
                            was_crit = enemy.take_damage(bullet.damage)
                            bullet.hit_enemies.add(id(enemy))
                            player.add_score(enemy.score // 5)
                            self.difficulty.on_damage_dealt(bullet.damage)
                            self.particles.hit_spark(bullet.x, bullet.y, bullet.color)
                            self.audio.play_hit()
                            if bullet.pierce > 0:
                                bullet.pierce -= 1
                            else:
                                bullet.alive = False
                            if not enemy.alive:
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
                            break
            for player in self.players:
                if not player.alive:
                    continue
                for bullet_list in [p.bullets for p in self.players]:
                    for bullet in bullet_list:
                        if not bullet.alive or not bullet.is_player:
                            continue
                        if self.boss and self.boss.alive and not self.boss.entrance:
                            if circle_rect_collide(bullet.x, bullet.y, bullet.radius, self.boss.rect):
                                was_weak = self.boss.take_damage(bullet.damage, bullet.x, bullet.y)
                                self.difficulty.on_damage_dealt(bullet.damage)
                                spark_color = (255, 255, 0) if was_weak else bullet.color
                                self.particles.hit_spark(bullet.x, bullet.y, spark_color)
                                self.audio.play_hit()
                                if was_weak:
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
                                    player.add_score(2000)
                                    for _ in range(5):
                                        self.particles.explosion(
                                            self.boss.x + random.randint(-50, 50),
                                            self.boss.y + random.randint(-30, 30),
                                            'boss', COLORS['boss']
                                        )
                                    self.audio.play_explosion('boss')
                                    self.difficulty.wave_complete = True
                                    self.boss = None
                                break
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
                        enemy.health = 0
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
        elif self.state == GameState.PLAYING:
            self.handle_playing_input()
            time_scale = self.get_global_time_scale()
            scaled_dt = dt * time_scale
            self.starfield.update(scaled_dt)
            self.particles.update(scaled_dt)
            self.audio.update(dt)
            total_enemies = len([e for e in self.enemies if e.alive])
            intensity = min(1.0, total_enemies / 15 + (0.5 if self.boss and self.boss.alive else 0))
            self.audio.set_intensity(intensity)
            current_time = pygame.time.get_ticks()
            if not self.boss or not self.boss.alive:
                self.spawn_timer += dt
                if self.spawn_timer >= self.difficulty.current_spawn_rate:
                    self.spawn_timer = 0
                    if self.difficulty.enemies_in_wave > len([e for e in self.enemies if e.alive]):
                        self.spawn_enemy()
            for enemy in self.enemies:
                if enemy.alive:
                    new_bullets = enemy.update(scaled_dt, self.players, self.particles, current_time)
                    self.enemy_bullets.extend(new_bullets)
                if enemy.y > SCREEN_HEIGHT + 50 and enemy.alive:
                    enemy.alive = False
                    self.difficulty.on_enemy_escaped()
            self.enemies = [e for e in self.enemies if e.alive]
            if self.boss and self.boss.alive:
                boss_bullets = self.boss.update(scaled_dt, self.players, current_time, self.particles)
                self.enemy_bullets.extend(boss_bullets)
            for b in self.enemy_bullets:
                b.update(scaled_dt)
            self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]
            for p in self.players:
                for b in p.bullets:
                    b.update(scaled_dt, self.enemies, self.players, self.particles)
                p.bullets = [b for b in p.bullets if b.alive]
            self.check_collisions()
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
                self.start_new_wave()
        elif self.state == GameState.GAME_OVER:
            if self.input.is_key_pressed(pygame.K_RETURN) or self.input.is_key_pressed(pygame.K_ESCAPE):
                self.state = GameState.MENU

    def draw(self):
        self.screen.fill(COLORS['bg'])
        self.starfield.draw(self.screen)
        if self.state in (GameState.PLAYING, GameState.PAUSED, GameState.WAVE_NOTIFY,
                          GameState.BOSS_INTRO, GameState.GAME_OVER, GameState.ENTER_NAME):
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
            total_score = sum(p.score for p in self.players)
            max_combo = max((p.combo for p in self.players), default=0)
            max_mult = max((p.score_multiplier for p in self.players), default=1.0)
            self.ui.draw_score(self.screen, total_score, max_combo, max_mult, self.difficulty.wave)
            if self.boss and self.boss.alive:
                self.ui.draw_boss_health(self.screen, self.boss)
            for p in self.players:
                if p.alive and p.slowmo_active:
                    self.ui.draw_slowmo_indicator(self.screen, True, p.slowmo_timer, SLOWMO_DURATION)
                    break
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

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.update(dt)
            self.draw()
        pygame.quit()
