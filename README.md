# IMD Smart Lighting Monitoring System (FIWARE NGSI-LD)

Este projeto simula um sistema de monitoramento da iluminação externa do IMD de maneira inteligente utilizando a stack **FIWARE** com o padrão **NGSI-LD**. 
Ele provisiona automaticamente um serviço, 10 postes de luz (dispositivos IoT) e gera dados simulados para visualização histórica.

## Arquitetura
O projeto utiliza os seguintes componentes:
* **Orion-LD Context Broker**: Gerenciamento de contexto em tempo real utilizando o padrão NGSI-LD.
* **IoT Agent JSON (modo NGSI-LD)**: Ponte de comunicação entre dispositivos e o Orion-LD, configurado com `IOTA_CB_NGSI_VERSION=ld`.
* **QuantumLeap**: Persistência de dados temporais no CrateDB.
* **CrateDB**: Banco de dados para séries temporais.
* **Grafana**: Dashboards para visualização de dados.
* **populate.py**: Script utilitário para automação e simulação de dados.
* **simulator.py**: Script responsável por simular continuamente dados dos sensores.
* **app.py**: Aplicação responsável pela lógica de decisão baseada em contexto.

## Sobre os Scripts:

**populate.py**:

Criamos um script para facilitar para automatizar a configuração inicial do ecossistema FIWARE e simular o envio de dados dos dispositivos. Nesse caso, são criados 10 "Postes" com os valores dos atributos gerados aleatoriamente. 

O que o Script faz:
* **Criação do Serviço**: Configura o imdlampservice no IoT Agent, definindo as chaves de segurança (API Key) e o tipo de entidade padrão (Lamp).
* **Registro das Subscriptions**: Cria automaticamente duas subscriptions no Orion-LD via endpoint NGSI-LD (`/ngsi-ld/v1/subscriptions`):
  - Uma para notificar o **QuantumLeap** (persistência de dados históricos).
  - Uma para notificar o **Context App** (motor de decisão inteligente).
* **Criação dos dispositivos**: Registra 10 postes inteligentes (Lamp001 a Lamp010) com atributos de status, brilho, luminosidade ambiente, detecção de movimento e atividade.
* **Simulação de dados**: Gera e envia o primeiro conjunto de dados utilizando valores aleatórios inteiros, garantindo que o banco de dados (CrateDB) já inicie com informações para visualização. Quando os dados sofrem alteração, é possível ver o histórico dos dados e suas alterações no QuantumLeap.

**simulator.py**:

O simulator.py é responsável por simular continuamente o comportamento dos sensores IoT, enviando dados em tempo real para o sistema.

O que o Script faz:
* **Geração contínua de dados**: Executa em loop infinito, simulando atualizações periódicas dos sensores.
* **Valores dinâmicos**:
  - ambient_light: valores aleatórios dentro de um intervalo (15s) (simulando variação de luminosidade ao longo do tempo).
  - motion_detected: valores booleanos aleatórios, simulando presença ou ausência de pessoas perto dos postes.
* **Filtro por atividade**:
  - Apenas dispositivos com active = true recebem atualizações.
  - A consulta ao Orion-LD usa a API NGSI-LD (`/ngsi-ld/v1/entities`) com header `NGSILD-Tenant`.
* **Envio para o IoT Agent**: Os dados são enviados via HTTP para o IoT Agent JSON, que os repassa ao Orion-LD.
* **Disparo do fluxo FIWARE**: Cada atualização gera eventos que:
  - atualizam o contexto no Orion-LD
  - disparam subscriptions NGSI-LD
  - alimentam o QuantumLeap
  - atualizam os dashboards no Grafana

## app.py (Decision Engine com Flask):

O app.py é uma aplicação desenvolvida com Flask que atua como um motor de decisão inteligente, responsável por automatizar o comportamento dos postes com base no contexto recebido.

O que a aplicação faz:

* **Recebimento de notificações NGSI-LD (endpoint /notify)**:
  - O Orion-LD envia notificações no formato normalizado NGSI-LD, contendo os dados das entidades dentro do campo `data`.
  - A aplicação recebe e processa os dados em tempo real.
* **Processamento de contexto**:
  - Analisa a luminosidade ambiente (ambient_light)
  - Verifica a presença de movimento (motion_detected)
* **Tomada de decisão automática**:
  - Se estiver claro (dia) → poste desligado
  - Se estiver escuro (noite):
  - com movimento → luz ligada (100%)
  - sem movimento → luz ligada com potência (20%)
* **Atualização do contexto no Orion-LD**:
  - A aplicação envia de volta os atributos calculados (status e brightness) via `PATCH /ngsi-ld/v1/entities/{entityId}/attrs`
  - O payload de atualização segue o formato normalizado NGSI-LD com `"type": "Property"`
  - Isso fecha o ciclo de controle do sistema
* **Integração com o ecossistema FIWARE**:
  - As atualizações geradas são persistidas no QuantumLeap
  - Os dashboards no Grafana são atualizados automaticamente

→ Essa aplicação representa a inteligência do sistema, transformando dados de sensores em ações automatizadas.

## Fluxo Completo do Sistema
* **1.** O simulator.py gera dados dos sensores.
* **2.** O IoT Agent envia para o Orion-LD (NGSI-LD).
* **3.** O Orion-LD notifica o app.py via subscription NGSI-LD.
* **4.** O app.py toma decisões (liga/desliga poste) e altera potência da luminosidade do poste.
* **5.** O Orion-LD atualiza os dados via PATCH NGSI-LD.
* **6.** O QuantumLeap armazena histórico.
* **7.** O Grafana exibe tudo em tempo real.

---

Link para documentação mais detalhada de alguns endpoints utilizados no Postman: https://documenter.getpostman.com/view/40491697/2sBXirhnik

## Como Executar

### 1. Pré-requisitos
* **Docker** e **Docker Compose** instalados.
* Navegador web para acessar o Grafana.

### 2. Subindo o Ambiente
No terminal, dentro da pasta raiz do projeto, execute:
```bash
docker-compose up 
```

### 3. Configuração inicial (populate)
No terminal, dentro da pasta raiz do projeto, execute:
```bash
docker exec -it fiware-populate python scripts/populate.py
```

### 4. Simulação contínua (simulator)
No terminal, dentro da pasta raiz do projeto, execute:
```bash
docker exec -it fiware-populate python scripts/simulator.py
```
→ Esse comando inicia a geração contínua de dados, permitindo visualizar o sistema em funcionamento em tempo real.

### 5. Acessar o Grafana

URL:

http://localhost:3000

Login inicial:

usuário: admin
senha: admin

Será solicitado alterar a senha no primeiro acesso.

Visualizar o Dashboard:

Dashboards → Browse → General → IMD Smart Lighting

Quando houver alterações nos atributos dos dispositivos, os dashboards são automaticamente atualizados.

## Diferenças da Versão NGSI-LD em relação à v2

| Aspecto | NGSI v2 | NGSI-LD |
|---|---|---|
| Orion | `fiware/orion` | `fiware/orion-ld:latest` |
| IoT Agent | Modo padrão (v2) | `IOTA_CB_NGSI_VERSION=ld` |
| Header de Tenant | `fiware-service` | `NGSILD-Tenant` |
| Endpoint de entidades | `/v2/entities` | `/ngsi-ld/v1/entities` |
| Endpoint de subscriptions | `/v2/subscriptions` | `/ngsi-ld/v1/subscriptions` |
| Formato de atributos | `{"value": x, "type": "Text"}` | `{"type": "Property", "value": x}` |
| Contexto semântico | Não utilizado | `@context` JSON-LD obrigatório |
| IDs de entidades | `Lamp001` | `urn:ngsi-ld:Lamp:001` (URN) |
