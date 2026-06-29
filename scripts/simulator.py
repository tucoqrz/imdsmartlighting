import requests
import time
import random

# URLs apontando para a máquina do Grupo 1 (10.7.52.55)
url_envio_dados = "http://10.7.52.55:7896/iot/json"
url_consulta_entidades = "http://10.7.52.55:1026/ngsi-ld/v1/entities"

API_KEY = "imdlightingmonitoring2026"
CONTEXT_URL = "https://raw.githubusercontent.com/smart-data-models/dataModel.Streetlighting/master/context.jsonld"

def get_lamps():
    params = {
        "type": "Lamp",
        "attrs": "active"
    }

    headers = {
        "NGSILD-Tenant": "imdlampservice",
        "Accept": "application/json",
        "Link": f'<{CONTEXT_URL}>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
    }

    try:
        res = requests.get(url_consulta_entidades, params=params, headers=headers)
        data = res.json()
        return [
            entity["id"]
            for entity in data
            if entity.get("active", {}).get("value", True) is True
        ]
    except Exception as e:
        print("Erro ao buscar lâmpadas:", e)
        return []
    
def simulate():
    print("Iniciando simulador NGSI-LD apontando para o servidor 10.7.52.55...")

    while True:
        lamp_ids = get_lamps()

        if not lamp_ids:
            print("Nenhuma lâmpada encontrada. Tentando novamente...")
            time.sleep(5)
            continue

        for entity_id in lamp_ids:
            device_id = f"lamp{entity_id.split(':')[-1]}"

            ambient_light = random.randint(0, 800)
            motion_detected = random.choice([True, False])
            active = True
            
            payload = {
                "ambient_light": ambient_light,
                "motion_detected": motion_detected,
                "active": active
            }
            
            url = f"{url_envio_dados}?i={device_id}&k={API_KEY}"
            try:
                requests.post(url, json=payload)
                print(f"{device_id} → ambient={ambient_light}, motion={motion_detected}, active={active}")
            except Exception as e:
                print("Erro:", e)

        print("---- aguardando próxima rodada ----\n")
        time.sleep(15)

if __name__ == "__main__":
    simulate()