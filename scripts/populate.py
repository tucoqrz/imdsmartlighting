import requests
import random
import time

# Portas e URLs comuns para a stack NGSI-LD
IOTA_SERVICES_URL = "http://iot-agent:4041/iot/services"
IOTA_DEVICES_URL = "http://iot-agent:4041/iot/devices"
UPDATE_BASE_URL = "http://iot-agent:7896/iot/json"
ORION_SUBS_URL = "http://orion:1026/ngsi-ld/v1/subscriptions"

SERVICE = "imdlampservice"
SERVICE_PATH = "/"
API_KEY = "imdlightingmonitoring2026"

# Contexto padrão para os modelos de dados
CONTEXT_URL = "https://raw.githubusercontent.com/smart-data-models/dataModel.Streetlighting/master/context.jsonld"

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
        else:
            print(f"Resposta do serviço: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Erro ao configurar serviço: {e}")

def create_subscription():
    # Subscription para notificar o QuantumLeap (padrão NGSI-LD)
    payload = {
        "description": "Notificar QuantumLeap sobre mudanças nas lâmpadas",
        "type": "Subscription",
        "entities": [{"type": "Lamp"}],
        "watchedAttributes": ["status", "brightness", "ambient_light", "motion_detected", "active"],
        "notification": {
            "format": "normalized",
            "endpoint": {
                "uri": "http://quantumleap:8668/v2/notify",
                "accept": "application/json"
            }
        },
        "@context": CONTEXT_URL
    }
    headers = {
        "NGSILD-Tenant": SERVICE,
        "Content-Type": "application/ld+json"
    }
    try:
        res = requests.post(ORION_SUBS_URL, json=payload, headers=headers)
        if res.status_code == 201:
            print("Subscription para QuantumLeap criada com sucesso!")
        else:
            print(f"Verificação de Subscription QuantumLeap: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Erro ao criar subscription QuantumLeap: {e}")

    # Subscription para notificar o Context App (motor de decisão)
    payload_app = {
        "description": "Notificar motor de decisão sobre mudanças nas lâmpadas",
        "type": "Subscription",
        "entities": [{"type": "Lamp"}],
        "watchedAttributes": ["ambient_light", "motion_detected", "active"],
        "notification": {
            "format": "normalized",
            "endpoint": {
                "uri": "http://context-app:5000/notify",
                "accept": "application/json"
            }
        },
        "@context": CONTEXT_URL
    }
    try:
        res = requests.post(ORION_SUBS_URL, json=payload_app, headers=headers)
        if res.status_code == 201:
            print("Subscription para Context App criada com sucesso!")
        else:
            print(f"Verificação de Subscription Context App: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Erro ao criar subscription Context App: {e}")

def create_lamps(number_of_lamps):
    headers = {
        "fiware-service": SERVICE,
        "fiware-servicepath": SERVICE_PATH,
        "Content-Type": "application/json"
    }

    for i in range(1, number_of_lamps + 1):
        device_id = f"lamp{i:03d}" 
        # No NGSI-LD, IDs de entidades DEVEM ser URNs válidas
        entity_id = f"urn:ngsi-ld:Lamp:{i:03d}"
        
        device_payload = {
            "devices": [
                {
                    "device_id": device_id,
                    "entity_name": entity_id,
                    "entity_type": "Lamp",
                    "protocol": "PDI-IoTA-JSON",
                    "transport": "HTTP",
                    # Atributos: object_id = nome completo para que o Orion-LD
                    # receba os nomes corretos que as subscriptions observam
                    "attributes": [
                        { "object_id": "status", "name": "status", "type": "Property" },
                        { "object_id": "brightness", "name": "brightness", "type": "Property" },
                        { "object_id": "ambient_light", "name": "ambient_light", "type": "Property" },
                        { "object_id": "motion_detected", "name": "motion_detected", "type": "Property" },
                        { "object_id": "active", "name": "active", "type": "Property" }
                    ]
                }
            ]
        }

        try:
            res = requests.post(IOTA_DEVICES_URL, json=device_payload, headers=headers)
            if res.status_code == 201:
                print(f"{entity_id} provisionado.")
            elif res.status_code == 409:
                print(f"{entity_id} já existe.")
            else:
                print(f"{entity_id}: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"Erro ao provisionar {entity_id}: {e}")
            continue

        # Valores iniciais aleatórios
        status = random.choice(["ON", "OFF"])
        brightness = random.randint(0, 100)
        ambient_light = random.randint(0, 800)
        motion_detected = random.choice([True, False])
        active = True

        # O envio do dado pelo dispositivo (sul → norte) via JSON do IoT Agent
        update_url = f"{UPDATE_BASE_URL}?i={device_id}&k={API_KEY}"
        try:
            requests.post(update_url, json={
                "status": status, 
                "brightness": brightness, 
                "ambient_light": ambient_light,
                "motion_detected": motion_detected,
                "active": active
            })
            print(f"Dados enviados para {entity_id}")
        except Exception as e:
            print(f"Erro ao enviar dados para {entity_id}: {e}")

if __name__ == "__main__":
    create_service()
    time.sleep(2)
    create_subscription()
    time.sleep(2)
    create_lamps(10)
    print("Processo concluído! Os dados agora devem aparecer no QuantumLeap via NGSI-LD.")