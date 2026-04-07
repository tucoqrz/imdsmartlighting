import requests
import random
import time

IOTA_SERVICES_URL = "http://iot-agent:4041/iot/services"
IOTA_DEVICES_URL = "http://iot-agent:4041/iot/devices"
UPDATE_BASE_URL = "http://iot-agent:7896/iot/json"
ORION_SUBS_URL = "http://orion:1026/v2/subscriptions"

SERVICE = "imdlampservice"
SERVICE_PATH = "/"
API_KEY = "imdlightingmonitoring2026"

def create_service():
    payload = {
        "services": [
            {
                "apikey": API_KEY,
                "cbroker": "http://orion:1026",
                "entity_type": "Lamp",
                "resource": "/iot/json"
            }
        ]
    }
    headers = {
        "fiware-service": SERVICE,
        "fiware-servicepath": SERVICE_PATH,
        "Content-Type": "application/json"
    }
    try:
        res = requests.post(IOTA_SERVICES_URL, json=payload, headers=headers)
        if res.status_code == 201:
            print(f"Serviço '{SERVICE}' criado com sucesso!")
        elif res.status_code == 409:
            print(f"Serviço '{SERVICE}' já existe.")
    except Exception as e:
        print(f"Erro ao configurar serviço: {e}")

def create_subscription():
    payload = {
        "description": "Notificar QuantumLeap sobre mudanças nas lâmpadas",
        "subject": {
            "entities": [{"idPattern": ".*", "type": "Lamp"}],
            "condition": {
                "attrs": ["status", "brightness", "ambient_light", "motion_detected"]
            }
        },
        "notification": {
            "http": {"url": "http://quantumleap:8668/v2/notify"},
            "attrs": ["status", "brightness", "ambient_light", "motion_detected"]
        }
    }
    headers = {
        "fiware-service": SERVICE,
        "fiware-servicepath": SERVICE_PATH,
        "Content-Type": "application/json"
    }
    try:
        res = requests.post(ORION_SUBS_URL, json=payload, headers=headers)
        if res.status_code == 201:
            print("Subscription no Orion criada com sucesso!")
        else:
            print(f"Verificação de Subscription: {res.status_code} (Pode já existir)")
    except Exception as e:
        print(f"Erro ao criar subscription: {e}")

def create_lamps(number_of_lamps):
    headers = {
        "fiware-service": SERVICE,
        "fiware-servicepath": SERVICE_PATH,
        "Content-Type": "application/json"
    }

    for i in range(1, number_of_lamps + 1):
        device_id = f"lamp{i:03d}" 
        entity_id = f"Lamp{i:03d}"
        
        device_payload = {
            "devices": [
                {
                    "device_id": device_id,
                    "entity_name": entity_id,
                    "entity_type": "Lamp",
                    "protocol": "PDI-IoTA-JSON",
                    "transport": "HTTP",
                    "attributes": [
                        { "object_id": "s", "name": "status", "type": "Text" },
                        { "object_id": "b", "name": "brightness", "type": "Number" },
                        { "object_id": "al", "name": "ambient_light", "type": "Number" },
                        { "object_id": "md", "name": "motion_detected", "type": "Boolean" }
                    ]
                }
            ]
        }

        requests.post(IOTA_DEVICES_URL, json=device_payload, headers=headers)
        print(f"{entity_id} provisionado.")

        s = random.choice(["ON", "OFF"])
        b = random.randint(0, 100)
        al = random.randint(100, 1000)   
        md = random.choice([True, False])

        update_url = f"{UPDATE_BASE_URL}?i={device_id}&k={API_KEY}"
        requests.post(update_url, json={"s": s, "b": b, "al": al, "md": md})
        print(f"Dados enviados para {entity_id}")

if __name__ == "__main__":
    create_service()
    time.sleep(1)
    create_subscription()
    time.sleep(1)
    create_lamps(10)
    print("Processo concluído! Os dados agora devem aparecer no QuantumLeap.")