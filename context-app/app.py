from flask import Flask, request
import requests
import time

app = Flask(__name__)

ORION_URL = "http://orion:1026/v2/entities"
HEADERS = {
    "fiware-service": "imdlampservice",
    "fiware-servicepath": "/",
    "Content-Type": "application/json"
}

def create_subscription():
    url = "http://orion:1026/v2/subscriptions"

    payload = {
        "description": "Notify decision engine",
        "subject": {
            "entities": [{"idPattern": ".*", "type": "Lamp"}],
            "condition": {
                "attrs": ["ambient_light", "motion_detected"]
            }
        },
        "notification": {
            "http": {
                "url": "http://context-app:5000/notify"
            }
        }
    }

    for i in range(15):
        try:
            res = requests.post(url, json=payload, headers=HEADERS)
            print("Subscription criada!", res.status_code)
            return
        except Exception as e:
            print(f"Tentativa {i+1}: erro → {e}")
            time.sleep(3)

    print("Falha ao conectar com Orion, mas app vai continuar rodando.")

@app.route("/notify", methods=["POST"])
def notify():
    data = request.json["data"]

    for entity in data:
        entity_id = entity["id"]
        ambient = entity["ambient_light"]["value"]
        motion = entity["motion_detected"]["value"]
        active = entity["active"]["value"]

        # > 400 = Dia -> Poste desligado (Economia de energia)
        if ambient > 400:
            status = "OFF"
            brightness = 0
        else:
            #se não, noite -> se houver alguém por perto, liga poste
            if motion:
                status = "ON"
                brightness = 100
            #se noite -> não há alguém por perto, poste ligado com luminosidade baixa (Economia de energia)
            else:
                status = "ON"
                brightness = 20

        update = {
            "status": {"value": status, "type": "Text"},
            "brightness": {"value": brightness, "type": "Number"},
            "active": {"value": active, "type": "Boolean"}
        }

        try:
            res = requests.patch(f"{ORION_URL}/{entity_id}/attrs", json=update, headers=HEADERS)
            print(f"{entity_id} → {status} ({brightness}) | {res.status_code}")
        except Exception as e:
            print(f"Erro ao atualizar {entity_id}: {e}")

    return "", 200

if __name__ == "__main__":
    print("Iniciando aplicação...")

    try:
        create_subscription()
    except Exception as e:
        print("Erro na subscription, continuando mesmo assim:", e)

    app.run(host="0.0.0.0", port=5000)