import requests
import random
import time

# URLs apontando para os serviços na VM do Grupo 1
url_servicos_iot = "http://10.7.52.55:4041/iot/services"
url_dispositivos_iot = "http://10.7.52.55:4041/iot/devices"
url_atualizacao_dados = "http://10.7.52.55:7896/iot/json"
url_inscricoes_orion = "http://10.7.52.55:1026/ngsi-ld/v1/subscriptions"

# IP da SUA VM (134) recebendo as notificações
url_sua_vm_context_app = "http://10.7.52.50:5000/notify"

NOME_DO_SERVICO = "imdlampservice"
CAMINHO_DO_SERVICO = "/"
CHAVE_DA_API = "imdlightingmonitoring2026"
URL_DO_CONTEXTO = "https://raw.githubusercontent.com/smart-data-models/dataModel.Streetlighting/master/context.jsonld"

def criar_servico_iot():
    dados_do_servico = {
        "services": [
            {
                "apikey": CHAVE_DA_API,
                "cbroker": "http://10.7.52.55:1026",
                "entity_type": "Lamp",
                "resource": "/iot/json"
            }
        ]
    }
    cabecalhos_servico = {
        "fiware-service": NOME_DO_SERVICO,
        "fiware-servicepath": CAMINHO_DO_SERVICO,
        "Content-Type": "application/json"
    }
    try:
        resposta = requests.post(url_servicos_iot, json=dados_do_servico, headers=cabecalhos_servico)
        if resposta.status_code == 201:
            print(f"Serviço '{NOME_DO_SERVICO}' criado com sucesso!")
        elif resposta.status_code == 409:
            print(f"Serviço '{NOME_DO_SERVICO}' já existe.")
        else:
            print(f"Resposta do serviço: {resposta.status_code} - {resposta.text}")
    except Exception as erro:
        print(f"Erro ao configurar serviço: {erro}")

def criar_inscricoes_no_orion():
    cabecalhos_inscricao = {
        "NGSILD-Tenant": NOME_DO_SERVICO,
        "Content-Type": "application/ld+json"
    }

    # 1. Inscrição do QuantumLeap (fica na VM do Grupo 1 mesmo)
    dados_inscricao_quantum = {
        "description": "Notificar QuantumLeap sobre mudanças nas lâmpadas",
        "type": "Subscription",
        "entities": [{"type": "Lamp"}],
        "watchedAttributes": ["status", "brightness", "ambient_light", "motion_detected", "active"],
        "notification": {
            "format": "normalized",
            "endpoint": {
                "uri": "http://10.7.52.55:8668/v2/notify",
                "accept": "application/json"
            }
        },
        "@context": URL_DO_CONTEXTO
    }
    try:
        resposta_quantum = requests.post(url_inscricoes_orion, json=dados_inscricao_quantum, headers=cabecalhos_inscricao)
        print(f"Subscription QuantumLeap: HTTP {resposta_quantum.status_code}")
    except Exception as erro:
        print(f"Erro ao criar subscription QuantumLeap: {erro}")

    # 2. Inscrição do Context App (apontando para a SUA VM)
    dados_inscricao_app = {
        "description": "Notificar motor de decisão sobre mudanças nas lâmpadas",
        "type": "Subscription",
        "entities": [{"type": "Lamp"}],
        "watchedAttributes": ["ambient_light", "motion_detected", "active"],
        "notification": {
            "format": "normalized",
            "endpoint": {
                "uri": url_sua_vm_context_app,
                "accept": "application/json"
            }
        },
        "@context": URL_DO_CONTEXTO
    }
    try:
        resposta_app = requests.post(url_inscricoes_orion, json=dados_inscricao_app, headers=cabecalhos_inscricao)
        print(f"Subscription Context App: HTTP {resposta_app.status_code}")
    except Exception as erro:
        print(f"Erro ao criar subscription Context App: {erro}")

def criar_postes_de_luz(quantidade_de_postes):
    cabecalhos_dispositivo = {
        "fiware-service": NOME_DO_SERVICO,
        "fiware-servicepath": CAMINHO_DO_SERVICO,
        "Content-Type": "application/json"
    }

    localizacao_dos_postes = {
        1:  [-35.20736, -5.83454],
        2:  [-35.20681, -5.83401],
        3:  [-35.20624, -5.83356],
        4:  [-35.20570, -5.83312],
        5:  [-35.20515, -5.83267]
    }

    for indice_da_linha in range(1, quantidade_de_postes + 1):
        identificador_do_dispositivo = f"lamp{indice_da_linha:03d}" 
        identificador_da_entidade = f"urn:ngsi-ld:Lamp:{indice_da_linha:03d}"
        coordenadas_atuais = localizacao_dos_postes.get(indice_da_linha, [-35.2050, -5.8340])
        
        configuracao_do_dispositivo = {
            "devices": [
                {
                    "device_id": identificador_do_dispositivo,
                    "entity_name": identificador_da_entidade,
                    "entity_type": "Lamp",
                    "apikey": CHAVE_DA_API,
                    "protocol": "PDI-IoTA-JSON",
                    "transport": "HTTP",
                    "attributes": [
                        { "object_id": "status", "name": "status", "type": "Property" },
                        { "object_id": "brightness", "name": "brightness", "type": "Property" },
                        { "object_id": "ambient_light", "name": "ambient_light", "type": "Property" },
                        { "object_id": "motion_detected", "name": "motion_detected", "type": "Property" },
                        { "object_id": "active", "name": "active", "type": "Property" }
                    ],
                    "static_attributes": [
                        {
                            "name": "location",
                            "type": "GeoProperty",
                            "value": {
                                "type": "Point",
                                "coordinates": coordenadas_atuais
                            }
                        }
                    ]
                }
            ]
        }

        try:
            requests.post(url_dispositivos_iot, json=configuracao_do_dispositivo, headers=cabecalhos_dispositivo)
            print(f"{identificador_da_entidade} provisionado.")
        except Exception as erro:
            print(f"Erro ao provisionar {identificador_da_entidade}: {erro}")
            continue

        # Envio inicial de estado para não ficar vazio
        luz_ambiente = random.randint(0, 800)
        movimento_detectado = random.choice([True, False])
        poste_ativo = True

        status_do_poste = "OFF" if luz_ambiente > 400 else "ON"
        brilho_do_poste = 0 if luz_ambiente > 400 else (100 if movimento_detectado else 20)

        url_para_envio = f"{url_atualizacao_dados}?i={identificador_do_dispositivo}&k={CHAVE_DA_API}"
        try:
            requests.post(url_para_envio, json={
                "status": status_do_poste, 
                "brightness": brilho_do_poste, 
                "ambient_light": luz_ambiente,
                "motion_detected": movimento_detectado,
                "active": poste_ativo
            })
        except Exception as erro:
            print(f"Erro ao enviar estado inicial de {identificador_da_entidade}: {erro}")

if __name__ == "__main__":
    criar_servico_iot()
    time.sleep(2)
    criar_inscricoes_no_orion()
    time.sleep(2)
    criar_postes_de_luz(10)
    print("Processo concluído! Configuração enviada para a VM 134 e 139.")