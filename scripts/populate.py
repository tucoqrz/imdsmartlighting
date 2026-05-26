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
        "watchedAttributes": ["status", "brightness", "ambient_light", "active"],
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
        "watchedAttributes": ["ambient_light", "active"],
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

    # Coordenadas fixas dos postes ao redor do IMD/UFRN (Natal-RN)
    # Formato GeoJSON: [longitude, latitude]
    lamp_locations = {
        1:  [-35.20736, -5.83454],
        2:  [-35.20681, -5.83401],
        3:  [-35.20624, -5.83356],
        4:  [-35.20570, -5.83312],
        5:  [-35.20515, -5.83267],
        6:  [-35.20460, -5.83489],
        7:  [-35.20405, -5.83535],
        8:  [-35.20550, -5.83580],
        9:  [-35.20615, -5.83522],
        10: [-35.20680, -5.83468],
    }

    for i in range(1, number_of_lamps + 1):
        device_id = f"lamp{i:03d}" 
        # No NGSI-LD, IDs de entidades DEVEM ser URNs válidas
        entity_id = f"urn:ngsi-ld:Lamp:{i:03d}"

        # Coordenadas do poste (usa posição padrão se não definida)
        coordinates = lamp_locations.get(i, [-35.2050, -5.8340])
        
        device_payload = {
            "devices": [
                {
                    "device_id": device_id,
                    "entity_name": entity_id,
                    "entity_type": "Lamp",
                    "apikey": API_KEY,
                    "protocol": "PDI-IoTA-JSON",
                    "transport": "HTTP",
                    # Atributos dinâmicos: mudam a cada envio de dados
                    "attributes": [
                        { "object_id": "status", "name": "status", "type": "Property" },
                        { "object_id": "brightness", "name": "brightness", "type": "Property" },
                        { "object_id": "ambient_light", "name": "ambient_light", "type": "Property" },
                        { "object_id": "active", "name": "active", "type": "Property" }
                    ],
                    # Atributos estáticos: definidos uma vez no provisionamento
                    "static_attributes": [
                        {
                            "name": "location",
                            "type": "GeoProperty",
                            "value": {
                                "type": "Point",
                                "coordinates": coordinates
                            }
                        }
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
        active = True

        # O envio do dado pelo dispositivo (sul → norte) via JSON do IoT Agent
        update_url = f"{UPDATE_BASE_URL}?i={device_id}&k={API_KEY}"
        try:
            requests.post(update_url, json={
                "status": status, 
                "brightness": brightness, 
                "ambient_light": ambient_light,
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