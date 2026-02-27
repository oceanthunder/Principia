from gymnasium import Env, spaces
import numpy as np
from ctypes import CDLL, c_int, c_short
import os
from PIL import Image
import ctypes

class POPEnv(Env):

    def __init__(self):
        super(POPEnv, self).__init__()
        
        self.path = "./SDLPoP"
        os.chdir(self.path)
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        
        self.lib = CDLL("./src/libSDLPoP.so")
        
        self.rl_step_mode = c_int.in_dll(self.lib, "rl_step_mode")
        self.rl_action = c_int.in_dll(self.lib, "rl_action")
        self.start_level = c_int.in_dll(self.lib, "start_level")
        self.rl_kid_dead = c_int.in_dll(self.lib, "rl_kid_dead")
        self.current_level = c_short.in_dll(self.lib, "current_level")
        self.hitp_curr = c_short.in_dll(self.lib, "hitp_curr")
        self.hitp_max = c_short.in_dll(self.lib, "hitp_max")
        self.have_sword = c_int.in_dll(self.lib, "have_sword")
        self.curr_room = c_int.in_dll(self.lib, "curr_room")
        self.guardhp_curr = c_short.in_dll(self.lib, "guardhp_curr")
        self.guardhp_prev = 0
        self.frame_buffer = (ctypes.c_ubyte*(320*200*3))()
        self.lib.rl_get_frame.argtypes = [ctypes.POINTER(ctypes.c_ubyte *(320*200*3))]
        self.lib.rl_get_frame.restype = None
        self.rl_step_mode.value = 1
        self.start_level.value = 1
        self.lib.pop_main()

        #init shit
        self.init_game = self.lib.init_game
 
        # 0=NONE, 1=LEFT, 2=RIGHT, 3=UP, 4=DOWN, 5=SHIFT
        self.action_space = spaces.Discrete(6)
        
        self.observation_space = spaces.Dict({
            "pixels": spaces.Box(low=0, high=255, shape=(84, 84, 1), dtype=np.uint8),
            "state": spaces.Box(low=0, high=1, shape=(4,), dtype=np.float32)
        })
        
        self.total_reward = 0.0
        self.step_count = 0
        self.max_steps = 2000000
        self.prev_hp = None
    
    def _get_obs(self) -> dict:
        self.lib.rl_get_frame(ctypes.byref(self.frame_buffer))

        norm_hitp_curr = self.hitp_curr.value / self.hitp_max.value
        norm_hitp_max = self.hitp_max.value / 10.0
        norm_current_level = self.current_level.value / 15.0
        is_alive = 1.0 if self.rl_kid_dead.value == 0 else 0.0

        state = np.array([norm_hitp_curr, norm_hitp_max, norm_current_level, is_alive], dtype=np.float32)
        pixels = np.frombuffer(self.frame_buffer, dtype=np.uint8).reshape((200, 320, 3))
        img = Image.fromarray(pixels).convert('L').resize((84, 84), Image.BILINEAR)
        pixels = np.array(img, dtype=np.uint8)[:, :, np.newaxis]
        return {"pixels": pixels, "state": state}
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed, options=options)

        self.init_game(1)

        self.rl_kid_dead.value = 0
        self.episode_return = 0.0
        self.step_count = 0
        self.got_sword = 0
        self.prev_hp = self.hitp_curr.value
        self.guardhp_prev = self.guardhp_curr.value
        self.visited_rooms = set()
        start_room = self.curr_room.value
        self.visited_rooms.add(start_room)
        self.prev_room_id = start_room

        obs = self._get_obs()
        info = {"hp": self.hitp_curr.value}

        return obs, info

    
    def step(self, action: int):
        self.rl_action.value = action
        
        step_reward = 0.0
        num_skip = 4 #frameskips
        terminated = False

        for _ in range(num_skip):

            self.lib.play_level_2()
            self.step_count += 1
            current_hp = self.hitp_curr.value
            frame_reward = -0.01

            if self.prev_hp is not None and current_hp < self.prev_hp:
                frame_reward -= 1
            #potions
            if self.prev_hp is not None and current_hp > self.prev_hp:
                frame_reward += 1

            if self.rl_kid_dead.value == 1:
                frame_reward -= 10
                terminated = True

            if self.current_level.value > 1:
                frame_reward += 10
                terminated = True

            if self.have_sword.value > self.got_sword:
                frame_reward += 7
                self.got_sword = self.have_sword.value
                self.visited_rooms.clear()
                self.visited_rooms.add(self.curr_room.value)

            room_id = self.curr_room.value
            if room_id not in self.visited_rooms:
                frame_reward += 4 
                self.visited_rooms.add(room_id)

            guardhp_curr = self.guardhp_curr.value
            if room_id == self.prev_room_id:
                if guardhp_curr < self.guardhp_prev:
                    if guardhp_curr > 0:
                        frame_reward += 2.0
                    elif self.guardhp_prev > 0:
                        frame_reward += 3.0

            self.prev_room_id = room_id
            self.guardhp_prev = guardhp_curr
            self.prev_hp = current_hp
            step_reward += frame_reward

            if terminated:
                break
        
        self.total_reward += step_reward
        obs = self._get_obs()
        truncated = self.step_count >= self.max_steps
        
        info = {
            "hp": self.hitp_curr.value,
            "step": self.step_count,
            "total_reward": self.total_reward,
            "has_sword": self.got_sword
        }

        return obs, step_reward, terminated, truncated, info
    
    def close(self):
        self.rl_step_mode.value = 0

