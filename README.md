# 🔍 DetectaIA - Plataforma de IA para Detecção de Fraude em Duplicatas Escriturais

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Visão Geral

**DetectaIA** é uma plataforma completa de IA/ML para detecção inteligente de fraude em duplicatas escriturais, desenvolvida especificamente para áreas de risco, compliance e crédito. Combina regras de negócio avançadas com algoritmos de Machine Learning para identificar automaticamente duplicatas suspeitas, oferecendo explicabilidade total das decisões e configuração flexível do apetite de risco.

### 🏆 Diferenciais Competitivos

- ✅ **Explicabilidade Total**: Cada flag de fraude vem com motivos claros e compreensíveis
- ✅ **Multi-tenant Seguro**: Isolamento completo de dados entre clientes
- ✅ **APIs Enterprise**: RESTful, documentadas e prontas para integração B2B
- ✅ **Apetite de Risco Configurável**: Ajuste dinâmico da sensibilidade de detecção
- ✅ **Interface Intuitiva**: Dashboard visual para analistas não-especialistas em IA
- ✅ **Escalabilidade**: Arquitetura preparada para alto volume de transações
- ✅ **Auditoria Completa**: Logs detalhados de todas as operações
- ✅ **Deploy Flexível**: Suporte a containers, cloud e on-premise

## 🚀 Demo Rápido

```bash
# Clone o repositório
git clone https://github.com/TozatoRodrigo/detecta_ia.git
cd detecta_ia

# Instale as dependências
pip install -r backend/requirements.txt

# Inicie a aplicação
python3 backend/main.py &
python3 -m streamlit run dashboard.py

# Acesse o dashboard
open http://localhost:8501
```

## Funcionalidades Principais

### 🔐 Autenticação Multi-tenant
- Gestão de clientes (fintechs, bancos, parceiros)
- Segregação completa de dados por cliente
- Autenticação JWT/OAuth

### 📊 Dashboard Interativo
- KPIs gerais (total duplicatas, % sem NF, suspeitas)
- Gráficos dinâmicos de tendências e distribuições
- Tabela detalhada com filtros e busca avançada
- Destaque visual para títulos suspeitos

### 🤖 Detecção de Fraude IA/ML
- **Regras simples**: Flag automático para duplicatas sem documento fiscal
- **Modelo avançado**: Isolation Forest para detecção de anomalias
- **Explicabilidade**: Motivos claros para cada flag
- **Apetite de risco**: Threshold ajustável por cliente

### 🔌 APIs RESTful
- Upload automatizado de lotes
- Consulta de flags e suspeitas
- Download de relatórios
- Documentação Swagger/OpenAPI

### 📈 Simulação e Relatórios
- Teste de cenários em tempo real
- Exportação CSV/XLSX
- Impacto de mudanças no apetite de risco

## 🛠️ Stack Tecnológico

- **Backend**: Python 3.11+ (FastAPI, pandas, scikit-learn)
- **Frontend**: Streamlit (Dashboard interativo)
- **Machine Learning**: Isolation Forest, Local Outlier Factor, Feature Engineering Avançado
- **APIs**: RESTful com documentação OpenAPI/Swagger
- **Banco de Dados**: PostgreSQL (produção), SQLite (desenvolvimento)
- **Cache**: Redis para sessões e performance
- **Containerização**: Docker + Docker Compose
- **Monitoramento**: Logs estruturados, Health Checks, Métricas
- **Segurança**: JWT Authentication, Rate Limiting, Auditoria

## 📁 Estrutura do Projeto

```
fraud-detection-platform/
├── backend/                    # API Backend
│   ├── app/
│   │   ├── audit.py           # Sistema de auditoria
│   │   ├── config.py          # Configurações avançadas
│   │   ├── database.py        # Modelos e ORM
│   │   ├── ml_service.py      # Serviços de ML
│   │   └── models.py          # Modelos Pydantic
│   ├── main.py                # FastAPI app principal
│   └── requirements.txt       # Dependências Python
├── tests/                     # Testes automatizados
│   └── test_fraud_detection.py
├── docs/                      # Documentação
│   ├── API_DOCUMENTATION.md
│   └── API_USAGE.md          # Guia de uso da API
├── dashboard.py               # Dashboard Streamlit
├── sample_data.csv           # Dados de exemplo
├── docker-compose.yml        # Orquestração de containers
├── Dockerfile               # Imagem Docker
├── deploy.sh               # Script de deploy automatizado
├── start.sh               # Script de inicialização
└── .env.example          # Variáveis de ambiente
```

## Instalação e Execução

### Método Rápido (Recomendado)
```bash
# Torna o script executável e inicia tudo automaticamente
chmod +x start.sh
./start.sh
```

### Método Manual

#### 1. Configurar Ambiente
```bash
# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r backend/requirements.txt
```

#### 2. Configurar Variáveis de Ambiente
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

#### 3. Iniciar Backend API
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. Iniciar Dashboard (em outro terminal)
```bash
streamlit run dashboard.py --server.port 8501
```

### 🐳 Deploy com Docker (Produção)
```bash
# Deploy completo com todos os serviços
./deploy.sh docker

# Ou manualmente
docker-compose up -d
```

### Acessar Aplicação
- **Dashboard Web**: http://localhost:8501
- **API**: http://localhost:8000
- **Documentação API**: http://localhost:8000/docs
- **Monitoramento**: http://localhost:3000 (Grafana - opcional)

## 🧪 Testes e Qualidade

### Executar Testes
```bash
# Executar todos os testes
./deploy.sh test

# Ou manualmente
python -m pytest tests/ -v --cov=backend/app --cov-report=html
```

### Cobertura de Testes
- ✅ Detecção de fraude (regras simples)
- ✅ Algoritmos de Machine Learning
- ✅ Feature engineering
- ✅ APIs endpoints
- ✅ Validação de dados
- ✅ Performance e escalabilidade

## 📊 Monitoramento e Observabilidade

### Scripts de Monitoramento
```bash
# Verificar saúde dos serviços
./deploy.sh monitor

# Criar backup dos dados
./deploy.sh backup

# Fazer rollback se necessário
./deploy.sh rollback

# Limpeza de arquivos antigos
./deploy.sh cleanup
```

### Métricas Disponíveis
- 📈 Taxa de detecção de fraude
- ⏱️ Tempo de processamento por lote
- 🔍 Distribuição de scores de risco
- 📊 Volume de transações por cliente
- 🚨 Alertas de alta criticidade

## 🔧 Configuração Avançada

### Apetite de Risco
```python
# Configurações disponíveis
{
    "sensitivity": "low|medium|high",
    "enable_ml_detection": true,
    "custom_thresholds": {
        "high_value": 1000000.0,
        "low_value": 100.0,
        "short_term_days": 7
    }
}
```

### Regras de Detecção
1. **Sem Documento Fiscal** (Peso: 0.8)
2. **Valores Extremos** (Peso: 0.6)
3. **Prazos Inadequados** (Peso: 0.7)
4. **Emissão em Finais de Semana** (Peso: 0.3)
5. **Padrões Atípicos por IA** (Peso: 0.9)

## 📋 Campos de Dados Obrigatórios

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| id_duplicata | string | Identificador único | "DUP001" |
| sacador | string | Empresa emissora | "Empresa ABC Ltda" |
| sacado | string | Empresa devedora | "Cliente XYZ SA" |
| valor | float | Valor em reais | 15000.50 |
| data_emissao | string | Data emissão (YYYY-MM-DD) | "2024-01-15" |
| data_vencimento | string | Data vencimento (YYYY-MM-DD) | "2024-02-15" |
| tipo_documento | string | Tipo do documento | "Duplicata" |
| documento_fiscal_vinculado | boolean | Possui NF vinculada | true/false |
| status | string | Status atual | "Ativo" |

## 🚀 Exemplos de Uso

### 1. Upload via API
```bash
curl -X POST "http://localhost:8000/upload" \
     -H "Authorization: Bearer SEU_TOKEN" \
     -F "file=@duplicatas.csv"
```

### 2. Consultar Duplicatas Suspeitas
```bash
curl -X GET "http://localhost:8000/duplicatas?suspicious_only=true" \
     -H "Authorization: Bearer SEU_TOKEN"
```

### 3. Configurar Apetite de Risco
```bash
curl -X POST "http://localhost:8000/config/risk-appetite" \
     -H "Authorization: Bearer SEU_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"sensitivity": "high", "enable_ml_detection": true}'
```

### 4. Exportar Relatório
```bash
curl -X GET "http://localhost:8000/export/report?format=csv&suspicious_only=true" \
     -H "Authorization: Bearer SEU_TOKEN" \
     -o relatorio_suspeitas.csv
```

## 🎯 Casos de Uso Empresariais

### Para Fintechs
- Validação automática de recebíveis
- Redução de risco de crédito
- Compliance regulatório
- Integração via API

### Para Bancos
- Due diligence automatizada
- Análise de carteiras de recebíveis
- Detecção de fraudes em tempo real
- Relatórios para auditoria

### Para Factorings
- Avaliação de risco de duplicatas
- Precificação dinâmica
- Monitoramento de portfólio
- Alertas de anomalias

## 🏆 Diferenciais Técnicos

- ✅ **Explicabilidade Total**: Cada decisão da IA é justificada
- ✅ **Multi-tenant Seguro**: Isolamento completo entre clientes
- ✅ **APIs Enterprise**: Documentadas, versionadas e escaláveis
- ✅ **Configuração Flexível**: Apetite de risco ajustável por cliente
- ✅ **Interface Intuitiva**: Dashboard para usuários não-técnicos
- ✅ **Auditoria Completa**: Logs detalhados de todas as operações
- ✅ **Deploy Flexível**: On-premise, cloud ou híbrido
- ✅ **Testes Automatizados**: Cobertura completa de funcionalidades

## 📞 Suporte e Documentação

- 📚 **Documentação Completa**: `/docs/API_USAGE.md`
- 🔧 **API Interativa**: http://localhost:8000/docs
- 📊 **Dashboard**: http://localhost:8501
- 🧪 **Testes**: `python -m pytest tests/`
- 📧 **Suporte**: Abra uma issue no repositório

## 📄 Licença

MIT License - Veja o arquivo LICENSE para detalhes.

---

**Desenvolvido para transformar a detecção de fraude em recebíveis através de IA explicável e configurável.**