"""
Sistema de Banco de Dados para a Plataforma de Detecção de Fraude
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração do banco
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fraud_detection.db")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Client(Base):
    """Modelo para clientes da plataforma"""
    __tablename__ = "clients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Configurações do cliente
    risk_sensitivity = Column(String, default="medium")
    ml_detection_enabled = Column(Boolean, default=True)
    max_file_size_mb = Column(Integer, default=50)
    data_retention_days = Column(Integer, default=90)

class Duplicata(Base):
    """Modelo para duplicatas"""
    __tablename__ = "duplicatas"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, index=True, nullable=False)
    
    # Dados originais
    id_duplicata = Column(String, nullable=False)
    sacador = Column(String, nullable=False)
    sacado = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    data_emissao = Column(DateTime, nullable=False)
    data_vencimento = Column(DateTime, nullable=False)
    tipo_documento = Column(String, nullable=False)
    documento_fiscal_vinculado = Column(Boolean, nullable=False)
    status = Column(String, nullable=False)
    
    # Resultados da análise
    is_suspicious = Column(Boolean, default=False)
    fraud_reasons = Column(JSON)  # Lista de motivos
    risk_score = Column(Float, default=0.0)
    ml_score = Column(Float, default=0.0)
    detection_method = Column(String)  # "rules", "ml", "both"
    
    # Metadados
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    file_batch_id = Column(String)  # Para rastrear lotes de upload

class ProcessingBatch(Base):
    """Modelo para lotes de processamento"""
    __tablename__ = "processing_batches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, index=True, nullable=False)
    
    filename = Column(String, nullable=False)
    total_records = Column(Integer, nullable=False)
    suspicious_count = Column(Integer, default=0)
    processing_time = Column(Float)
    
    # Configurações usadas no processamento
    risk_sensitivity = Column(String)
    ml_enabled = Column(Boolean)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="processing")  # processing, completed, failed

class AuditLog(Base):
    """Modelo para logs de auditoria"""
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, index=True, nullable=False)
    
    event_type = Column(String, nullable=False)
    event_details = Column(JSON)
    user_ip = Column(String)
    success = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class MLModel(Base):
    """Modelo para armazenar informações dos modelos ML"""
    __tablename__ = "ml_models"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, index=True, nullable=False)
    
    model_type = Column(String, nullable=False)  # isolation_forest, lof
    model_version = Column(String, nullable=False)
    contamination = Column(Float)
    n_samples_trained = Column(Integer)
    
    # Métricas de performance
    accuracy_score = Column(Float)
    precision_score = Column(Float)
    recall_score = Column(Float)
    
    # Metadados
    trained_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    model_path = Column(String)  # Caminho para o arquivo do modelo

# Funções de utilidade para banco de dados

def get_db() -> Session:
    """Dependency para obter sessão do banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Cria todas as tabelas no banco"""
    Base.metadata.create_all(bind=engine)

def get_client_by_id(db: Session, client_id: str) -> Optional[Client]:
    """Busca cliente por ID"""
    return db.query(Client).filter(Client.client_id == client_id).first()

def create_client(db: Session, client_id: str, name: str, email: str = None) -> Client:
    """Cria novo cliente"""
    client = Client(
        client_id=client_id,
        name=name,
        email=email
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

def save_duplicatas_batch(
    db: Session,
    client_id: str,
    duplicatas: List[Dict[str, Any]],
    batch_info: Dict[str, Any]
) -> str:
    """Salva lote de duplicatas no banco"""
    
    # Criar registro do lote
    batch = ProcessingBatch(
        client_id=client_id,
        filename=batch_info.get("filename", "unknown"),
        total_records=len(duplicatas),
        suspicious_count=sum(1 for d in duplicatas if d.get("is_suspicious", False)),
        processing_time=batch_info.get("processing_time", 0),
        risk_sensitivity=batch_info.get("risk_sensitivity", "medium"),
        ml_enabled=batch_info.get("ml_enabled", True),
        status="completed"
    )
    db.add(batch)
    db.flush()  # Para obter o ID
    
    # Salvar duplicatas
    for dup_data in duplicatas:
        duplicata = Duplicata(
            client_id=client_id,
            file_batch_id=batch.id,
            id_duplicata=dup_data["id_duplicata"],
            sacador=dup_data["sacador"],
            sacado=dup_data["sacado"],
            valor=dup_data["valor"],
            data_emissao=datetime.strptime(dup_data["data_emissao"], "%Y-%m-%d"),
            data_vencimento=datetime.strptime(dup_data["data_vencimento"], "%Y-%m-%d"),
            tipo_documento=dup_data["tipo_documento"],
            documento_fiscal_vinculado=dup_data["documento_fiscal_vinculado"],
            status=dup_data["status"],
            is_suspicious=dup_data.get("is_suspicious", False),
            fraud_reasons=dup_data.get("fraud_reasons", []),
            risk_score=dup_data.get("risk_score", 0.0),
            ml_score=dup_data.get("ml_score", 0.0),
            detection_method=dup_data.get("detection_method", "rules"),
            processed_at=datetime.utcnow()
        )
        db.add(duplicata)
    
    db.commit()
    return batch.id

def get_duplicatas_by_client(
    db: Session,
    client_id: str,
    suspicious_only: bool = False,
    limit: int = 1000,
    offset: int = 0
) -> List[Duplicata]:
    """Busca duplicatas por cliente"""
    query = db.query(Duplicata).filter(Duplicata.client_id == client_id)
    
    if suspicious_only:
        query = query.filter(Duplicata.is_suspicious == True)
    
    return query.offset(offset).limit(limit).all()

def get_client_stats(db: Session, client_id: str) -> Dict[str, Any]:
    """Calcula estatísticas para um cliente"""
    
    # Contar duplicatas
    total_query = db.query(Duplicata).filter(Duplicata.client_id == client_id)
    total_duplicatas = total_query.count()
    
    if total_duplicatas == 0:
        return {
            "total_duplicatas": 0,
            "suspicious_count": 0,
            "suspicious_percentage": 0,
            "without_fiscal_doc": 0,
            "avg_risk_score": 0,
            "total_value": 0,
            "suspicious_value": 0
        }
    
    # Duplicatas suspeitas
    suspicious_query = total_query.filter(Duplicata.is_suspicious == True)
    suspicious_count = suspicious_query.count()
    
    # Sem documento fiscal
    no_fiscal_count = total_query.filter(Duplicata.documento_fiscal_vinculado == False).count()
    
    # Valores
    from sqlalchemy import func
    value_stats = db.query(
        func.sum(Duplicata.valor).label('total_value'),
        func.avg(Duplicata.risk_score).label('avg_risk_score')
    ).filter(Duplicata.client_id == client_id).first()
    
    suspicious_value = db.query(func.sum(Duplicata.valor)).filter(
        Duplicata.client_id == client_id,
        Duplicata.is_suspicious == True
    ).scalar() or 0
    
    return {
        "total_duplicatas": total_duplicatas,
        "suspicious_count": suspicious_count,
        "suspicious_percentage": (suspicious_count / total_duplicatas) * 100,
        "without_fiscal_doc": no_fiscal_count,
        "avg_risk_score": float(value_stats.avg_risk_score or 0),
        "total_value": float(value_stats.total_value or 0),
        "suspicious_value": float(suspicious_value)
    }

def log_audit_event(
    db: Session,
    client_id: str,
    event_type: str,
    event_details: Dict[str, Any],
    user_ip: str = None,
    success: bool = True
):
    """Registra evento de auditoria no banco"""
    audit_log = AuditLog(
        client_id=client_id,
        event_type=event_type,
        event_details=event_details,
        user_ip=user_ip,
        success=success
    )
    db.add(audit_log)
    db.commit()

def cleanup_old_data(db: Session, retention_days: int = 90):
    """Remove dados antigos baseado na política de retenção"""
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    # Remove duplicatas antigas
    db.query(Duplicata).filter(Duplicata.created_at < cutoff_date).delete()
    
    # Remove logs de auditoria antigos
    db.query(AuditLog).filter(AuditLog.created_at < cutoff_date).delete()
    
    # Remove lotes de processamento antigos
    db.query(ProcessingBatch).filter(ProcessingBatch.created_at < cutoff_date).delete()
    
    db.commit()

# Inicializar banco de dados
if __name__ == "__main__":
    create_tables()
    print("Tabelas criadas com sucesso!")