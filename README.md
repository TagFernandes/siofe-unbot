# SIOFE - Sistema de Extração de Ofertas

O **SIOFE** é um serviço especializado na extração e disponibilização de dados sobre as ofertas de disciplinas da faculdade. Ele atua como uma camada de backend que processa as informações acadêmicas e as expõe via API para consumo de outros serviços.

## 🚀 Funcionamento

O sistema realiza a raspagem/processamento das matérias e centraliza os dados no endpoint principal:

* **Endpoint:** `/oferta`
* **Método:** `GET`
* **Descrição:** Retorna o JSON contendo a lista atualizada das ofertas extraídas.

## ⚙️ Configuração de Ciclo (`time.json`)

A periodicidade da extração é controlada externamente pelo arquivo `time.json`. 
Este arquivo é fundamental para definir de quantos em quantos segundos o script de extração deve ser executado, permitindo o ajuste do intervalo de atualização sem a necessidade de reiniciar ou modificar o código-fonte da aplicação.

## 🛠 Como Rodar a Aplicação

Para garantir a estabilidade em ambiente de execução, o SIOFE utiliza o servidor WSGI **Gunicorn**. Instale as bibliotecas do requirements e tilize o comando abaixo para iniciar o serviço:

1. **Execute:**
   ```bash
   python3 app.py



## Arquitetura do Sistema SIOFE

O **SIOFE** (Sistema de Extração de Ofertas) é um microserviço robusto projetado para automação de coleta de dados acadêmicos, com foco em alta disponibilidade e observabilidade detalhada.

## 🏗️ Visão Geral da Arquitetura

A arquitetura é baseada em um modelo de processamento assíncrono onde a API serve dados pré-processados enquanto uma thread de background lida com a automação pesada.



### 1. Camada de API (Entrypoint)
O arquivo `app.py` utiliza **Flask** para expor os dados. 
- **Endpoint `/oferta`**: Realiza leitura de disco (Arquivos JSON na pasta `ofertas/`). Isso garante respostas em milissegundos, independente do site da faculdade estar lento ou fora do ar.
- **Middleware ProxyFix**: Configurado para que o sistema funcione corretamente atrás de um proxy reverso (como Nginx).

### 2. Motor de Automação e Parsing
A lógica de extração é dividida em dois núcleos:
- **Navegação (`lista_oferta.py`)**: Utiliza **Selenium WebDriver** em modo *headless*. Ele gerencia a autenticação de cookies, seleção de departamentos e níveis de ensino (Graduação).
- **Extração (`extract_oferta.py`)**: Utiliza **BeautifulSoup4** e **Regex** para limpar o HTML bruto. Ele isola nomes de professores (removendo cargas horárias) e padroniza os horários das turmas.

### 3. Observabilidade (Stack de Monitoramento)
O SIOFE integra as três colunas da observabilidade moderna:

* **Métricas (Prometheus)**: 
    - Exporta dados via `/metrics` usando `MultiProcessCollector`.
    - Monitora o timestamp da última geração do arquivo (`ULTIMA_GERACAO_OFERTA_TIMESTAMP`).
* **Logs (Grafana Loki)**: 
    - Logs estruturados enviados via `LokiLoggerHandler`.
    - Captura global de exceções não tratadas para garantir que nenhum erro crítico passe despercebido.
* **Trace (OpenTelemetry)**: 
    - Instrumentação automática do Flask.
    - Exportação via protocolo **GRPC** para o coletor (porta 4317).

## 🔄 Ciclo de Vida do Processamento

O sistema opera em um loop contínuo definido por:

1.  **Inicialização**: O Gunicorn inicia e executa o `when_ready` (configurando o `control.json`).
2.  **Thread de Background**: A thread `oferta` inicia, lê o `time.json` para saber o intervalo de descanso e começa a extração.
3.  **Persistência**: Os dados extraídos são validados e salvos em arquivos nomeados por semestre (ex: `oferta_2026_1.json`).
4.  **Consumo**: Quando um cliente (como o UnBot) solicita o dado, a API apenas lê o arquivo correspondente no sistema de arquivos.

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Função |
| :--- | :--- |
| **Flask** | Framework Web/API |
| **Gunicorn** | Servidor WSGI de Produção |
| **Selenium** | Automação de Navegação (Headless) |
| **BeautifulSoup4** | Extração de dados de HTML |
| **Prometheus Client** | Exposição de métricas de performance |
| **OpenTelemetry** | Rastreamento distribuído |
| **Loki Handler** | Centralização de logs |

---
