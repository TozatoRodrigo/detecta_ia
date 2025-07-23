"""
Sistema de Configuração Avançado para a Plataforma de Detecção de Fraude
"""
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseSettings, Field
from enum import Enum
import json

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class DatabaseConfig(BaseSettings):
    """Configurações do banco de dados"""
    url: str = Field(default="sqlite:///./fraud_detection.db", env="DATABASE_URL")
    echo: bool = Field(default=False, env="DATABASE_ECHO")
    pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")

class SecurityConfig(BaseSettings):
    """Configurações de segurança"""
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    token_expire_hours: int = Field(default=24, env="TOKEN_EXPIRE_HOURS")
    bcrypt_rounds: int = Field(default=12, env="BCRYPT_ROUNDS")
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=1000, env="RATE_LIMIT_PER_MINUTE")
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")

class MLConfig(BaseSettings):
    """Configurações de Machine Learning"""
    default_contamination: float = Field(default=0.1, env="ML_DEFAULT_CONTAMINATION")
    model_retrain_interval_hours: int = Field(default=24, env="ML_RETRAIN_INTERVAL")
    max_features_isolation_forest: int = Field(default=10, env="ML_MAX_FEATURES")
    n_estimators: int = Field(default=200, env="ML_N_ESTIMATORS")
    
    # Thresholds por sensibilidade
    sensitivity_thresholds: Dict[str, float] = {
        "low": 0.05,
        "medium": 0.1,
        "high": 0.2
    }
    
    # Features para o modelo
    numerical_features: List[str] = [
        "valor", "valor_log", "valor_zscore", "days_to_maturity",
        "sacador_frequency", "sacado_frequency", "tipo_documento_frequency",
        "sacador_valor_mean", "sacador_valor_std", "sacador_count",
        "sacador_days_mean", "sacador_fiscal_rate", "valor_per_day",
        "sacador_deviation", "high_value_flag", "short_term_flag", "no_fiscal_flag"
    ]

class FraudRulesConfig(BaseSettings):
    """Configurações das regras de detecção de fraude"""
    
    # Limites de valor
    high_value_threshold: float = Field(default=1000000.0, env="FRAUD_HIGH_VALUE_THRESHOLD")
    low_value_threshold: float = Field(default=100.0, env="FRAUD_LOW_VALUE_THRESHOLD")
    
    # Limites de prazo
    min_days_to_maturity: int = Field(default=7, env="FRAUD_MIN_DAYS_MATURITY")
    max_days_to_maturity: int = Field(default=365, env="FRAUD_MAX_DAYS_MATURITY")
    
    # Detecção de padrões
    round_number_threshold: float = Field(default=10000.0, env="FRAUD_ROUND_NUMBER_THRESHOLD")
    weekend_emission_risk_multiplier: float = Field(default=1.2, env="FRAUD_WEEKEND_MULTIPLIER")
    
    # Pesos das regras
    rule_weights: Dict[str, float] = {
        "no_fiscal_document": 0.8,
        "high_value": 0.6,
        "low_value": 0.4,
        "short_term": 0.7,
        "long_term": 0.5,
        "weekend_emission": 0.3,
        "round_numbers": 0.4,
        "invalid_dates": 0.9
    }

class LoggingConfig(BaseSettings):
    """Configurações de logging"""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    file: str = Field(default="app.log", env="LOG_FILE")
    max_file_size_mb: int = Field(default=100, env="LOG_MAX_FILE_SIZE_MB")
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Auditoria
    audit_enabled: bool = Field(default=True, env="AUDIT_ENABLED")
    audit_file: str = Field(default="audit.log", env="AUDIT_FILE")
    audit_retention_days: int = Field(default=365, env="AUDIT_RETENTION_DAYS")

class APIConfig(BaseSettings):
    """Configurações da API"""
    title: str = "Fraud Detection Platform API"
    description: str = "API para detecção de fraude em duplicatas escriturais"
    version: str = "1.0.0"
    
    # CORS
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # Paginação
    default_page_size: int = Field(default=100, env="API_DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=1000, env="API_MAX_PAGE_SIZE")

class RedisConfig(BaseSettings):
    """Configurações do Redis (para cache e sessões)"""
    url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    db: int = Field(default=0, env="REDIS_DB")
    
    # Cache settings
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    session_ttl_seconds: int = Field(default=86400, env="SESSION_TTL_SECONDS")

class NotificationConfig(BaseSettings):
    """Configurações de notificações"""
    email_enabled: bool = Field(default=False, env="NOTIFICATION_EMAIL_ENABLED")
    smtp_host: str = Field(default="localhost", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str = Field(default="", env="SMTP_USERNAME")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    
    # Webhooks
    webhook_enabled: bool = Field(default=False, env="NOTIFICATION_WEBHOOK_ENABLED")
    webhook_urls: List[str] = Field(default=[], env="NOTIFICATION_WEBHOOK_URLS")
    
    # Alertas
    high_risk_alert_threshold: float = Field(default=0.8, env="ALERT_HIGH_RISK_THRESHOLD")
    batch_alert_suspicious_rate: float = Field(default=0.3, env="ALERT_BATCH_SUSPICIOUS_RATE")

class Settings(BaseSettings):
    """Configurações principais da aplicação"""
    
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Sub-configurações
    database: DatabaseConfig = DatabaseConfig()
    security: SecurityConfig = SecurityConfig()
    ml: MLConfig = MLConfig()
    fraud_rules: FraudRulesConfig = FraudRulesConfig()
    logging: LoggingConfig = LoggingConfig()
    api: APIConfig = APIConfig()
    redis: RedisConfig = RedisConfig()
    notifications: NotificationConfig = NotificationConfig()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def is_production(self) -> bool:
        """Verifica se está em produção"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Verifica se está em desenvolvimento"""
        return self.environment == Environment.DEVELOPMENT
    
    def get_fraud_rule_config(self, rule_name: str) -> Dict[str, Any]:
        """Obtém configuração específica de uma regra de fraude"""
        base_config = {
            "enabled": True,
            "weight": self.fraud_rules.rule_weights.get(rule_name, 1.0)
        }
        
        if rule_name == "no_fiscal_document":
            base_config.update({
                "description": "Duplicata sem documento fiscal vinculado",
                "severity": "high"
            })
        elif rule_name == "high_value":
            base_config.update({
                "threshold": self.fraud_rules.high_value_threshold,
                "description": f"Valor acima de R$ {self.fraud_rules.high_value_threshold:,.2f}",
                "severity": "medium"
            })
        elif rule_name == "low_value":
            base_config.update({
                "threshold": self.fraud_rules.low_value_threshold,
                "description": f"Valor abaixo de R$ {self.fraud_rules.low_value_threshold:.2f}",
                "severity": "low"
            })
        
        return base_config
    
    def get_ml_contamination(self, sensitivity: str) -> float:
        """Obtém taxa de contaminação baseada na sensibilidade"""
        return self.ml.sensitivity_thresholds.get(sensitivity, self.ml.default_contamination)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte configurações para dicionário"""
        return {
            "environment": self.environment.value,
            "debug": self.debug,
            "database": {
                "url": self.database.url,
                "echo": self.database.echo
            },
            "security": {
                "token_expire_hours": self.security.token_expire_hours,
                "rate_limit_per_minute": self.security.rate_limit_per_minute
            },
            "ml": {
                "default_contamination": self.ml.default_contamination,
                "model_retrain_interval_hours": self.ml.model_retrain_interval_hours
            },
            "fraud_rules": {
                "high_value_threshold": self.fraud_rules.high_value_threshold,
                "low_value_threshold": self.fraud_rules.low_value_threshold
            }
        }

# Instância global das configurações
settings = Settings()

# Função para recarregar configurações
def reload_settings():
    """Recarrega as configurações do arquivo .env"""
    global settings
    settings = Settings()
    return settings

# Função para validar configurações
def validate_settings() -> List[str]:
    """Valida as configurações e retorna lista de erros"""
    errors = []
    
    # Validar configurações críticas
    if settings.security.secret_key == "your-secret-key-change-in-production":
        if settings.is_production():
            errors.append("SECRET_KEY deve ser alterada em produção")
    
    if settings.database.url.startswith("sqlite") and settings.is_production():
        errors.append("SQLite não é recomendado para produção")
    
    if settings.ml.default_contamination <= 0 or settings.ml.default_contamination >= 1:
        errors.append("ML_DEFAULT_CONTAMINATION deve estar entre 0 e 1")
    
    if settings.fraud_rules.high_value_threshold <= settings.fraud_rules.low_value_threshold:
        errors.append("FRAUD_HIGH_VALUE_THRESHOLD deve ser maior que FRAUD_LOW_VALUE_THRESHOLD")
    
    return errors

# Função para obter configurações específicas do cliente
def get_client_config(client_id: str) -> Dict[str, Any]:
    """Obtém configurações específicas de um cliente"""
    # Em uma implementação real, isso viria do banco de dados
    # Por enquanto, retorna configurações padrão
    return {
        "client_id": client_id,
        "risk_sensitivity": "medium",
        "ml_detection_enabled": True,
        "custom_rules": [],
        "notification_preferences": {
            "email_alerts": False,
            "webhook_alerts": False
        },
        "data_retention_days": 90,
        "max_file_size_mb": settings.security.max_file_size_mb
    }

if __name__ == "__main__":
    # Teste das configurações
    print("🔧 Configurações da Aplicação")
    print("=" * 40)
    print(f"Ambiente: {settings.environment.value}")
    print(f"Debug: {settings.debug}")
    print(f"Banco: {settings.database.url}")
    print(f"ML Contamination: {settings.ml.default_contamination}")
    
    # Validar configurações
    errors = validate_settings()
    if errors:
        print("\n❌ Erros de configuração:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ Configurações válidas!")