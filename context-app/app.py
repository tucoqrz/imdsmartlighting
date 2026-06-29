from flask import Flask, request
import requests

app = Flask(__name__)

# NGSI-LD endpoints
ORION_URL = "[http://10.7.52.55:5000/notify](http://10.7.52.55:5000/notify)"
SERVICE = "imdlampservice"

# Contexto padrão para os modelos de dados
CONTEXT_URL = "https://raw.githubusercontent.com/smart-data-models/dataModel.Streetlighting/master/context.jsonld"

# Headers para atualizações NGSI-LD
HEADERS = {
    "NGSILD-Tenant": SERVICE,
    "Content-Type": "application/json",
    "Link": f'<{CONTEXT_URL}>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
}

GET_HEADERS = {
    "NGSILD-Tenant": SERVICE,
    "Accept": "application/json",
    "Link": f'<{CONTEXT_URL}>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
}

def property_value(entity, attr_name):
    return entity.get(attr_name, {}).get("value")

def fetch_entity_context(entity_id):
    try:
        res = requests.get(f"{ORION_URL}/{entity_id}", headers=GET_HEADERS)
        if res.status_code != 200:
            print(f"{entity_id} → falha ao buscar contexto completo | HTTP {res.status_code}")
            return {}
        return res.json()
    except Exception as e:
        print(f"Erro ao buscar contexto completo de {entity_id}: {e}")
        return {}

@app.route("/notify", methods=["POST"])
def notify():
    """
    Recebe notificações NGSI-LD do Orion-LD.
    O payload segue o formato normalizado:
    {
        "id": "urn:ngsi-ld:Notification:...",
        "type": "Notification",
        "subscriptionId": "urn:ngsi-ld:Subscription:...",
        "data": [
            {
                "id": "urn:ngsi-ld:Lamp:001",
                "type": "Lamp",
                "ambient_light": { "type": "Property", "value": 500 },
                "motion_detected": { "type": "Property", "value": true },
                "active": { "type": "Property", "value": true }
            }
        ]
    }
    """
    notification = request.json

    # No NGSI-LD, os dados vêm dentro de "data"
    entities = notification.get("data", [])

    for entity in entities:
        entity_id = entity["id"]

        # No formato normalizado NGSI-LD, atributos são objetos com "value"
        ambient = property_value(entity, "ambient_light")
        motion_detected = property_value(entity, "motion_detected")
        active = property_value(entity, "active")

        if ambient is None or motion_detected is None:
            full_entity = fetch_entity_context(entity_id)
            ambient = ambient if ambient is not None else property_value(full_entity, "ambient_light")
            motion_detected = (
                motion_detected
                if motion_detected is not None
                else property_value(full_entity, "motion_detected")
            )
            active = active if active is not None else property_value(full_entity, "active")

        # Pula entidades sem os dados necessários
        if ambient is None or motion_detected is None:
            print(f"{entity_id} → dados insuficientes, pulando...")
            continue

        # > 400 = Dia -> Poste desligado (Economia de energia)
        if ambient > 400:
            status = "OFF"
            brightness = 0
        elif motion_detected:
            # Noite com movimento -> potência máxima
            status = "ON"
            brightness = 100
        else:
            # Noite sem movimento -> iluminação reduzida
            status = "ON"
            brightness = 20

        # Payload de atualização no formato NGSI-LD normalizado
        update = {
            "status": {
                "type": "Property",
                "value": status
            },
            "brightness": {
                "type": "Property",
                "value": brightness
            },
            "ambient_light": {
                "type": "Property",
                "value": ambient
            },
            "motion_detected": {
                "type": "Property",
                "value": motion_detected
            },
            "active": {
                "type": "Property",
                "value": active if active is not None else True
            }
        }

        try:
            # PATCH /ngsi-ld/v1/entities/{entityId}/attrs
            res = requests.patch(
                f"{ORION_URL}/{entity_id}/attrs",
                json=update,
                headers=HEADERS
            )
            print(f"{entity_id} → {status} ({brightness}%) | HTTP {res.status_code}")
        except Exception as e:
            print(f"Erro ao atualizar {entity_id}: {e}")

    return "", 200

if __name__ == "__main__":
    print("Iniciando Context App (NGSI-LD)...")
    app.run(host="0.0.0.0", port=5000)
