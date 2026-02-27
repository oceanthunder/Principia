#!/usr/bin/env python3
"""
explore_ctypes.py - Learning ctypes with SDLPoP

This is an EXPLORATION script to understand how ctypes can control the game.
Run it step by step in a Python REPL or with breakpoints to learn!

Key Concepts:
1. CDLL loads a shared library (.so)
2. Structure mirrors C structs in Python
3. in_dll() accesses global C variables
4. You can call C functions directly

Author: Your exploration journey into C/Python interop!
"""

from ctypes import (
    CDLL, Structure, POINTER,
    c_byte, c_ubyte, c_short, c_ushort, c_int, c_uint,
    c_char, c_void_p, byref, cast, sizeof
)
import os

# =============================================================================
# STEP 1: Define C structures in Python
# =============================================================================
# These MUST match the C definitions exactly! (from types.h)

class CharType(Structure):
    """Mirrors char_type from types.h (16 bytes total)"""
    _fields_ = [
        ("frame", c_ubyte),      # byte frame
        ("x", c_ubyte),          # byte x
        ("y", c_ubyte),          # byte y
        ("direction", c_byte),   # sbyte direction (-1=left, 0=right)
        ("curr_col", c_byte),    # sbyte curr_col
        ("curr_row", c_byte),    # sbyte curr_row
        ("action", c_ubyte),     # byte action
        ("fall_x", c_byte),      # sbyte fall_x
        ("fall_y", c_byte),      # sbyte fall_y
        ("room", c_ubyte),       # byte room
        ("repeat", c_ubyte),     # byte repeat
        ("charid", c_ubyte),     # byte charid (0=kid, 1=shadow, 2=guard...)
        ("sword", c_ubyte),      # byte sword (0=sheathed, 2=drawn)
        ("alive", c_byte),       # sbyte alive (-1=alive, 0=dead)
        ("curr_seq", c_ushort),  # word curr_seq
    ]

    def __repr__(self):
        return (f"CharType(x={self.x}, y={self.y}, room={self.room}, "
                f"alive={self.alive}, action={self.action}, hp=?)")


# =============================================================================
# STEP 2: Load the library
# =============================================================================
print("=" * 60)
print("STEP 2: Loading libSDLPoP.so")
print("=" * 60)

# Change to the directory containing the .so
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    lib = CDLL("./libSDLPoP.so")
    print("✓ Library loaded successfully!")
    print(f"  Library object: {lib}")
except OSError as e:
    print(f"✗ Failed to load library: {e}")
    print("  Make sure libSDLPoP.so exists and is built as a shared library")
    exit(1)


# =============================================================================
# STEP 3: Access global variables
# =============================================================================
print("\n" + "=" * 60)
print("STEP 3: Accessing global variables via in_dll()")
print("=" * 60)

# Access global variables using in_dll()
# This tells Python: "find symbol 'Kid' in the library, treat it as CharType"

try:
    Kid = CharType.in_dll(lib, "Kid")
    Guard = CharType.in_dll(lib, "Guard")
    Char = CharType.in_dll(lib, "Char")
    
    # Simple integers
    hitp_curr = c_short.in_dll(lib, "hitp_curr")
    hitp_max = c_short.in_dll(lib, "hitp_max")
    current_level = c_short.in_dll(lib, "current_level")
    
    # Control inputs - these are what the RL agent will SET
    control_x = c_byte.in_dll(lib, "control_x")
    control_y = c_byte.in_dll(lib, "control_y")
    control_shift = c_byte.in_dll(lib, "control_shift")
    
    print("✓ Global variables accessed:")
    print(f"  Kid:           {Kid}")
    print(f"  hitp_curr:     {hitp_curr.value}")
    print(f"  hitp_max:      {hitp_max.value}")
    print(f"  current_level: {current_level.value}")
    print(f"  control_x:     {control_x.value}")
    print(f"  control_y:     {control_y.value}")
    print(f"  control_shift: {control_shift.value}")
    
except Exception as e:
    print(f"✗ Failed to access globals: {e}")
    print("  This is expected! The game hasn't been initialized yet.")
    print("  Values are garbage until SDL is initialized and game starts.")


# =============================================================================
# STEP 4: Define function prototypes
# =============================================================================
print("\n" + "=" * 60)
print("STEP 4: Setting up function prototypes")
print("=" * 60)

# Tell ctypes about function signatures
# Format: lib.function_name.argtypes = [arg1_type, arg2_type, ...]
#         lib.function_name.restype = return_type

# Initialization functions
lib.pop_main.argtypes = []
lib.pop_main.restype = None

lib.start_game.argtypes = []
lib.start_game.restype = None

lib.init_game.argtypes = [c_int]  # level number
lib.init_game.restype = None

# The key frame-step function!
lib.play_frame.argtypes = []
lib.play_frame.restype = None

# Drawing (needed for visual mode)
lib.draw_game_frame.argtypes = []
lib.draw_game_frame.restype = None

print("✓ Function prototypes defined:")
print("  - pop_main()       : Main entry point")
print("  - start_game()     : Initialize game state")
print("  - init_game(level) : Initialize specific level")
print("  - play_frame()     : Execute ONE game tick ← Key for RL!")
print("  - draw_game_frame(): Render the current frame")


# =============================================================================
# STEP 5: Demo - Reading values (will be garbage until game runs)
# =============================================================================
print("\n" + "=" * 60)
print("STEP 5: Current values (pre-initialization, expect garbage)")
print("=" * 60)

def print_game_state():
    """Print current game state from C globals"""
    print(f"  Level: {current_level.value}")
    print(f"  HP: {hitp_curr.value}/{hitp_max.value}")
    print(f"  Kid position: room={Kid.room}, x={Kid.x}, y={Kid.y}")
    print(f"  Kid state: alive={Kid.alive}, action={Kid.action}, frame={Kid.frame}")
    print(f"  Kid direction: {Kid.direction} (-1=left, 0=right)")
    print(f"  Controls: x={control_x.value}, y={control_y.value}, shift={control_shift.value}")

print_game_state()


# =============================================================================
# STEP 6: The RL Interface Pattern
# =============================================================================
print("\n" + "=" * 60)
print("STEP 6: RL Interface Pattern (pseudocode)")
print("=" * 60)

print("""
The RL training loop would look like:

    # B1: With SDL window (for debugging)
    # ----------------------------------
    # 1. Start game in a subprocess or thread
    # 2. From Python, set controls and call play_frame()
    
    def step(action):
        # Decode action to control inputs
        control_x.value = action_to_dx[action]      # -1, 0, or 1
        control_y.value = action_to_dy[action]      # -1, 0, or 1  
        control_shift.value = action_to_shift[action]  # 0 or 1
        
        # Execute one game frame
        lib.play_frame()
        
        # Optional: render (for B1 mode)
        lib.draw_game_frame()
        
        # Read observation
        obs = {
            'x': Kid.x,
            'y': Kid.y, 
            'room': Kid.room,
            'hp': hitp_curr.value,
            'alive': Kid.alive,
        }
        
        # Calculate reward
        done = Kid.alive >= 0  # 0 = dead, -1 = alive
        reward = compute_reward(obs)
        
        return obs, reward, done

    # B2: Headless (for training)
    # ---------------------------
    # Same as above but skip draw_game_frame()
    # May need to mock/disable SDL_Init for true headless
""")


# =============================================================================
# STEP 7: The Challenge
# =============================================================================
print("\n" + "=" * 60)
print("STEP 7: The Challenge - SDL Initialization")
print("=" * 60)

print("""
PROBLEM: Simply calling lib.pop_main() won't work directly because:
  1. pop_main() has an infinite game loop
  2. SDL needs to be initialized properly
  3. The game expects to control its own main thread

SOLUTIONS to explore:

A) Thread-based: Run game in a separate thread, control via ctypes
   - Tricky: SDL often requires main thread

B) Modify C code: Add a "step mode" flag
   - Add: extern int step_mode;
   - Modify play_level_2() to return after one frame in step mode
   - Python sets step_mode=1, calls the loop, it returns after 1 frame

C) Use your existing shared memory approach (seg003.c)
   - You already have semaphores set up!
   - Game waits on sem_action_ready
   - Python posts the semaphore with action, reads state

D) Hybrid: Initialize game normally, then switch to Python control
   - Call init functions to set up SDL
   - Replace main loop with Python loop calling play_frame()

Which approach interests you most for learning?
""")


# =============================================================================
# INTERACTIVE EXPLORATION
# =============================================================================
print("\n" + "=" * 60)
print("TRY THIS: Interactive exploration")
print("=" * 60)

print("""
In a Python REPL, try:

>>> from explore_ctypes import *
>>> sizeof(CharType)  # Should be 16
>>> Kid.x, Kid.y      # Garbage until game runs

To see all exported symbols:
$ nm -D libSDLPoP.so | less

To set control inputs (won't do anything until game runs):
>>> control_x.value = 1   # Move right
>>> control_x.value = -1  # Move left
>>> control_y.value = -1  # Jump/climb
>>> control_shift.value = 1  # Action/fight
""")

print(f"\nCharType size: {sizeof(CharType)} bytes (should be 16)")
