import requests
import time
import random

UPDATE_URL = "http://iot-agent:7896/iot/json"
API_KEY = "imdlightingmonitoring2026"

NUM_LAMPS = 10

def simulate():
    print("Iniciando simulador...")

    while True:
        
        for i in range(1, NUM_LAMPS + 1):
            device_id = f"lamp{i:03d}"
            # 0-400 = noite | 401 - 800 = dia
            ambient_light = random.randint(0, 800) 
            motion = random.choice([True, False])
            payload = {
                "al": ambient_light,
                "md": motion
            }
            url = f"{UPDATE_URL}?i={device_id}&k={API_KEY}"
            try:
                requests.post(url, json=payload)
                print(f"{device_id} → ambient={ambient_light}, motion={motion}")
            except Exception as e:
                print("Erro:", e)

        print("---- aguardando próxima rodada ----\n")
        time.sleep(15)

if __name__ == "__main__":
    simulate()