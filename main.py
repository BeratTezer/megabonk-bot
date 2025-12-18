import time
import os
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from game_env import GameEnv
import sys
from train import start_training


def run_trained_model():
    """Eğitilmiş PPO modelini çalıştırır."""
    print("Eğitilmiş model yükleniyor...")
    model_path = "models/ppo_final_model.zip"
    if not os.path.exists(model_path):
        print(f"HATA: '{model_path}' bulunamadı. Lütfen önce Mod 2'yi çalıştırın.")
        return

    env = DummyVecEnv([lambda: GameEnv()])
    model = PPO.load(model_path, env=env)

    print("Eğitilmiş Ajan Başlatılıyor. Durdurmak için CTRL+C basın.")
    obs = env.reset()
    try:
        while True:
            action, _states = model.predict(obs, deterministic=True)
            obs, rewards, dones, info = env.step(action)

            if dones.any():
                print("Bölüm bitti, ortam sıfırlanıyor...")
                obs = env.reset()
    except KeyboardInterrupt:
        print("Ajan durduruldu.")
    env.close()


def main_menu():
    os.makedirs("models", exist_ok=True)

    while True:
        print("\n" + "=" * 30)
        print("Megabonk AJAN KONTROL")
        print("=" * 30)
        print("1. Modeli Eğit")
        print("2. Eğitilmiş Ajanı Çalıştır")
        print("3. Çıkış")
        print("=" * 30)

        choice = input("Seçiminiz (1-3): ")

        if choice == "1":
            print("Mod 1 (Eğitim) başlatılıyor... Eğitim uzun sürebilir.")
            try:
                start_training()
            except KeyboardInterrupt:
                print("\nEğitim durduruldu.")
            except Exception as e:
                print(f"Mod 1 hatası: {e}")

        elif choice == "2":
            print("Mod 2 (Çalıştırma) başlatılıyor...")
            run_trained_model()

        elif choice == "3":
            print("Çıkılıyor...")
            break
        else:
            print("Geçersiz seçim. Lütfen 1-3 arası bir sayı girin.")


if __name__ == "__main__":
    main_menu()
