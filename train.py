# train.py
import torch
import os
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback
from game_env import GameEnv


class RenderCallback(BaseCallback):
    def __init__(self, render_freq: int, verbose=0):
        super(RenderCallback, self).__init__(verbose)
        self.render_freq = render_freq

    def _on_step(self) -> bool:
        if self.n_calls % self.render_freq == 0:
            try:
                self.training_env.envs[0].render()
            except Exception as e:
                print(f"RenderCallback hatasi: {e}")
        return True


def start_training():
    print("Eğitim Modu Başlatılıyor... (VEKTOR tabanlı - MlpPolicy)")

    MODEL_PATH = "models/ppo_final_model.zip"

    env = DummyVecEnv([lambda: GameEnv()])

    if os.path.exists(MODEL_PATH):
        print(f"Varolan model şuradan yükleniyor: {MODEL_PATH}")
        model = PPO.load(
            MODEL_PATH, env=env, device="cuda" if torch.cuda.is_available() else "cpu"
        )
        model.tensorboard_log = "./ppo_tensorboard_logs/"
    else:
        print("Yeni model oluşturuluyor...")
        model = PPO(
            "MlpPolicy",
            env,
            verbose=1,
            tensorboard_log="./ppo_tensorboard_logs/",
            device="cuda" if torch.cuda.is_available() else "cpu",
        )
        # ---

    render_callback = RenderCallback(render_freq=5)

    print("Eğitim başlıyor...")
    print("Eğitimi durdurmak için CTRL+C tuşlarına basın.")

    try:
        model.learn(
            total_timesteps=1_000_000,
            callback=render_callback,
            reset_num_timesteps=False,
        )

    except KeyboardInterrupt:
        print("Eğitim durduruldu. İlerleme kaydediliyor...")

    model.save(MODEL_PATH)
    print(f"Eğitim tamamlandı. Model şuraya kaydedildi: {MODEL_PATH}")
    env.close()
