import requests
import time
import random

# URLs apontando para a máquina do Grupo 1 (10.7.52.55) onde fica a recepção de dados
url_envio_dados = "http://10.7.52.55:7896/iot/json"
url_consulta_entidades = "http://10.7.52.55:1026/ngsi-ld/v1/entities"

CHAVE_DA_API = "imdlightingmonitoring2026"
URL_DO_CONTEXTO = "https://raw.githubusercontent.com/smart-data-models/dataModel.Streetlighting/master/context.jsonld"

def buscar_identificadores_das_lampadas():
    parametros_busca = {
        "type": "Lamp",
        "attrs": "active"
    }
    cabecalhos_busca = {
        "NGSILD-Tenant": "imdlampservice",
        "Accept": "application/json",
        "Link": f'<{URL_DO_CONTEXTO}>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
    }

    try:
        resposta = requests.get(url_consulta_entidades, params=parametros_busca, headers=cabecalhos_busca)
        dados_recebidos = resposta.json()
        return [
            entidade_atual["id"]
            for entidade_atual in dados_recebidos
            if entidade_atual.get("active", {}).get("value", True) is True
        ]
    except Exception as erro:
        print("Erro ao buscar lâmpadas ativas:", erro)
        return []
    
def iniciar_simulacao_continua():
    print("Iniciando simulador de sensores enviando dados para 10.7.52.55...")

    while True:
        lista_de_lampadas = buscar_identificadores_das_lampadas()

        if not lista_de_lampadas:
            print("Nenhuma lâmpada encontrada. Tentando novamente em 5 segundos...")
            time.sleep(5)
            continue

        for entidade_id in lista_de_lampadas:
            identificador_do_dispositivo = f"lamp{entidade_id.split(':')[-1]}"

            luz_ambiente = random.randint(0, 800)
            movimento_detectado = random.choice([True, False])
            poste_ativo = True
            
            carga_de_dados = {
                "ambient_light": luz_ambiente,
                "motion_detected": movimento_detectado,
                "active": poste_ativo
            }
            
            url_final = f"{url_envio_dados}?i={identificador_do_dispositivo}&k={CHAVE_DA_API}"
            try:
                requests.post(url_final, json=carga_de_dados)
                print(f"{identificador_do_dispositivo} → luz={luz_ambiente}, movimento={movimento_detectado}")
            except Exception as erro:
                print("Erro ao enviar dados do sensor:", erro)

        print("---- Aguardando 15 segundos para a próxima medição ----\n")
        time.sleep(15)

if __name__ == "__main__":
    iniciar_simulacao_continua()