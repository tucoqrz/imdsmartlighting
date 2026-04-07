# IMD Smart Lighting Monitoring System (FIWARE)

Este projeto simula um sistema de monitoramento da iluminação externa do IMD de maneira inteligente utilizando a stack **FIWARE**. 
Ele provisiona automaticamente um serviço, 10 postes de luz (dispositivos IoT) e gera dados simulados para visualização histórica.

## Arquitetura
O projeto utiliza os seguintes componentes:
* **Orion Context Broker**: Gerenciamento de contexto em tempo real.
* **IoT Agent JSON**: Ponte de comunicação entre dispositivos e o Orion.
* **QuantumLeap**: Persistência de dados temporais no CrateDB.
* **CrateDB**: Banco de dados para séries temporais.
* **Grafana**: Dashboards para visualização de dados.
* **Python Populate**: Agente critou um script utilitário para automação e simulação de dados.


## Sobre o Script Python Populate
A gente criou um script para facilitar para automatizar a configuração inicial do ecossistema FIWARE e simular o envio de dados dos dispositivos. Nesse caso, são criados 10 "Postes" com os valores dos atributos gerados aleatoriamente. 

O que o Script faz:
* **Criação do Serviço**: Configura o imdlampservice no IoT Agent, definindo as chaves de segurança (API Key) e o tipo de entidade padrão (Lamp).
* **Registro da Subscription**: Cria automaticamente uma regra no Orion Context Broker para que toda vez que uma lâmpada atualizar seu estado, os dados sejam repassados para o QuantumLeap.
* **Criação dos dispositivos**: Registra 10 postes inteligentes (Lamp001 a Lamp010) com atributos de status, brilho, luminosidade ambiente e detecção de movimento.
* **Simulação de dados**: Gera e envia o primeiro conjunto de dados utilizando valores aleatórios inteiros, garantindo que o banco de dados (CrateDB) já inicie com informações para visualização. Quando os dados sofrem alteração, é possível ver o histórico dos dados e suas alterações no QuantumLeap.

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

### 3. Rodando o Script para simular dados (Opcional)
No terminal, dentro da pasta raiz do projeto, execute:
```bash
docker exec -it fiware-populate python populate.py
```