import json
import os
import time
from game.config import *


class HighScoreManager:
    def __init__(self):
        self.scores = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, 'r', encoding='utf-8') as f:
                    self.scores = json.load(f)
        except Exception:
            self.scores = []

    def _save(self):
        try:
            os.makedirs(os.path.dirname(HIGHSCORE_FILE), exist_ok=True)
            with open(HIGHSCORE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.scores, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_score(self, name, score, wave):
        entry = {
            'name': name,
            'score': score,
            'wave': wave,
            'date': time.strftime('%Y-%m-%d %H:%M')
        }
        self.scores.append(entry)
        self.scores.sort(key=lambda x: x['score'], reverse=True)
        self.scores = self.scores[:10]
        self._save()
        return self.scores.index(entry) + 1

    def get_top_scores(self, count=10):
        return self.scores[:count]

    def is_high_score(self, score):
        if len(self.scores) < 10:
            return True
        return score > self.scores[-1]['score']


class ReplayManager:
    def __init__(self):
        self.recording = False
        self.frames = []
        self.max_frames = 60 * 60 * 5
        self.current_frame = 0
        self.replaying = False
        self.replay_data = None
        self.paused = False
        self.play_speed = 1.0
        self.frame_accumulator = 0.0

    def start_recording(self):
        self.recording = True
        self.frames = []
        self.current_frame = 0

    def stop_recording(self):
        self.recording = False

    def record_frame(self, game_state):
        if not self.recording:
            return
        if len(self.frames) >= self.max_frames:
            self.frames = self.frames[-self.max_frames // 2:]
        self.frames.append(game_state.copy())

    def save_replay(self, name=None):
        if len(self.frames) < 60:
            return None
        if name is None:
            name = time.strftime('replay_%Y%m%d_%H%M%S')
        filename = os.path.join(REPLAY_DIR, f'{name}.json')
        try:
            os.makedirs(REPLAY_DIR, exist_ok=True)
            data = {
                'name': name,
                'date': time.strftime('%Y-%m-%d %H:%M'),
                'fps': 60,
                'frames': self.frames,
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            return filename
        except Exception:
            return None

    def list_replays(self):
        replays = []
        try:
            if os.path.exists(REPLAY_DIR):
                for f in sorted(os.listdir(REPLAY_DIR)):
                    if f.endswith('.json'):
                        replays.append(f[:-5])
        except Exception:
            pass
        return replays

    def load_replay(self, name):
        filename = os.path.join(REPLAY_DIR, f'{name}.json')
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.replay_data = data
            self.replaying = True
            self.current_frame = 0
            self.paused = False
            self.play_speed = 1.0
            self.frame_accumulator = 0.0
            return True
        except Exception:
            return False

    def get_total_frames(self):
        if self.replay_data and 'frames' in self.replay_data:
            return len(self.replay_data['frames'])
        return 0

    def get_current_idx(self):
        return self.current_frame

    def seek(self, frame_idx):
        if self.replay_data:
            n = len(self.replay_data.get('frames', []))
            self.current_frame = max(0, min(n - 1, int(frame_idx)))
            self.frame_accumulator = 0.0

    def seek_forward(self, delta_frames=60):
        self.seek(self.current_frame + delta_frames)

    def seek_backward(self, delta_frames=60):
        self.seek(self.current_frame - delta_frames)

    def toggle_pause(self):
        self.paused = not self.paused

    def set_speed(self, speed):
        self.play_speed = max(0.25, min(8.0, speed))

    def get_next_frame(self, dt=16.0):
        if not self.replaying or not self.replay_data:
            return None
        if self.paused:
            if self.current_frame < len(self.replay_data['frames']):
                return self.replay_data['frames'][self.current_frame]
            return None
        frames_list = self.replay_data.get('frames', [])
        if self.current_frame >= len(frames_list):
            self.replaying = False
            return None
        self.frame_accumulator += self.play_speed
        step_frames = int(self.frame_accumulator)
        self.frame_accumulator -= step_frames
        self.current_frame += max(1, step_frames)
        if self.current_frame >= len(frames_list):
            self.replaying = False
            return None
        return frames_list[self.current_frame]

    def get_keyframes(self):
        keyframes = []
        if not self.replay_data or 'frames' not in self.replay_data:
            return keyframes
        frames = self.replay_data['frames']
        n = len(frames)
        last_wave = None
        last_weapon = {}
        for i, f in enumerate(frames):
            marker = None
            w = f.get('wave', 0)
            if last_wave is None or w != last_wave:
                marker = {'type': 'wave', 'label': f'第{w}波'}
                last_wave = w
            elif f.get('boss') is not None and i > 0:
                prev = frames[i-1] if i > 0 else {}
                if prev.get('boss') is None:
                    marker = {'type': 'boss_intro', 'label': 'Boss出现'}
            elif f.get('boss') is None and i > 0:
                prev = frames[i-1] if i > 0 else {}
                if prev.get('boss') is not None:
                    marker = {'type': 'boss_dead', 'label': 'Boss倒下'}
            else:
                for ev in f.get('events', []):
                    if ev.get('type') == 'weapon_switch':
                        pid = ev.get('player_id', 1)
                        cur_w = ev.get('weapon', '')
                        if last_weapon.get(pid) != cur_w:
                            marker = {'type': 'weapon', 'label': f'切{cur_w}'}
                            last_weapon[pid] = cur_w
                            break
            if marker and i < n - 1:
                keyframes.append({'frame': i, **marker})
        return keyframes

    def stop_replay(self):
        self.replaying = False
        self.replay_data = None
        self.paused = False
        self.play_speed = 1.0


class BestiaryManager:
    def __init__(self):
        self.data = {'enemies': {}, 'bosses': {}}
        self._load()

    def _load(self):
        try:
            if os.path.exists(BESTIARY_FILE):
                with open(BESTIARY_FILE, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
        except Exception:
            self.data = {'enemies': {}, 'bosses': {}}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(BESTIARY_FILE), exist_ok=True)
            with open(BESTIARY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def record_encounter(self, enemy_type, wave=1):
        changed = False
        if enemy_type not in self.data['enemies']:
            self.data['enemies'][enemy_type] = {
                'kills': 0, 'encountered': True,
                'first_wave': wave, 'best_kill_wave': 0,
                'hit_count': 0
            }
            changed = True
        elif not self.data['enemies'][enemy_type].get('encountered', False):
            self.data['enemies'][enemy_type]['encountered'] = True
            self.data['enemies'][enemy_type]['first_wave'] = wave
            changed = True
        if changed:
            self._save()

    def record_kill(self, enemy_type, wave=1):
        self.record_encounter(enemy_type, wave)
        if enemy_type in self.data['enemies']:
            self.data['enemies'][enemy_type]['kills'] = self.data['enemies'][enemy_type].get('kills', 0) + 1
            old_best = self.data['enemies'][enemy_type].get('best_kill_wave', 0)
            if wave > old_best:
                self.data['enemies'][enemy_type]['best_kill_wave'] = wave
        else:
            self.data['enemies'][enemy_type] = {
                'kills': 1, 'encountered': True,
                'first_wave': wave, 'best_kill_wave': wave,
                'hit_count': 0
            }
        self._save()

    def record_hit_by(self, enemy_type):
        if enemy_type in self.data['enemies']:
            self.data['enemies'][enemy_type]['hit_count'] = self.data['enemies'][enemy_type].get('hit_count', 0) + 1
            self._save()

    def record_boss(self, boss_name, wave=1):
        changed = False
        if boss_name not in self.data['bosses']:
            self.data['bosses'][boss_name] = {
                'kills': 0, 'encountered': True,
                'first_wave': wave, 'best_kill_wave': 0,
                'hit_count': 0
            }
            changed = True
        elif not self.data['bosses'][boss_name].get('encountered', False):
            self.data['bosses'][boss_name]['encountered'] = True
            self.data['bosses'][boss_name]['first_wave'] = wave
            changed = True
        if changed:
            self._save()

    def record_boss_kill(self, boss_name, wave=1):
        self.record_boss(boss_name, wave)
        if boss_name in self.data['bosses']:
            self.data['bosses'][boss_name]['kills'] = self.data['bosses'][boss_name].get('kills', 0) + 1
            old_best = self.data['bosses'][boss_name].get('best_kill_wave', 0)
            if wave > old_best:
                self.data['bosses'][boss_name]['best_kill_wave'] = wave
        else:
            self.data['bosses'][boss_name] = {
                'kills': 1, 'encountered': True,
                'first_wave': wave, 'best_kill_wave': wave,
                'hit_count': 0
            }
        self._save()

    def record_hit_by_boss(self, boss_name):
        if boss_name in self.data['bosses']:
            self.data['bosses'][boss_name]['hit_count'] = self.data['bosses'][boss_name].get('hit_count', 0) + 1
            self._save()

    def get_enemy_data(self):
        return self.data['enemies']

    def get_boss_data(self):
        return self.data['bosses']

    def is_encountered(self, key, is_boss=False):
        if is_boss:
            return key in self.data['bosses'] and self.data['bosses'][key].get('encountered', False)
        else:
            return key in self.data['enemies'] and self.data['enemies'][key].get('encountered', False)


class ShipConfigManager:
    PRESET_CONFIGS = {
        '重型火力流': {
            'color_idx': 1, 'shape_idx': 1, 'weapon_idx': 0, 'upgrade_idx': 1,
            'desc': '生命+30%，伤害+10%，开局武器升+伤害强化'
        },
        '轻型机动流': {
            'color_idx': 2, 'shape_idx': 2, 'weapon_idx': 1, 'upgrade_idx': 2,
            'desc': '速度+25%，散热强化，霰弹开局快速清屏'
        },
        '均衡标准流': {
            'color_idx': 0, 'shape_idx': 0, 'weapon_idx': 0, 'upgrade_idx': 0,
            'desc': '均衡属性，激光+1级，适合新手'
        },
        '导弹狙击流': {
            'color_idx': 5, 'shape_idx': 3, 'weapon_idx': 2, 'upgrade_idx': 1,
            'desc': '三角战机+追踪导弹，精准打击流'
        },
        '等离子破坏流': {
            'color_idx': 4, 'shape_idx': 1, 'weapon_idx': 3, 'upgrade_idx': 3,
            'desc': '重型+等离子炮，蓄力爆发流，护盾+伤害'
        },
    }

    def __init__(self):
        self.configs = {}
        self.selected = None
        self._load()

    def _load(self):
        try:
            if os.path.exists(SHIP_CONFIGS_FILE):
                with open(SHIP_CONFIGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.configs = data.get('configs', {})
                self.selected = data.get('selected')
            else:
                self.configs = dict(self.PRESET_CONFIGS)
                self.selected = '均衡标准流'
                self._save()
        except Exception:
            self.configs = dict(self.PRESET_CONFIGS)
            self.selected = '均衡标准流'

    def _save(self):
        try:
            os.makedirs(os.path.dirname(SHIP_CONFIGS_FILE), exist_ok=True)
            with open(SHIP_CONFIGS_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'configs': self.configs,
                    'selected': self.selected,
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def list_configs(self):
        return sorted(self.configs.keys())

    def get_config(self, name):
        return self.configs.get(name)

    def get_selected_config(self):
        if self.selected and self.selected in self.configs:
            return self.configs[self.selected]
        return self.configs.get('均衡标准流', {})

    def select_config(self, name):
        if name in self.configs:
            self.selected = name
            self._save()
            return True
        return False

    def save_current_as(self, name, color_idx, shape_idx, weapon_idx, upgrade_idx):
        self.configs[name] = {
            'color_idx': color_idx,
            'shape_idx': shape_idx,
            'weapon_idx': weapon_idx,
            'upgrade_idx': upgrade_idx,
            'desc': f'自定义配置 [{name}]'
        }
        self.selected = name
        self._save()

    def delete_config(self, name):
        if name in self.configs and name not in self.PRESET_CONFIGS:
            del self.configs[name]
            if self.selected == name:
                self.selected = '均衡标准流'
            self._save()
            return True
        return False
