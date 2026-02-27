import gymnasium
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv, VecTransposeImage
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.utils import set_random_seed
from POP_env import POPEnv

def make_env(rank, seed=0):
    def _init():
        env = POPEnv()
        env.reset(seed=seed + rank)
        env = Monitor(env)
        return env
    set_random_seed(seed)
    return _init

def train():
    num_cpu = 12
    env = SubprocVecEnv([make_env(i) for i in range(num_cpu)])
    env = VecTransposeImage(env)

    model = PPO(
        policy="MultiInputPolicy",
        env=env,
        learning_rate=2.5e-4,
        n_steps=2048,
        batch_size=512,     
        n_epochs=10,
        gamma=0.99,       
        gae_lambda=0.95,
        ent_coef=0.01,    
        verbose=1,
        target_kl=0.015, 
        tensorboard_log="logs/",
        device="cuda"
    )

    print(f"Starting training on {num_cpu} environments...")
    try:
        model.learn(total_timesteps=8000000, progress_bar=True)
        model.save("models/ppo_final")
    except KeyboardInterrupt:
        model.save("models/ppo_interrupted")
    finally:
        env.close()

if __name__ == "__main__":
    train()
