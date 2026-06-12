import pygame


class InputManager:
    def __init__(self):
        self.keys = {}
        self.key_pressed = {}
        self.joysticks = []
        self.joystick_buttons = {}
        self._init_joysticks()

    def _init_joysticks(self):
        pygame.joystick.init()
        count = pygame.joystick.get_count()
        for i in range(count):
            try:
                joy = pygame.joystick.Joystick(i)
                joy.init()
                self.joysticks.append(joy)
                self.joystick_buttons[i] = set()
            except Exception:
                pass

    def process_event(self, event):
        if event.type == pygame.KEYDOWN:
            self.keys[event.key] = True
            self.key_pressed[event.key] = True
        elif event.type == pygame.KEYUP:
            self.keys[event.key] = False
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.joy < len(self.joysticks):
                self.joystick_buttons[event.joy].add(event.button)
        elif event.type == pygame.JOYBUTTONUP:
            if event.joy < len(self.joysticks):
                self.joystick_buttons[event.joy].discard(event.button)

    def is_key_down(self, key):
        return self.keys.get(key, False)

    def is_key_pressed(self, key):
        result = self.key_pressed.get(key, False)
        return result

    def clear_pressed(self):
        self.key_pressed.clear()

    def get_joystick_count(self):
        return len(self.joysticks)

    def get_joystick_axis(self, joy_idx, axis_idx):
        if joy_idx < len(self.joysticks):
            try:
                return self.joysticks[joy_idx].get_axis(axis_idx)
            except Exception:
                return 0.0
        return 0.0

    def is_joystick_button_down(self, joy_idx, button):
        return button in self.joystick_buttons.get(joy_idx, set())

    def get_player_keys(self, player_id):
        keys = {}
        if player_id == 1:
            for k in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN,
                      pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s,
                      pygame.K_SPACE, pygame.K_z, pygame.K_x, pygame.K_LSHIFT]:
                keys[k] = self.keys.get(k, False)
        else:
            for k in [pygame.K_j, pygame.K_l, pygame.K_i, pygame.K_k, pygame.K_RETURN]:
                keys[k] = self.keys.get(k, False)
        if player_id <= len(self.joysticks):
            joy_idx = player_id - 1
            deadzone = 0.2
            axis_x = self.get_joystick_axis(joy_idx, 0)
            axis_y = self.get_joystick_axis(joy_idx, 1)
            if player_id == 1:
                if abs(axis_x) > deadzone:
                    if axis_x < 0:
                        keys[pygame.K_LEFT] = True
                    else:
                        keys[pygame.K_RIGHT] = True
                if abs(axis_y) > deadzone:
                    if axis_y < 0:
                        keys[pygame.K_UP] = True
                    else:
                        keys[pygame.K_DOWN] = True
                if self.is_joystick_button_down(joy_idx, 0):
                    keys[pygame.K_SPACE] = True
                if self.is_joystick_button_down(joy_idx, 1):
                    keys[pygame.K_x] = True
            else:
                if abs(axis_x) > deadzone:
                    if axis_x < 0:
                        keys[pygame.K_j] = True
                    else:
                        keys[pygame.K_l] = True
                if abs(axis_y) > deadzone:
                    if axis_y < 0:
                        keys[pygame.K_i] = True
                    else:
                        keys[pygame.K_k] = True
                if self.is_joystick_button_down(joy_idx, 0):
                    keys[pygame.K_RETURN] = True
        return keys
