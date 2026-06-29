from flask import Flask, request
import requests

app = Flask(__name__)

# Aponta para o Orion na VM do Grupo 1
endereco_orion_grupo1 = "http://10.7.52.55:1026/ngsi-ld/v1/entities"
NOME_DO_SERVICO = "imdlampservice"
URL_DO_CONTEXTO = "https://raw.githubusercontent.com/smart-data-models/dataModel.Streetlighting/master/context.jsonld"

cabecalhos_atualizacao = {
    "NGSILD-Tenant": NOME_DO_SERVICO,
    "Content-Type": "application/json",
    "Link": f'<{URL_DO_CONTEXTO}>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
}

cabecalhos_busca = {
    "NGSILD-Tenant": NOME_DO_SERVICO,
    "Accept": "application/json",
    "Link": f'<{URL_DO_CONTEXTO}>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
}

def obter_valor_propriedade(entidade, nome_do_atributo):
    return entidade.get(nome_do_atributo, {}).get("value")

def buscar_contexto_completo(identificador_da_entidade):
    try:
        resposta = requests.get(f"{endereco_orion_grupo1}/{identificador_da_entidade}", headers=cabecalhos_busca)
        if resposta.status_code != 200:
            print(f"{identificador_da_entidade} → falha ao buscar contexto completo | HTTP {resposta.status_code}")
            return {}
        return resposta.json()
    except Exception as erro_busca:
        print(f"Erro ao buscar contexto completo de {identificador_da_entidade}: {erro_busca}")
        return {}

@app.route("/notify", methods=["POST"])
def notify():
    notificacao_recebida = request.json
    lista_de_entidades = notificacao_recebida.get("data", [])

    for entidade_atual in lista_de_entidades:
        identificador_da_entidade = entidade_atual["id"]

        luz_ambiente = obter_valor_propriedade(entidade_atual, "ambient_light")
        movimento_detectado = obter_valor_propriedade(entidade_atual, "motion_detected")
        poste_ativo = obter_valor_propriedade(entidade_atual, "active")

        if luz_ambiente is None or movimento_detectado is None:
            entidade_completa = buscar_contexto_completo(identificador_da_entidade)
            luz_ambiente = luz_ambiente if luz_ambiente is not None else obter_valor_propriedade(entidade_completa, "ambient_light")
            movimento_detectado = (
                movimento_detectado
                if movimento_detectado is not None
                else obter_valor_propriedade(entidade_completa, "motion_detected")
            )
            poste_ativo = poste_ativo if poste_ativo is not None else obter_valor_propriedade(entidade_completa, "active")

        if luz_ambiente is None or movimento_detectado is None:
            print(f"{identificador_da_entidade} → dados insuficientes, pulando...")
            continue

        if luz_ambiente > 400:
            status_do_poste = "OFF"
            brilho_do_poste = 0
        elif movimento_detectado:
            status_do_poste = "ON"
            brilho_do_poste = 100
        else:
            status_do_poste = "ON"
            brilho_do_poste = 20

        dados_para_atualizar = {
            "status": {
                "type": "Property",
                "value": status_do_poste
            },
            "brightness": {
                "type": "Property",
                "value": brilho_do_poste
            },
            "ambient_light": {
                "type": "Property",
                "value": luz_ambiente
            },
            "motion_detected": {
                "type": "Property",
                "value": movimento_detectado
            },
            "active": {
                "type": "Property",
                "value": poste_ativo if poste_ativo is not None else True
            }
        }

        try:
            resposta_patch = requests.patch(
                f"{endereco_orion_grupo1}/{identificador_da_entidade}/attrs",
                json=dados_para_atualizar,
                headers=cabecalhos_atualizacao
            )
            print(f"{identificador_da_entidade} → {status_do_poste} ({brilho_do_poste}%) | HTTP {resposta_patch.status_code}")
        except Exception as erro_atualizacao:
            print(f"Erro ao atualizar {identificador_da_entidade}: {erro_atualizacao}")

    return "", 200

if __name__ == "__main__":
    print("Iniciando Context App (NGSI-LD) na porta 5000...")
    app.run(host="0.0.0.0", port=5000)