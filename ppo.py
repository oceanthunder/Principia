import gymnasium
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecTransposeImage
from stable_baselines3.common.monitor import Monitor
from POP_env import POPEnv

def make_env():
    env = POPEnv()
    env = Monitor(env)
    return env

def train():
    env = DummyVecEnv([make_env])
    env = VecTransposeImage(env)

    model = PPO(
        policy="MultiInputPolicy",
        env=env,
        learning_rate=0.0001,
        device="cuda",
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        verbose=1,
        tensorboard_log="logs/"
    )

    print("Starting training...")
    try:
        model.learn(total_timesteps=1000000, progress_bar=True)
        
        model.save("models/ppo")
        print("Model saved!")
        
    except KeyboardInterrupt:
        print("Training interrupted. Saving current progress...")
        model.save("models/ppo_interrupted")

    finally:
        env.close()

if __name__ == "__main__":
    train()
