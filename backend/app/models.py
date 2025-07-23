from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class RiskSensitivity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class DocumentType(str, Enum):
    DUPLICATA = "Duplicata"
    NOTA_PROMISSORIA = "Nota Promissória"
    CHEQUE = "Cheque"

class DuplicataStatus(str, Enum):
    ATIVO = "Ativo"
    VENCIDO = "Vencido"
    PAGO = "Pago"
    CANCELADO = "Cancelado"

class DuplicataBase(BaseModel):
    id_duplicata: str = Field(..., description="ID único da duplicata")
    sacador: str = Field(..., description="Nome do sacador (emissor)")
    sacado: str = Field(..., description="Nome do sacado (devedor)")
    valor: float = Field(..., gt=0, description="Valor da duplicata em reais")
    data_emissao: str = Field(..., description="Data de emissão (YYYY-MM-DD)")
    data_vencimento: str = Field(..., description="Data de vencimento (YYYY-MM-DD)")
    tipo_documento: str = Field(..., description="Tipo do documento")
    documento_fiscal_vinculado: bool = Field(..., description="Se possui documento fiscal vinculado")
    status: str = Field(..., description="Status atual da duplicata")

class DuplicataResponse(DuplicataBase):
    is_suspicious: bool = Field(..., description="Se a duplicata é suspeita")
    fraud_reasons: List[str] = Field(..., description="Motivos pelos quais foi flagada")
    risk_score: float = Field(..., ge=0, le=1, description="Score de risco (0-1)")
    processed_at: Optional[datetime] = Field(None, description="Timestamp do processamento")

class RiskAppetiteConfig(BaseModel):
    sensitivity: RiskSensitivity = Field(RiskSensitivity.MEDIUM, description="Sensibilidade do modelo")
    threshold: Optional[float] = Field(None, ge=0, le=1, description="Threshold customizado")
    enable_ml_detection: bool = Field(True, description="Habilitar detecção ML")
    enable_simple_rules: bool = Field(True, description="Habilitar regras simples")

class UploadResponse(BaseModel):
    message: str = Field(..., description="Mensagem de status")
    total_records: int = Field(..., description="Total de registros processados")
    suspicious_count: int = Field(..., description="Número de registros suspeitos")
    processing_time: float = Field(..., description="Tempo de processamento em segundos")
    client_id: str = Field(..., description="ID do cliente")

class StatsResponse(BaseModel):
    total_duplicatas: int = Field(..., description="Total de duplicatas")
    suspicious_count: int = Field(..., description="Número de suspeitas")
    suspicious_percentage: float = Field(..., description="Percentual de suspeitas")
    without_fiscal_doc: int = Field(..., description="Sem documento fiscal")
    avg_risk_score: float = Field(..., description="Score médio de risco")
    top_sacadores_risk: List[Dict[str, Any]] = Field([], description="Top sacadores por risco")
    top_sacados_risk: List[Dict[str, Any]] = Field([], description="Top sacados por risco")

class FraudRule(BaseModel):
    name: str = Field(..., description="Nome da regra")
    description: str = Field(..., description="Descrição da regra")
    enabled: bool = Field(True, description="Se a regra está ativa")
    weight: float = Field(1.0, ge=0, le=1, description="Peso da regra no score final")

class MLModelInfo(BaseModel):
    model_type: str = Field(..., description="Tipo do modelo ML")
    trained_at: Optional[datetime] = Field(None, description="Quando foi treinado")
    training_samples: int = Field(0, description="Número de amostras de treino")
    contamination_rate: float = Field(..., description="Taxa de contaminação usada")
    feature_importance: Dict[str, float] = Field({}, description="Importância das features")

class ClientInfo(BaseModel):
    client_id: str = Field(..., description="ID do cliente")
    name: str = Field(..., description="Nome do cliente")
    created_at: datetime = Field(..., description="Data de criação")
    last_activity: Optional[datetime] = Field(None, description="Última atividade")
    total_duplicatas_processed: int = Field(0, description="Total de duplicatas processadas")

class AuthRequest(BaseModel):
    client_id: str = Field(..., description="ID do cliente para autenticação")

class AuthResponse(BaseModel):
    access_token: str = Field(..., description="Token de acesso JWT")
    token_type: str = Field("bearer", description="Tipo do token")
    expires_in: int = Field(..., description="Tempo de expiração em segundos")