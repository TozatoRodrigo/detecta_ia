# API Documentation - Fraud Detection Platform

## Visão Geral

A API da Plataforma de Detecção de Fraude oferece endpoints RESTful para upload, processamento e análise de duplicatas escriturais, com detecção automática de fraudes usando regras de negócio e modelos de Machine Learning.

## Base URL

```
http://localhost:8000
```

## Autenticação

A API usa autenticação JWT Bearer Token. Todos os endpoints (exceto `/auth/login`) requerem o header:

```
Authorization: Bearer <token>
```

### POST /auth/login

Gera token de autenticação para um cliente.

**Parâmetros:**
- `client_id` (string): ID do cliente

**Resposta:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

## Endpoints Principais

### POST /upload

Faz upload e processa arquivo CSV de duplicatas.

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Body:**
- `file`: Arquivo CSV com duplicatas

**Campos obrigatórios no CSV:**
- `id_duplicata`: ID único da duplicata
- `sacador`: Nome do sacador (emissor)
- `sacado`: Nome do sacado (devedor)
- `valor`: Valor da duplicata em reais
- `data_emissao`: Data de emissão (YYYY-MM-DD)
- `data_vencimento`: Data de vencimento (YYYY-MM-DD)
- `tipo_documento`: Tipo do documento
- `documento_fiscal_vinculado`: true/false
- `status`: Status atual da duplicata

**Resposta:**
```json
{
  "message": "Arquivo processado com sucesso",
  "total_records": 100,
  "suspicious_count": 15,
  "processing_time": 2.34
}
```

### GET /duplicatas

Retorna lista de duplicatas processadas.

**Parâmetros de Query:**
- `suspicious_only` (boolean, opcional): Retorna apenas duplicatas suspeitas

**Resposta:**
```json
[
  {
    "id_duplicata": "DUP001",
    "sacador": "Empresa A",
    "sacado": "Cliente X",
    "valor": 10000.0,
    "data_emissao": "2024-01-15",
    "data_vencimento": "2024-02-15",
    "tipo_documento": "Duplicata",
    "documento_fiscal_vinculado": false,
    "status": "Ativo",
    "is_suspicious": true,
    "fraud_reasons": ["Sem documento fiscal vinculado"],
    "risk_score": 0.85
  }
]
```

### GET /stats

Retorna estatísticas das duplicatas processadas.

**Resposta:**
```json
{
  "total_duplicatas": 100,
  "suspicious_count": 15,
  "suspicious_percentage": 15.0,
  "without_fiscal_doc": 12,
  "avg_risk_score": 0.23
}
```

### POST /config/risk-appetite

Atualiza configuração de apetite de risco.

**Body:**
```json
{
  "sensitivity": "medium",
  "threshold": 0.5,
  "enable_ml_detection": true
}
```

**Valores para sensitivity:**
- `"low"`: Baixa sensibilidade (menos flags)
- `"medium"`: Sensibilidade média
- `"high"`: Alta sensibilidade (mais flags)

### GET /config/risk-appetite

Retorna configuração atual de apetite de risco.

**Resposta:**
```json
{
  "sensitivity": "medium",
  "threshold": null,
  "enable_ml_detection": true
}
```

## Regras de Detecção de Fraude

### Regras Simples

1. **Sem Documento Fiscal**: Duplicatas sem documento fiscal vinculado
2. **Valor Alto**: Valores acima de R$ 1.000.000
3. **Prazo Curto**: Vencimento em menos de 7 dias

### Detecção ML

Utiliza **Isolation Forest** para detectar anomalias baseadas em:
- Valor da duplicata
- Prazo de vencimento
- Padrões do sacador
- Padrões do sacado

## Códigos de Status HTTP

- `200`: Sucesso
- `400`: Erro na requisição (dados inválidos)
- `401`: Não autorizado (token inválido)
- `404`: Recurso não encontrado
- `500`: Erro interno do servidor

## Exemplos de Uso

### Autenticação
```bash
curl -X POST "http://localhost:8000/auth/login?client_id=meu_cliente" \
  -H "Content-Type: application/json"
```

### Upload de Arquivo
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@duplicatas.csv"
```

### Consultar Duplicatas Suspeitas
```bash
curl -X GET "http://localhost:8000/duplicatas?suspicious_only=true" \
  -H "Authorization: Bearer <token>"
```

### Atualizar Configuração de Risco
```bash
curl -X POST "http://localhost:8000/config/risk-appetite" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"sensitivity": "high", "enable_ml_detection": true}'
```

## Limitações e Considerações

- Máximo de 10.000 registros por upload
- Tokens expiram em 24 horas
- Dados são armazenados em memória (implementar banco de dados em produção)
- Modelos ML são retreinados a cada upload

## Documentação Interativa

Acesse a documentação interativa Swagger em:
```
http://localhost:8000/docs
```

## Suporte

Para suporte técnico ou dúvidas sobre a API, consulte a documentação completa ou entre em contato com a equipe de desenvolvimento.