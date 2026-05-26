import requests
import time
import random

UPDATE_URL = "http://iot-agent:7896/iot/json"
API_KEY = "imdlightingmonitoring2026"

# NGSI-LD endpoint para consultar entidades
ENTITIES_URL = "http://orion:1026/ngsi-ld/v1/entities"

# Contexto padrão para os modelos de dados
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
        res = requests.get(ENTITIES_URL, params=params, headers=headers)
        data = res.json()
        # No NGSI-LD normalizado, atributos são objetos com "value"
        # Filtra apenas lâmpadas ativas
        return [
            entity["id"]
            for entity in data
            if entity.get("active", {}).get("value", True) is True
        ]
    except Exception as e:
        print("Erro ao buscar lâmpadas:", e)
        return []
    
def simulate():
    print("Iniciando simulador NGSI-LD...")

    while True:
        lamp_ids = get_lamps()

        if not lamp_ids:
            print("Nenhuma lâmpada encontrada (Orion pode estar reiniciando). Tentando novamente...")
            time.sleep(5)
            continue

        for entity_id in lamp_ids:
            # Extrai o device_id a partir do entity_id (urn:ngsi-ld:Lamp:lamp001 → lamp001)
            device_id = entity_id.split(":")[-1]

            # 0-400 = noite | 401 - 800 = dia
            ambient_light = random.randint(0, 800) 
            active = True
            payload = {
                "ambient_light": ambient_light,
                "active": active
            }
            url = f"{UPDATE_URL}?i={device_id}&k={API_KEY}"
            try:
                requests.post(url, json=payload)
                print(f"{device_id} → ambient={ambient_light}, active={active}")
            except Exception as e:
                print("Erro:", e)

        print("---- aguardando próxima rodada ----\n")
        time.sleep(15)

if __name__ == "__main__":
    simulate()