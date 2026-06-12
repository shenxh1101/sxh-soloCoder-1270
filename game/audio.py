import random
import math
import array
import pygame


class SoundManager:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        self.music_intensity = 0.0
        self.target_intensity = 0.0
        self.shoot_sounds = {}
        self.explosion_sounds = {}
        self.enabled = True
        self._generate_sounds()

    def _generate_tone(self, frequency, duration, volume=0.3, waveform='sine', decay=3.0):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = array.array('h')
        for i in range(n_samples):
            t = i / sample_rate
            env = max(0, 1.0 - t * decay)
            if waveform == 'sine':
                val = math.sin(2 * math.pi * frequency * t)
            elif waveform == 'square':
                val = 1.0 if math.sin(2 * math.pi * frequency * t) > 0 else -1.0
            elif waveform == 'sawtooth':
                val = 2 * (frequency * t - math.floor(frequency * t + 0.5))
            elif waveform == 'triangle':
                val = abs(4 * (frequency * t - math.floor(frequency * t + 0.25) + 0.25)) - 1.0
            else:
                val = math.sin(2 * math.pi * frequency * t)
            noise = (random.random() - 0.5) * 0.3
            sample = int((val * 0.7 + noise * 0.3) * env * volume * 32767)
            sample = max(-32768, min(32767, sample))
            buf.append(sample)
            buf.append(sample)
        return pygame.mixer.Sound(buffer=buf)

    def _generate_sounds(self):
        self.shoot_sounds['laser'] = []
        for i in range(8):
            freq = 800 + i * 100 + random.randint(-50, 50)
            self.shoot_sounds['laser'].append(
                self._generate_tone(freq, 0.08, 0.15, 'sawtooth', 8.0)
            )

        self.shoot_sounds['shotgun'] = []
        for i in range(6):
            self.shoot_sounds['shotgun'].append(
                self._generate_tone(150 + random.randint(-30, 30), 0.15, 0.25, 'square', 5.0)
            )

        self.shoot_sounds['missile'] = []
        for i in range(6):
            self.shoot_sounds['missile'].append(
                self._generate_tone(200 + random.randint(-40, 40), 0.2, 0.2, 'triangle', 4.0)
            )

        self.shoot_sounds['plasma'] = []
        for i in range(6):
            freq = 300 + i * 50 + random.randint(-20, 20)
            self.shoot_sounds['plasma'].append(
                self._generate_tone(freq, 0.3, 0.3, 'sine', 2.5)
            )

        self.explosion_sounds['small'] = []
        for i in range(6):
            self.explosion_sounds['small'].append(
                self._generate_tone(100 + random.randint(-20, 20), 0.2, 0.2, 'square', 6.0)
            )

        self.explosion_sounds['medium'] = []
        for i in range(6):
            self.explosion_sounds['medium'].append(
                self._generate_tone(70 + random.randint(-15, 15), 0.35, 0.3, 'square', 4.0)
            )

        self.explosion_sounds['large'] = []
        for i in range(5):
            self.explosion_sounds['large'].append(
                self._generate_tone(50 + random.randint(-10, 10), 0.5, 0.4, 'square', 2.5)
            )

        self.explosion_sounds['boss'] = []
        for i in range(4):
            self.explosion_sounds['boss'].append(
                self._generate_tone(35 + random.randint(-8, 8), 0.8, 0.5, 'square', 1.5)
            )

        self.hit_sound = self._generate_tone(600, 0.05, 0.1, 'sine', 15.0)
        self.upgrade_sound = self._generate_tone(880, 0.15, 0.25, 'sine', 4.0)
        self.warning_sound = self._generate_tone(220, 0.3, 0.3, 'square', 2.0)
        self.boss_intro = self._generate_tone(80, 1.0, 0.4, 'sawtooth', 1.0)
        self.dodge_sound = self._generate_tone(1200, 0.1, 0.2, 'sine', 8.0)

    def play_shoot(self, weapon_type):
        if not self.enabled:
            return
        sounds = self.shoot_sounds.get(weapon_type, [])
        if sounds:
            random.choice(sounds).play()

    def play_explosion(self, size='medium'):
        if not self.enabled:
            return
        sounds = self.explosion_sounds.get(size, self.explosion_sounds['medium'])
        if sounds:
            random.choice(sounds).play()

    def play_hit(self):
        if self.enabled:
            self.hit_sound.play()

    def play_upgrade(self):
        if self.enabled:
            self.upgrade_sound.play()

    def play_warning(self):
        if self.enabled:
            self.warning_sound.play()

    def play_boss_intro(self):
        if self.enabled:
            self.boss_intro.play()

    def play_dodge(self):
        if self.enabled:
            self.dodge_sound.play()

    def set_intensity(self, intensity):
        self.target_intensity = max(0.0, min(1.0, intensity))

    def update(self, dt):
        self.music_intensity += (self.target_intensity - self.music_intensity) * dt / 2000

    def toggle(self):
        self.enabled = not self.enabled
