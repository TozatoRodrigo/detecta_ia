from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
import json
import io
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Fraud Detection Platform API",
    description="API para detecção de fraude em duplicatas escriturais",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")

# Models
class DuplicataBase(BaseModel):
    id_duplicata: str
    sacador: str
    sacado: str
    valor: float
    data_emissao: str
    data_vencimento: str
    tipo_documento: str
    documento_fiscal_vinculado: bool
    status: str

class DuplicataResponse(DuplicataBase):
    is_suspicious: bool
    fraud_reasons: List[str]
    risk_score: float

class RiskAppetiteConfig(BaseModel):
    sensitivity: str  # "low", "medium", "high"
    threshold: Optional[float] = None
    enable_ml_detection: bool = True

class UploadResponse(BaseModel):
    message: str
    total_records: int
    suspicious_count: int
    processing_time: float

# In-memory storage (replace with database in production)
duplicatas_db: Dict[str, List[DuplicataResponse]] = {}
client_configs: Dict[str, RiskAppetiteConfig] = {}

# ML Models storage
ml_models: Dict[str, Any] = {}

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and extract client_id"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        client_id = payload.get("client_id")
        if not client_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return client_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def create_token(client_id: str) -> str:
    """Create JWT token for client"""
    payload = {
        "client_id": client_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def detect_fraud_simple(duplicata: DuplicataBase) -> tuple[bool, List[str]]:
    """Enhanced rule-based fraud detection"""
    reasons = []
    is_suspicious = False
    
    # Rule 1: No fiscal document
    if not duplicata.documento_fiscal_vinculado:
        reasons.append("Sem documento fiscal vinculado")
        is_suspicious = True
    
    # Rule 2: Very high values (above 1M)
    if duplicata.valor > 1000000:
        reasons.append("Valor muito alto (acima de R$ 1M)")
        is_suspicious = True
    
    # Rule 3: Very short payment term (less than 7 days)
    try:
        emissao = datetime.strptime(duplicata.data_emissao, "%Y-%m-%d")
        vencimento = datetime.strptime(duplicata.data_vencimento, "%Y-%m-%d")
        days_diff = (vencimento - emissao).days
        
        if days_diff < 7:
            reasons.append("Prazo de vencimento muito curto (< 7 dias)")
            is_suspicious = True
        elif days_diff > 365:
            reasons.append("Prazo de vencimento muito longo (> 1 ano)")
            is_suspicious = True
    except:
        reasons.append("Datas inválidas ou inconsistentes")
        is_suspicious = True
    
    # Rule 4: Weekend emission pattern (higher risk)
    try:
        emissao = datetime.strptime(duplicata.data_emissao, "%Y-%m-%d")
        if emissao.weekday() >= 5:  # Saturday or Sunday
            reasons.append("Emissão em final de semana")
            is_suspicious = True
    except:
        pass
    
    # Rule 5: Very low values (possible test transactions)
    if duplicata.valor < 100:
        reasons.append("Valor muito baixo (possível transação de teste)")
        is_suspicious = True
    
    # Rule 6: Round numbers (often suspicious)
    if duplicata.valor % 1000 == 0 and duplicata.valor >= 10000:
        reasons.append("Valor em números redondos (padrão suspeito)")
        is_suspicious = True
    
    return is_suspicious, reasons

def train_ml_model(df: pd.DataFrame, client_id: str, sensitivity: str = "medium"):
    """Train ML model for anomaly detection"""
    try:
        # Prepare features
        features = []
        
        # Numerical features
        features.append(df['valor'].values.reshape(-1, 1))
        
        # Date features
        df['data_emissao_dt'] = pd.to_datetime(df['data_emissao'])
        df['data_vencimento_dt'] = pd.to_datetime(df['data_vencimento'])
        df['days_to_maturity'] = (df['data_vencimento_dt'] - df['data_emissao_dt']).dt.days
        features.append(df['days_to_maturity'].values.reshape(-1, 1))
        
        # Categorical features (encoded)
        df['sacador_encoded'] = pd.Categorical(df['sacador']).codes
        df['sacado_encoded'] = pd.Categorical(df['sacado']).codes
        features.append(df['sacador_encoded'].values.reshape(-1, 1))
        features.append(df['sacado_encoded'].values.reshape(-1, 1))
        
        # Combine features
        X = np.hstack(features)
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Set contamination based on sensitivity
        contamination_map = {
            "low": 0.05,
            "medium": 0.1,
            "high": 0.2
        }
        contamination = contamination_map.get(sensitivity, 0.1)
        
        # Train Isolation Forest
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        iso_forest.fit(X_scaled)
        
        # Store model and scaler
        ml_models[client_id] = {
            "model": iso_forest,
            "scaler": scaler,
            "feature_names": ["valor", "days_to_maturity", "sacador_encoded", "sacado_encoded"]
        }
        
        return True
    except Exception as e:
        print(f"Error training ML model: {e}")
        return False

def predict_ml_anomalies(df: pd.DataFrame, client_id: str) -> List[tuple[bool, float]]:
    """Predict anomalies using trained ML model"""
    if client_id not in ml_models:
        return [(False, 0.0) for _ in range(len(df))]
    
    try:
        model_data = ml_models[client_id]
        model = model_data["model"]
        scaler = model_data["scaler"]
        
        # Prepare features (same as training)
        features = []
        features.append(df['valor'].values.reshape(-1, 1))
        
        df['data_emissao_dt'] = pd.to_datetime(df['data_emissao'])
        df['data_vencimento_dt'] = pd.to_datetime(df['data_vencimento'])
        df['days_to_maturity'] = (df['data_vencimento_dt'] - df['data_emissao_dt']).dt.days
        features.append(df['days_to_maturity'].values.reshape(-1, 1))
        
        df['sacador_encoded'] = pd.Categorical(df['sacador']).codes
        df['sacado_encoded'] = pd.Categorical(df['sacado']).codes
        features.append(df['sacador_encoded'].values.reshape(-1, 1))
        features.append(df['sacado_encoded'].values.reshape(-1, 1))
        
        X = np.hstack(features)
        X_scaled = scaler.transform(X)
        
        # Predict
        predictions = model.predict(X_scaled)
        scores = model.decision_function(X_scaled)
        
        # Convert to boolean and normalize scores
        results = []
        for pred, score in zip(predictions, scores):
            is_anomaly = pred == -1
            normalized_score = max(0, min(1, (score + 0.5) * 2))  # Normalize to 0-1
            results.append((is_anomaly, normalized_score))
        
        return results
    except Exception as e:
        print(f"Error predicting anomalies: {e}")
        return [(False, 0.0) for _ in range(len(df))]

@app.post("/auth/login")
async def login(client_id: str):
    """Generate authentication token for client"""
    token = create_token(client_id)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/upload", response_model=UploadResponse)
async def upload_duplicatas(
    file: UploadFile = File(...),
    client_id: str = Depends(verify_token)
):
    """Upload and process duplicatas file"""
    start_time = datetime.now()
    
    try:
        # Read file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Validate required columns
        required_cols = [
            'id_duplicata', 'sacador', 'sacado', 'valor',
            'data_emissao', 'data_vencimento', 'tipo_documento',
            'documento_fiscal_vinculado', 'status'
        ]
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing_cols}"
            )
        
        # Get client config
        config = client_configs.get(client_id, RiskAppetiteConfig(sensitivity="medium"))
        
        # Train ML model if enabled
        if config.enable_ml_detection:
            train_ml_model(df, client_id, config.sensitivity)
        
        # Get ML predictions
        ml_predictions = predict_ml_anomalies(df, client_id) if config.enable_ml_detection else []
        
        # Process each duplicata
        processed_duplicatas = []
        suspicious_count = 0
        
        for idx, row in df.iterrows():
            duplicata = DuplicataBase(**row.to_dict())
            
            # Simple fraud detection
            is_suspicious_simple, simple_reasons = detect_fraud_simple(duplicata)
            
            # ML fraud detection
            ml_suspicious = False
            ml_score = 0.0
            ml_reasons = []
            
            if config.enable_ml_detection and idx < len(ml_predictions):
                ml_suspicious, ml_score = ml_predictions[idx]
                if ml_suspicious:
                    ml_reasons.append("Padrão atípico detectado por IA")
            
            # Combine results
            all_reasons = simple_reasons + ml_reasons
            is_suspicious = is_suspicious_simple or ml_suspicious
            risk_score = max(0.8 if is_suspicious_simple else 0.0, ml_score)
            
            if is_suspicious:
                suspicious_count += 1
            
            processed_duplicata = DuplicataResponse(
                **duplicata.dict(),
                is_suspicious=is_suspicious,
                fraud_reasons=all_reasons,
                risk_score=risk_score
            )
            processed_duplicatas.append(processed_duplicata)
        
        # Store in database
        duplicatas_db[client_id] = processed_duplicatas
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return UploadResponse(
            message="Arquivo processado com sucesso",
            total_records=len(processed_duplicatas),
            suspicious_count=suspicious_count,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/duplicatas", response_model=List[DuplicataResponse])
async def get_duplicatas(
    suspicious_only: bool = False,
    client_id: str = Depends(verify_token)
):
    """Get duplicatas for client"""
    if client_id not in duplicatas_db:
        return []
    
    duplicatas = duplicatas_db[client_id]
    
    if suspicious_only:
        duplicatas = [d for d in duplicatas if d.is_suspicious]
    
    return duplicatas

@app.get("/stats")
async def get_stats(client_id: str = Depends(verify_token)):
    """Get comprehensive statistics for client"""
    if client_id not in duplicatas_db:
        return {
            "total_duplicatas": 0,
            "suspicious_count": 0,
            "suspicious_percentage": 0,
            "without_fiscal_doc": 0,
            "avg_risk_score": 0,
            "total_value": 0,
            "suspicious_value": 0,
            "top_risk_reasons": [],
            "sacador_stats": {},
            "value_distribution": {}
        }
    
    duplicatas = duplicatas_db[client_id]
    suspicious = [d for d in duplicatas if d.is_suspicious]
    without_fiscal = [d for d in duplicatas if not d.documento_fiscal_vinculado]
    
    # Calculate value statistics
    total_value = sum(d.valor for d in duplicatas)
    suspicious_value = sum(d.valor for d in suspicious)
    
    # Top risk reasons
    all_reasons = []
    for d in suspicious:
        all_reasons.extend(d.fraud_reasons)
    
    from collections import Counter
    reason_counts = Counter(all_reasons)
    top_reasons = [{"reason": reason, "count": count} for reason, count in reason_counts.most_common(5)]
    
    # Sacador statistics
    sacador_stats = {}
    df = pd.DataFrame([d.dict() for d in duplicatas])
    if not df.empty:
        sacador_groups = df.groupby('sacador').agg({
            'is_suspicious': ['count', 'sum'],
            'valor': 'sum',
            'risk_score': 'mean'
        }).round(2)
        
        for sacador in sacador_groups.index[:5]:  # Top 5
            total_count = sacador_groups.loc[sacador, ('is_suspicious', 'count')]
            suspicious_count = sacador_groups.loc[sacador, ('is_suspicious', 'sum')]
            total_value = sacador_groups.loc[sacador, ('valor', 'sum')]
            avg_risk = sacador_groups.loc[sacador, ('risk_score', 'mean')]
            
            sacador_stats[sacador] = {
                "total_duplicatas": int(total_count),
                "suspicious_count": int(suspicious_count),
                "suspicious_rate": round((suspicious_count / total_count) * 100, 1),
                "total_value": float(total_value),
                "avg_risk_score": float(avg_risk)
            }
    
    # Value distribution
    values = [d.valor for d in duplicatas]
    value_distribution = {
        "min": min(values) if values else 0,
        "max": max(values) if values else 0,
        "median": float(np.median(values)) if values else 0,
        "q25": float(np.percentile(values, 25)) if values else 0,
        "q75": float(np.percentile(values, 75)) if values else 0
    }
    
    return {
        "total_duplicatas": len(duplicatas),
        "suspicious_count": len(suspicious),
        "suspicious_percentage": (len(suspicious) / len(duplicatas)) * 100 if duplicatas else 0,
        "without_fiscal_doc": len(without_fiscal),
        "avg_risk_score": float(np.mean([d.risk_score for d in duplicatas])) if duplicatas else 0,
        "total_value": total_value,
        "suspicious_value": suspicious_value,
        "suspicious_value_percentage": (suspicious_value / total_value) * 100 if total_value > 0 else 0,
        "top_risk_reasons": top_reasons,
        "sacador_stats": sacador_stats,
        "value_distribution": value_distribution
    }

@app.post("/config/risk-appetite")
async def update_risk_appetite(
    config: RiskAppetiteConfig,
    client_id: str = Depends(verify_token)
):
    """Update risk appetite configuration"""
    client_configs[client_id] = config
    
    # Reprocess existing data if available
    if client_id in duplicatas_db:
        # This would trigger reprocessing with new config
        # For now, just store the config
        pass
    
    return {"message": "Configuração atualizada com sucesso"}

@app.get("/config/risk-appetite")
async def get_risk_appetite(client_id: str = Depends(verify_token)):
    """Get current risk appetite configuration"""
    return client_configs.get(client_id, RiskAppetiteConfig(sensitivity="medium"))

@app.get("/export/report")
async def export_report(
    format: str = "csv",
    suspicious_only: bool = False,
    client_id: str = Depends(verify_token)
):
    """Export duplicatas report in CSV or JSON format"""
    if client_id not in duplicatas_db:
        raise HTTPException(status_code=404, detail="No data found for client")
    
    duplicatas = duplicatas_db[client_id]
    
    if suspicious_only:
        duplicatas = [d for d in duplicatas if d.is_suspicious]
    
    if format.lower() == "json":
        return {"data": duplicatas, "total_records": len(duplicatas)}
    
    # CSV format
    df = pd.DataFrame([d.dict() for d in duplicatas])
    
    # Format for better readability
    df['fraud_reasons'] = df['fraud_reasons'].apply(lambda x: '; '.join(x) if x else '')
    df['valor'] = df['valor'].apply(lambda x: f"{x:.2f}")
    df['risk_score'] = df['risk_score'].apply(lambda x: f"{x:.3f}")
    
    csv_content = df.to_csv(index=False)
    
    from fastapi.responses import Response
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=duplicatas_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@app.get("/analytics/trends")
async def get_trends(client_id: str = Depends(verify_token)):
    """Get trend analysis for duplicatas"""
    if client_id not in duplicatas_db:
        return {"daily_trends": [], "monthly_trends": []}
    
    duplicatas = duplicatas_db[client_id]
    df = pd.DataFrame([d.dict() for d in duplicatas])
    
    if df.empty:
        return {"daily_trends": [], "monthly_trends": []}
    
    df['data_emissao_dt'] = pd.to_datetime(df['data_emissao'])
    
    # Daily trends
    daily_stats = df.groupby([df['data_emissao_dt'].dt.date, 'is_suspicious']).agg({
        'valor': ['count', 'sum'],
        'risk_score': 'mean'
    }).reset_index()
    
    daily_trends = []
    for _, row in daily_stats.iterrows():
        daily_trends.append({
            "date": row['data_emissao_dt'].strftime('%Y-%m-%d'),
            "is_suspicious": row['is_suspicious'],
            "count": int(row[('valor', 'count')]),
            "total_value": float(row[('valor', 'sum')]),
            "avg_risk_score": float(row[('risk_score', 'mean')])
        })
    
    # Monthly trends
    monthly_stats = df.groupby([df['data_emissao_dt'].dt.to_period('M'), 'is_suspicious']).agg({
        'valor': ['count', 'sum'],
        'risk_score': 'mean'
    }).reset_index()
    
    monthly_trends = []
    for _, row in monthly_stats.iterrows():
        monthly_trends.append({
            "month": str(row['data_emissao_dt']),
            "is_suspicious": row['is_suspicious'],
            "count": int(row[('valor', 'count')]),
            "total_value": float(row[('valor', 'sum')]),
            "avg_risk_score": float(row[('risk_score', 'mean')])
        })
    
    return {
        "daily_trends": daily_trends,
        "monthly_trends": monthly_trends
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)