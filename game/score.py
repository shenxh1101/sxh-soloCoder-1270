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
            return True
        except Exception:
            return False

    def get_next_frame(self):
        if not self.replaying or not self.replay_data:
            return None
        if self.current_frame >= len(self.replay_data['frames']):
            self.replaying = False
            return None
        frame = self.replay_data['frames'][self.current_frame]
        self.current_frame += 1
        return frame

    def stop_replay(self):
        self.replaying = False
        self.replay_data = None


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

    def record_encounter(self, enemy_type):
        if enemy_type not in self.data['enemies']:
            self.data['enemies'][enemy_type] = {'kills': 0, 'encountered': True}
        else:
            self.data['enemies'][enemy_type]['encountered'] = True

    def record_kill(self, enemy_type):
        self.record_encounter(enemy_type)
        self.data['enemies'][enemy_type]['kills'] = self.data['enemies'].get(enemy_type, {}).get('kills', 0) + 1
        self._save()

    def record_boss(self, boss_name):
        if boss_name not in self.data['bosses']:
            self.data['bosses'][boss_name] = {'kills': 0, 'encountered': True}
        else:
            self.data['bosses'][boss_name]['encountered'] = True

    def record_boss_kill(self, boss_name):
        self.record_boss(boss_name)
        self.data['bosses'][boss_name]['kills'] = self.data['bosses'].get(boss_name, {}).get('kills', 0) + 1
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
