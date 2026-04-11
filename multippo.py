import gymnasium
import os
import sys
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, VecTransposeImage
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.utils import set_random_seed
from POP_env import POPEnv

def make_env(rank, mode, seed=0):
    def _init():
        # Mode Logic
        if mode == "1": # One window (only rank 0)
            if rank == 0:
                if "SDL_VIDEODRIVER" in os.environ: del os.environ["SDL_VIDEODRIVER"]
            else:
                os.environ["SDL_VIDEODRIVER"] = "dummy"
        
        elif mode == "2": # All windows
            if "SDL_VIDEODRIVER" in os.environ: del os.environ["SDL_VIDEODRIVER"]
            
        elif mode == "3": # Headless (no windows)
            os.environ["SDL_VIDEODRIVER"] = "dummy"

        env = POPEnv()
        env.reset(seed=seed + rank)
        env = Monitor(env)
        return env
    
    set_random_seed(seed)
    return _init

def train(mode):
    # Recommended for i5-9300H: 4 to 8. 12 is overkill for 8 threads.
    num_cpu = 6 
    
    print(f"Mode selected: {mode}")
    print(f"Starting training on {num_cpu} environments...")
    
    env = SubprocVecEnv([make_env(i, mode) for i in range(num_cpu)])
    env = VecTransposeImage(env)

    model = PPO(
        policy="MultiInputPolicy",
        env=env,
        learning_rate=2.5e-4,
        n_steps=4096,
        batch_size=1024,     
        n_epochs=10, # Reduced to 10 for better stability on mobile CPUs
        verbose=1,
        tensorboard_log="logs/",
        device="cuda"
    )

    try:
        model.learn(total_timesteps=8000000, progress_bar=True)
        model.save("models/ppo_final")
    except KeyboardInterrupt:
        print("\nTraining interrupted. Saving model...")
        model.save("models/ppo_interrupted")
    finally:
        env.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python multippo.py [1|2|3]")
        print("1: One window")
        print("2: All windows")
        print("3: Headless")
    else:
        user_mode = sys.argv[1]
        train(user_mode)

