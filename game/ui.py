import math
import pygame
from game.config import *


class UIManager:
    def __init__(self):
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self._init_fonts()

    def _init_fonts(self):
        try:
            self.font_large = pygame.font.SysFont('consolas, monospace, arial, sans', 48, bold=True)
            self.font_medium = pygame.font.SysFont('consolas, monospace, arial, sans', 28, bold=True)
            self.font_small = pygame.font.SysFont('consolas, monospace, arial, sans', 18)
        except Exception:
            try:
                self.font_large = pygame.font.Font(None, 48)
                self.font_medium = pygame.font.Font(None, 28)
                self.font_small = pygame.font.Font(None, 18)
            except Exception:
                self.font_large = None
                self.font_medium = None
                self.font_small = None
        if self.font_large is None:
            self.font_large = pygame.font.Font(None, 48) if pygame.font.get_init() else None
        if self.font_medium is None:
            self.font_medium = pygame.font.Font(None, 28) if pygame.font.get_init() else None
        if self.font_small is None:
            self.font_small = pygame.font.Font(None, 18) if pygame.font.get_init() else None

    def draw_text(self, surface, text, x, y, color=None, font=None, center=False):
        if color is None:
            color = COLORS['ui']
        if font is None:
            font = self.font_small
        if font is None:
            return pygame.Rect(x, y, 0, 0)
        text_surf = font.render(text, True, color)
        rect = text_surf.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        surface.blit(text_surf, rect)
        return rect

    def draw_text_with_shadow(self, surface, text, x, y, color=None, shadow_color=(0, 0, 0),
                              font=None, center=False):
        if color is None:
            color = COLORS['ui']
        if font is None:
            font = self.font_small
        self.draw_text(surface, text, x + 2, y + 2, shadow_color, font, center)
        return self.draw_text(surface, text, x, y, color, font, center)

    def draw_player_hud(self, surface, player, x_offset=0, is_p2=False):
        if not player.alive:
            return
        color = COLORS['player'] if not is_p2 else COLORS['player2']
        y = 15
        if is_p2:
            x = SCREEN_WIDTH - 280
        else:
            x = 15
        self.draw_text(surface, f'P{player.id}', x, y, color, self.font_medium)
        hp_text = f'生命: {player.health}/{player.max_health}'
        self.draw_text(surface, hp_text, x, y + 30, color, self.font_small)
        bar_w = 180
        bar_h = 12
        pygame.draw.rect(surface, (50, 50, 50), (x, y + 50, bar_w, bar_h))
        hp_ratio = max(0, player.health / player.max_health)
        hp_color = (80, 255, 120) if hp_ratio > 0.5 else (255, 200, 0) if hp_ratio > 0.25 else (255, 80, 80)
        pygame.draw.rect(surface, hp_color, (x, y + 50, int(bar_w * hp_ratio), bar_h))
        pygame.draw.rect(surface, color, (x, y + 50, bar_w, bar_h), 2)
        self.draw_text(surface, f'命数: {"◆" * player.lives}', x, y + 68, color, self.font_small)
        weapon = player.current_weapon
        self.draw_text(surface, f'武器: {weapon.name} Lv.{weapon.level}',
                       x, y + 90, color, self.font_small)
        heat_ratio = weapon.heat / weapon.max_heat
        heat_color = (80, 255, 120)
        if heat_ratio > 0.7:
            heat_color = (255, 140, 0)
        if weapon.overheated:
            heat_color = (255, 50, 50)
        pygame.draw.rect(surface, (50, 50, 50), (x, y + 110, bar_w, 8))
        pygame.draw.rect(surface, heat_color, (x, y + 110, int(bar_w * heat_ratio), 8))
        pygame.draw.rect(surface, COLORS['heat'], (x, y + 110, bar_w, 8), 1)
        heat_label = '过热!' if weapon.overheated else '热量'
        self.draw_text(surface, heat_label, x + bar_w + 5, y + 108, heat_color, self.font_small)
        if weapon.type == 'plasma' and weapon.is_charging:
            charge_ratio = min(1.0, weapon.charge_time / 1000)
            pygame.draw.rect(surface, (50, 50, 50), (x, y + 125, bar_w, 6))
            pygame.draw.rect(surface, COLORS['plasma'],
                             (x, y + 125, int(bar_w * charge_ratio), 6))
            pygame.draw.rect(surface, (200, 100, 255), (x, y + 125, bar_w, 6), 1)

    def draw_score(self, surface, score, combo, multiplier, wave, center_x=None):
        if center_x is None:
            center_x = SCREEN_WIDTH // 2
        self.draw_text_with_shadow(surface, f'得分: {score}',
                                   center_x, 15, COLORS['ui'], font=self.font_medium, center=True)
        if combo > 1:
            pulse = 1.0 + 0.1 * math.sin(pygame.time.get_ticks() / 100)
            combo_color = (255, int(200 * pulse), 0)
            self.draw_text_with_shadow(surface, f'{combo} 连击! x{multiplier:.1f}',
                                       center_x, 50, combo_color, font=self.font_medium, center=True)
        self.draw_text_with_shadow(surface, f'第 {wave} 波',
                                   center_x, 85, (180, 180, 255), font=self.font_small, center=True)

    def draw_boss_health(self, surface, boss):
        if not boss or not boss.alive or boss.entrance:
            return
        bar_w = SCREEN_WIDTH - 100
        bar_h = 20
        x = 50
        y = SCREEN_HEIGHT - 45
        self.draw_text_with_shadow(surface, f'Boss: {boss.name}',
                                   x, y - 25, COLORS['boss'], font=self.font_small)
        pygame.draw.rect(surface, (50, 50, 50), (x, y, bar_w, bar_h))
        ratio = max(0, boss.health / boss.max_health)
        color = COLORS['boss']
        if boss.rage_mode:
            color = (255, 50, 50)
        pygame.draw.rect(surface, color, (x, y, int(bar_w * ratio), bar_h))
        pygame.draw.rect(surface, (255, 255, 255), (x, y, bar_w, bar_h), 2)
        phase_text = f'阶段 {boss.phase + 1}/{boss.max_phase + 1}'
        if boss.rage_mode:
            phase_text += ' - 狂暴!'
        self.draw_text(surface, phase_text, x + bar_w - 100, y - 25, color, self.font_small)
        if boss.weakpoint_active:
            self.draw_text_with_shadow(surface, '弱点暴露!',
                                       SCREEN_WIDTH // 2, y - 25, (255, 255, 0),
                                       font=self.font_medium, center=True)

    def draw_menu(self, surface, title, options, selected_idx, center_x=None, center_y=None):
        if center_x is None:
            center_x = SCREEN_WIDTH // 2
        if center_y is None:
            center_y = SCREEN_HEIGHT // 2
        title_y = center_y - 150
        self.draw_text_with_shadow(surface, title, center_x, title_y,
                                   (0, 220, 255), font=self.font_large, center=True)
        subtitle_y = title_y + 60
        self.draw_text(surface, '太空射击 - 复古街机版',
                       center_x, subtitle_y, (150, 150, 200), font=self.font_small, center=True)
        for i, opt in enumerate(options):
            y = center_y - 40 + i * 55
            color = (255, 255, 100) if i == selected_idx else COLORS['ui']
            prefix = '> ' if i == selected_idx else '  '
            self.draw_text_with_shadow(surface, prefix + opt,
                                       center_x, y, color, font=self.font_medium, center=True)

    def draw_highscores(self, surface, scores, x, y):
        self.draw_text_with_shadow(surface, '=== 高分榜 ===',
                                   x, y, (255, 220, 100), font=self.font_medium, center=True)
        for i, s in enumerate(scores[:8]):
            row_y = y + 40 + i * 28
            color = (255, 255, 255) if i == 0 else (220, 220, 220) if i < 3 else COLORS['ui']
            text = f'{i + 1:2d}. {s["name"]:<10} {s["score"]:>8d}  波{s["wave"]}'
            self.draw_text(surface, text, x, row_y, color, self.font_small, center=True)

    def draw_wave_notification(self, surface, wave, is_boss=False, boss_name=''):
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        if is_boss:
            self.draw_text_with_shadow(surface, '警告! Boss出现!',
                                       center_x, center_y - 40,
                                       (255, 50, 50), font=self.font_large, center=True)
            self.draw_text_with_shadow(surface, boss_name,
                                       center_x, center_y + 20,
                                       COLORS['boss'], font=self.font_medium, center=True)
        else:
            self.draw_text_with_shadow(surface, f'第 {wave} 波',
                                       center_x, center_y - 20,
                                       (0, 220, 255), font=self.font_large, center=True)

    def draw_game_over(self, surface, score, wave, is_high_score):
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        self.draw_text_with_shadow(surface, '游戏结束',
                                   center_x, center_y - 100,
                                   (255, 80, 80), font=self.font_large, center=True)
        self.draw_text(surface, f'最终得分: {score}',
                       center_x, center_y - 30,
                       COLORS['ui'], font=self.font_medium, center=True)
        self.draw_text(surface, f'到达波次: {wave}',
                       center_x, center_y + 10,
                       COLORS['ui'], font=self.font_medium, center=True)
        if is_high_score:
            self.draw_text_with_shadow(surface, '*** 新高分! ***',
                                       center_x, center_y + 60,
                                       (255, 220, 100), font=self.font_medium, center=True)

    def draw_pause(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))
        self.draw_text_with_shadow(surface, '暂停',
                                   SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                   (255, 255, 255), font=self.font_large, center=True)
        self.draw_text(surface, '按 ESC 继续',
                       SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50,
                       COLORS['ui'], self.font_small, center=True)

    def draw_controls(self, surface, x, y, is_p2=False):
        prefix = 'P1: ' if not is_p2 else 'P2: '
        if not is_p2:
            controls = ['WASD/方向键 移动', '空格 射击', '1-4 切换武器', 'X 蓄力(等离子炮)', 'Q/E 上下切武器']
        else:
            controls = ['IJKL 移动', '回车 射击']
        self.draw_text(surface, prefix + '控制', x, y, COLORS['ui'], self.font_small)
        for i, c in enumerate(controls):
            self.draw_text(surface, c, x, y + 20 + i * 18, (150, 150, 180), self.font_small)

    def draw_slowmo_indicator(self, surface, active, timer, max_time):
        if not active:
            return
        ratio = timer / max_time
        w = 100
        h = 6
        x = SCREEN_WIDTH // 2 - w // 2
        y = 120
        pygame.draw.rect(surface, (100, 200, 255), (x, y, int(w * ratio), h))
        pygame.draw.rect(surface, (255, 255, 255), (x, y, w, h), 1)
        self.draw_text(surface, '极限闪避!', SCREEN_WIDTH // 2, y - 18,
                       (100, 200, 255), self.font_small, center=True)
