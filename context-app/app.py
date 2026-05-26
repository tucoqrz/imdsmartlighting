from flask import Flask, request
import requests

app = Flask(__name__)

# NGSI-LD endpoints
ORION_URL = "http://orion:1026/ngsi-ld/v1/entities"
SERVICE = "imdlampservice"

# Contexto padrão para os modelos de dados
CONTEXT_URL = "https://raw.githubusercontent.com/smart-data-models/dataModel.Streetlighting/master/context.jsonld"

# Headers para atualizações NGSI-LD
HEADERS = {
    "NGSILD-Tenant": SERVICE,
    "Content-Type": "application/json",
    "Link": f'<{CONTEXT_URL}>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
}

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
        ambient = entity.get("ambient_light", {}).get("value")
        active = entity.get("active", {}).get("value")

        # Pula entidades sem os dados necessários
        if ambient is None:
            print(f"{entity_id} → dados insuficientes, pulando...")
            continue

        # > 400 = Dia -> Poste desligado (Economia de energia)
        if ambient > 400:
            status = "OFF"
            brightness = 0
        else:
            # Noite -> poste ligado com luminosidade proporcional
            status = "ON"
            brightness = 100

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