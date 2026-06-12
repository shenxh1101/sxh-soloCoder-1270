import random
from game.config import *


class DifficultyManager:
    def __init__(self):
        self.wave = 1
        self.enemies_killed = 0
        self.enemies_escaped = 0
        self.player_damage_taken = 0
        self.player_damage_dealt = 0
        self.current_spawn_rate = DIFFICULTY_BASE_SPAWN_RATE
        self.difficulty_score = 1.0
        self.wave_timer = 0
        self.enemies_in_wave = 0
        self.enemies_spawned_in_wave = 0
        self.wave_complete = False

    def start_new_wave(self):
        self.wave += 1
        self.enemies_in_wave = 5 + self.wave * 3
        self.enemies_spawned_in_wave = 0
        self.wave_complete = False
        self._recalculate_difficulty()

    def _recalculate_difficulty(self):
        performance = 1.0
        if self.enemies_killed > 0:
            kill_rate = self.enemies_killed / max(1, self.enemies_killed + self.enemies_escaped)
            performance *= 0.5 + kill_rate
        if self.player_damage_dealt > 0:
            efficiency = self.player_damage_dealt / max(1, self.player_damage_taken + 1)
            performance *= min(1.5, 0.8 + efficiency * 0.1)
        self.difficulty_score = 1.0 + (self.wave - 1) * 0.15
        self.difficulty_score *= performance
        self.difficulty_score = min(3.5, max(0.8, self.difficulty_score))
        self.current_spawn_rate = int(
            DIFFICULTY_BASE_SPAWN_RATE / self.difficulty_score
        )
        self.current_spawn_rate = max(DIFFICULTY_MIN_SPAWN_RATE, self.current_spawn_rate)

    def on_enemy_killed(self):
        self.enemies_killed += 1
        self.enemies_in_wave -= 1
        if self.enemies_in_wave <= 0:
            self.wave_complete = True

    def on_enemy_escaped(self):
        self.enemies_escaped += 1
        self.enemies_in_wave -= 1
        if self.enemies_in_wave <= 0:
            self.wave_complete = True

    def on_player_damage_taken(self, damage):
        self.player_damage_taken += damage

    def on_damage_dealt(self, damage):
        self.player_damage_dealt += damage

    def get_available_enemy_types(self):
        all_types = ['drone', 'kamikaze', 'fighter', 'bomber',
                     'shield_cruiser', 'stealth_recon', 'sniper', 'tank', 'mother_ship']
        if self.difficulty_score < 1.2:
            return all_types[:3]
        elif self.difficulty_score < 1.5:
            return all_types[:5]
        elif self.difficulty_score < 2.0:
            return all_types[:7]
        else:
            return all_types

    def pick_enemy_type(self):
        available = self.get_available_enemy_types()
        weights = {
            'drone': 30, 'kamikaze': 20, 'fighter': 20, 'bomber': 12,
            'shield_cruiser': 8, 'stealth_recon': 6, 'sniper': 8,
            'tank': 5, 'mother_ship': 3,
        }
        weighted = [(t, weights.get(t, 10)) for t in available]
        total = sum(w for _, w in weighted)
        r = random.randint(0, total)
        cumulative = 0
        for t, w in weighted:
            cumulative += w
            if r <= cumulative:
                return t
        return available[0]

    def should_spawn_boss(self):
        return self.wave > 0 and self.wave % WAVE_BOSS_INTERVAL == 0 and self.wave_complete

    def reset_wave(self):
        self.enemies_in_wave = 5 + self.wave * 3
        self.enemies_spawned_in_wave = 0
        self.wave_complete = False

    def update(self, dt):
        self.wave_timer += dt
