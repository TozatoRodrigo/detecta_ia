# Guia de Uso da API - Plataforma de Detecção de Fraude

## Visão Geral

Esta API permite detectar fraudes em duplicatas escriturais usando regras de negócio e algoritmos de Machine Learning. A plataforma é multi-tenant, permitindo que diferentes clientes (fintechs, bancos, etc.) utilizem o serviço de forma isolada.

## Autenticação

### 1. Obter Token de Acesso

```bash
curl -X POST "http://localhost:8000/auth/login?client_id=seu_client_id" \
     -H "Content-Type: application/json"
```

**Resposta:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### 2. Usar Token nas Requisições

Inclua o token no header `Authorization`:
```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Upload e Processamento de Dados

### Formato do Arquivo CSV

O arquivo deve conter as seguintes colunas obrigatórias:

| Campo | Tipo | Descrição | Exemplo |
|-------|------|-----------|---------|
| id_duplicata | string | Identificador único | "DUP001" |
| sacador | string | Empresa emissora | "Empresa ABC Ltda" |
| sacado | string | Empresa pagadora | "Cliente XYZ SA" |
| valor | float | Valor da duplicata | 15000.50 |
| data_emissao | string | Data de emissão (YYYY-MM-DD) | "2024-01-15" |
| data_vencimento | string | Data de vencimento (YYYY-MM-DD) | "2024-02-15" |
| tipo_documento | string | Tipo do documento | "Duplicata" |
| documento_fiscal_vinculado | boolean | Se tem NF vinculada | true/false |
| status | string | Status atual | "Ativo" |

### Upload via API

```bash
curl -X POST "http://localhost:8000/upload" \
     -H "Authorization: Bearer SEU_TOKEN" \
     -F "file=@duplicatas.csv"
```

**Resposta:**
```json
{
  "message": "Arquivo processado com sucesso",
  "total_records": 150,
  "suspicious_count": 23,
  "processing_time": 2.45
}
```

## Consulta de Dados

### Listar Todas as Duplicatas

```bash
curl -X GET "http://localhost:8000/duplicatas" \
     -H "Authorization: Bearer SEU_TOKEN"
```

### Listar Apenas Duplicatas Suspeitas

```bash
curl -X GET "http://localhost:8000/duplicatas?suspicious_only=true" \
     -H "Authorization: Bearer SEU_TOKEN"
```

**Resposta:**
```json
[
  {
    "id_duplicata": "DUP002",
    "sacador": "Empresa Gamma SA",
    "sacado": "Cliente Delta Inc",
    "valor": 75000.0,
    "data_emissao": "2024-01-16",
    "data_vencimento": "2024-01-20",
    "tipo_documento": "Duplicata",
    "documento_fiscal_vinculado": false,
    "status": "Ativo",
    "is_suspicious": true,
    "fraud_reasons": [
      "Sem documento fiscal vinculado",
      "Prazo de vencimento muito curto (< 7 dias)"
    ],
    "risk_score": 0.85
  }
]
```

## Estatísticas e Analytics

### Obter Estatísticas Gerais

```bash
curl -X GET "http://localhost:8000/stats" \
     -H "Authorization: Bearer SEU_TOKEN"
```

**Resposta:**
```json
{
  "total_duplicatas": 150,
  "suspicious_count": 23,
  "suspicious_percentage": 15.3,
  "without_fiscal_doc": 18,
  "avg_risk_score": 0.34,
  "total_value": 2500000.0,
  "suspicious_value": 850000.0,
  "suspicious_value_percentage": 34.0,
  "top_risk_reasons": [
    {"reason": "Sem documento fiscal vinculado", "count": 18},
    {"reason": "Valor muito alto (acima de R$ 1M)", "count": 5}
  ],
  "sacador_stats": {
    "Empresa Alpha Ltda": {
      "total_duplicatas": 25,
      "suspicious_count": 8,
      "suspicious_rate": 32.0,
      "total_value": 450000.0,
      "avg_risk_score": 0.42
    }
  }
}
```

### Análise de Tendências

```bash
curl -X GET "http://localhost:8000/analytics/trends" \
     -H "Authorization: Bearer SEU_TOKEN"
```

## Configuração de Apetite de Risco

### Atualizar Configuração

```bash
curl -X POST "http://localhost:8000/config/risk-appetite" \
     -H "Authorization: Bearer SEU_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "sensitivity": "high",
       "enable_ml_detection": true
     }'
```

**Parâmetros:**
- `sensitivity`: "low", "medium", "high"
- `enable_ml_detection`: true/false

### Consultar Configuração Atual

```bash
curl -X GET "http://localhost:8000/config/risk-appetite" \
     -H "Authorization: Bearer SEU_TOKEN"
```

## Exportação de Relatórios

### Exportar em CSV

```bash
curl -X GET "http://localhost:8000/export/report?format=csv&suspicious_only=true" \
     -H "Authorization: Bearer SEU_TOKEN" \
     -o relatorio_suspeitas.csv
```

### Exportar em JSON

```bash
curl -X GET "http://localhost:8000/export/report?format=json" \
     -H "Authorization: Bearer SEU_TOKEN"
```

## Regras de Detecção de Fraude

### Regras Simples (Sempre Aplicadas)

1. **Sem Documento Fiscal**: Duplicatas sem NF vinculada
2. **Valores Extremos**: Acima de R$ 1M ou abaixo de R$ 100
3. **Prazo Inadequado**: Vencimento < 7 dias ou > 1 ano
4. **Emissão em Final de Semana**: Sábado ou domingo
5. **Valores Redondos**: Múltiplos de R$ 1.000 acima de R$ 10.000

### Detecção por Machine Learning

- **Isolation Forest**: Detecta padrões anômalos multivariados
- **Local Outlier Factor**: Identifica outliers locais
- **Features Utilizadas**:
  - Valor e transformações (log, z-score)
  - Padrões temporais (dias para vencimento, fim de semana)
  - Frequência de sacador/sacado
  - Estatísticas históricas por sacador
  - Indicadores de risco combinados

## Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 400 | Dados inválidos ou arquivo malformado |
| 401 | Token inválido ou expirado |
| 404 | Recurso não encontrado |
| 422 | Erro de validação dos dados |
| 500 | Erro interno do servidor |

## Limites e Quotas

- **Tamanho máximo do arquivo**: 50MB
- **Registros por upload**: 100.000
- **Requests por minuto**: 1.000
- **Retenção de dados**: 90 dias

## Exemplos de Integração

### Python

```python
import requests
import pandas as pd

# Autenticação
response = requests.post("http://localhost:8000/auth/login", 
                        params={"client_id": "meu_client"})
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Upload de arquivo
with open("duplicatas.csv", "rb") as file:
    files = {"file": ("duplicatas.csv", file, "text/csv")}
    response = requests.post("http://localhost:8000/upload", 
                           files=files, headers=headers)
    print(response.json())

# Consultar duplicatas suspeitas
response = requests.get("http://localhost:8000/duplicatas?suspicious_only=true", 
                       headers=headers)
suspeitas = response.json()
print(f"Encontradas {len(suspeitas)} duplicatas suspeitas")
```

### JavaScript/Node.js

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

// Autenticação
const authResponse = await axios.post('http://localhost:8000/auth/login', null, {
  params: { client_id: 'meu_client' }
});
const token = authResponse.data.access_token;
const headers = { Authorization: `Bearer ${token}` };

// Upload de arquivo
const form = new FormData();
form.append('file', fs.createReadStream('duplicatas.csv'));

const uploadResponse = await axios.post('http://localhost:8000/upload', form, {
  headers: { ...headers, ...form.getHeaders() }
});
console.log(uploadResponse.data);

// Consultar estatísticas
const statsResponse = await axios.get('http://localhost:8000/stats', { headers });
console.log(statsResponse.data);
```

## Suporte

Para dúvidas técnicas ou suporte:
- Documentação interativa: http://localhost:8000/docs
- Dashboard web: http://localhost:8501
- Email: suporte@frauddetection.com