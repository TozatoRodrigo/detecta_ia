"""
Sistema de Auditoria e Logs para a Plataforma de Detecção de Fraude
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import os

class AuditEventType(Enum):
    """Tipos de eventos de auditoria"""
    LOGIN = "login"
    UPLOAD = "upload"
    QUERY = "query"
    CONFIG_CHANGE = "config_change"
    EXPORT = "export"
    ML_PREDICTION = "ml_prediction"
    FRAUD_DETECTION = "fraud_detection"

class AuditLogger:
    """Sistema de auditoria e logs"""
    
    def __init__(self, log_file: str = "audit.log"):
        self.log_file = log_file
        self.setup_logger()
    
    def setup_logger(self):
        """Configura o logger de auditoria"""
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Remove handlers existentes
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Handler para arquivo
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formato dos logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_event(
        self,
        event_type: AuditEventType,
        client_id: str,
        details: Dict[str, Any],
        user_ip: Optional[str] = None,
        success: bool = True
    ):
        """Registra um evento de auditoria"""
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "client_id": client_id,
            "user_ip": user_ip,
            "success": success,
            "details": details
        }
        
        log_message = json.dumps(audit_record, ensure_ascii=False)
        
        if success:
            self.logger.info(log_message)
        else:
            self.logger.error(log_message)
    
    def log_login(self, client_id: str, user_ip: str, success: bool = True):
        """Log de tentativa de login"""
        self.log_event(
            AuditEventType.LOGIN,
            client_id,
            {"action": "authentication_attempt"},
            user_ip,
            success
        )
    
    def log_upload(
        self,
        client_id: str,
        filename: str,
        total_records: int,
        suspicious_count: int,
        processing_time: float,
        user_ip: str
    ):
        """Log de upload de arquivo"""
        self.log_event(
            AuditEventType.UPLOAD,
            client_id,
            {
                "filename": filename,
                "total_records": total_records,
                "suspicious_count": suspicious_count,
                "processing_time": processing_time,
                "suspicious_rate": (suspicious_count / total_records) * 100 if total_records > 0 else 0
            },
            user_ip
        )
    
    def log_query(
        self,
        client_id: str,
        query_type: str,
        filters: Dict[str, Any],
        result_count: int,
        user_ip: str
    ):
        """Log de consulta de dados"""
        self.log_event(
            AuditEventType.QUERY,
            client_id,
            {
                "query_type": query_type,
                "filters": filters,
                "result_count": result_count
            },
            user_ip
        )
    
    def log_config_change(
        self,
        client_id: str,
        old_config: Dict[str, Any],
        new_config: Dict[str, Any],
        user_ip: str
    ):
        """Log de mudança de configuração"""
        self.log_event(
            AuditEventType.CONFIG_CHANGE,
            client_id,
            {
                "old_config": old_config,
                "new_config": new_config,
                "changes": self._get_config_changes(old_config, new_config)
            },
            user_ip
        )
    
    def log_export(
        self,
        client_id: str,
        export_format: str,
        record_count: int,
        suspicious_only: bool,
        user_ip: str
    ):
        """Log de exportação de dados"""
        self.log_event(
            AuditEventType.EXPORT,
            client_id,
            {
                "format": export_format,
                "record_count": record_count,
                "suspicious_only": suspicious_only
            },
            user_ip
        )
    
    def log_ml_prediction(
        self,
        client_id: str,
        model_type: str,
        total_predictions: int,
        anomalies_detected: int,
        avg_score: float
    ):
        """Log de predições do modelo ML"""
        self.log_event(
            AuditEventType.ML_PREDICTION,
            client_id,
            {
                "model_type": model_type,
                "total_predictions": total_predictions,
                "anomalies_detected": anomalies_detected,
                "anomaly_rate": (anomalies_detected / total_predictions) * 100 if total_predictions > 0 else 0,
                "avg_score": avg_score
            }
        )
    
    def log_fraud_detection(
        self,
        client_id: str,
        duplicata_id: str,
        fraud_reasons: list,
        risk_score: float,
        detection_method: str
    ):
        """Log de detecção de fraude específica"""
        self.log_event(
            AuditEventType.FRAUD_DETECTION,
            client_id,
            {
                "duplicata_id": duplicata_id,
                "fraud_reasons": fraud_reasons,
                "risk_score": risk_score,
                "detection_method": detection_method,
                "severity": self._get_severity(risk_score)
            }
        )
    
    def _get_config_changes(self, old_config: Dict, new_config: Dict) -> Dict[str, Any]:
        """Identifica mudanças entre configurações"""
        changes = {}
        
        for key in set(old_config.keys()) | set(new_config.keys()):
            old_value = old_config.get(key)
            new_value = new_config.get(key)
            
            if old_value != new_value:
                changes[key] = {
                    "from": old_value,
                    "to": new_value
                }
        
        return changes
    
    def _get_severity(self, risk_score: float) -> str:
        """Determina a severidade baseada no score de risco"""
        if risk_score >= 0.8:
            return "HIGH"
        elif risk_score >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_audit_summary(self, client_id: str, days: int = 7) -> Dict[str, Any]:
        """Gera resumo de auditoria para um cliente"""
        # Em uma implementação real, isso consultaria um banco de dados
        # Por enquanto, retorna um exemplo
        return {
            "client_id": client_id,
            "period_days": days,
            "total_events": 150,
            "events_by_type": {
                "login": 25,
                "upload": 8,
                "query": 95,
                "config_change": 3,
                "export": 12,
                "fraud_detection": 7
            },
            "fraud_detections": {
                "total": 7,
                "high_severity": 2,
                "medium_severity": 3,
                "low_severity": 2
            },
            "most_active_days": [
                {"date": "2024-01-20", "events": 35},
                {"date": "2024-01-19", "events": 28}
            ]
        }

# Instância global do logger de auditoria
audit_logger = AuditLogger()