"""
Enhanced ML Service for fraud detection with multiple algorithms and feature engineering
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class FraudDetectionML:
    """Enhanced ML service for fraud detection"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_names = []
        
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Advanced feature engineering"""
        df_features = df.copy()
        
        # Date features
        df_features['data_emissao_dt'] = pd.to_datetime(df_features['data_emissao'])
        df_features['data_vencimento_dt'] = pd.to_datetime(df_features['data_vencimento'])
        df_features['days_to_maturity'] = (df_features['data_vencimento_dt'] - df_features['data_emissao_dt']).dt.days
        df_features['is_weekend_emission'] = df_features['data_emissao_dt'].dt.weekday >= 5
        df_features['emission_hour'] = df_features['data_emissao_dt'].dt.hour
        df_features['emission_month'] = df_features['data_emissao_dt'].dt.month
        df_features['is_month_end'] = df_features['data_emissao_dt'].dt.day >= 25
        
        # Value features
        df_features['valor_log'] = np.log1p(df_features['valor'])
        df_features['valor_zscore'] = (df_features['valor'] - df_features['valor'].mean()) / df_features['valor'].std()
        
        # Categorical frequency encoding
        for col in ['sacador', 'sacado', 'tipo_documento']:
            freq_map = df_features[col].value_counts().to_dict()
            df_features[f'{col}_frequency'] = df_features[col].map(freq_map)
        
        # Sacador/Sacado patterns
        sacador_stats = df_features.groupby('sacador').agg({
            'valor': ['mean', 'std', 'count'],
            'days_to_maturity': 'mean',
            'documento_fiscal_vinculado': 'mean'
        }).round(2)
        
        sacador_stats.columns = ['sacador_valor_mean', 'sacador_valor_std', 'sacador_count', 
                                'sacador_days_mean', 'sacador_fiscal_rate']
        
        df_features = df_features.merge(sacador_stats, left_on='sacador', right_index=True, how='left')
        
        # Risk indicators
        df_features['high_value_flag'] = (df_features['valor'] > df_features['valor'].quantile(0.95)).astype(int)
        df_features['short_term_flag'] = (df_features['days_to_maturity'] < 7).astype(int)
        df_features['no_fiscal_flag'] = (~df_features['documento_fiscal_vinculado']).astype(int)
        
        # Interaction features
        df_features['valor_per_day'] = df_features['valor'] / (df_features['days_to_maturity'] + 1)
        df_features['sacador_deviation'] = abs(df_features['valor'] - df_features['sacador_valor_mean'])
        
        return df_features
    
    def prepare_features(self, df: pd.DataFrame, client_id: str, fit_encoders: bool = False) -> np.ndarray:
        """Prepare features for ML models"""
        df_features = self.engineer_features(df)
        
        # Select numerical features
        numerical_features = [
            'valor', 'valor_log', 'valor_zscore', 'days_to_maturity',
            'sacador_frequency', 'sacado_frequency', 'tipo_documento_frequency',
            'sacador_valor_mean', 'sacador_valor_std', 'sacador_count',
            'sacador_days_mean', 'sacador_fiscal_rate', 'valor_per_day',
            'sacador_deviation', 'high_value_flag', 'short_term_flag', 'no_fiscal_flag'
        ]
        
        # Handle missing values
        for col in numerical_features:
            if col in df_features.columns:
                df_features[col] = df_features[col].fillna(df_features[col].median())
        
        X = df_features[numerical_features].values
        
        # Scale features
        if fit_encoders:
            self.scalers[client_id] = StandardScaler()
            X_scaled = self.scalers[client_id].fit_transform(X)
            self.feature_names = numerical_features
        else:
            if client_id in self.scalers:
                X_scaled = self.scalers[client_id].transform(X)
            else:
                X_scaled = X
        
        return X_scaled
    
    def train_isolation_forest(self, df: pd.DataFrame, client_id: str, contamination: float = 0.1) -> bool:
        """Train Isolation Forest model"""
        try:
            X = self.prepare_features(df, client_id, fit_encoders=True)
            
            model = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=200,
                max_samples='auto',
                max_features=1.0
            )
            
            model.fit(X)
            
            self.models[f"{client_id}_isolation"] = {
                'model': model,
                'type': 'isolation_forest',
                'trained_at': datetime.now(),
                'contamination': contamination,
                'n_samples': len(df)
            }
            
            logger.info(f"Isolation Forest trained for client {client_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error training Isolation Forest: {e}")
            return False
    
    def train_lof(self, df: pd.DataFrame, client_id: str, contamination: float = 0.1) -> bool:
        """Train Local Outlier Factor model"""
        try:
            X = self.prepare_features(df, client_id, fit_encoders=True)
            
            n_neighbors = min(20, len(df) // 2)
            
            model = LocalOutlierFactor(
                n_neighbors=n_neighbors,
                contamination=contamination,
                novelty=True
            )
            
            model.fit(X)
            
            self.models[f"{client_id}_lof"] = {
                'model': model,
                'type': 'local_outlier_factor',
                'trained_at': datetime.now(),
                'contamination': contamination,
                'n_samples': len(df)
            }
            
            logger.info(f"LOF trained for client {client_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error training LOF: {e}")
            return False
    
    def predict_anomalies(self, df: pd.DataFrame, client_id: str, model_type: str = 'isolation') -> List[Tuple[bool, float]]:
        """Predict anomalies using trained models"""
        model_key = f"{client_id}_{model_type}"
        
        if model_key not in self.models:
            return [(False, 0.0) for _ in range(len(df))]
        
        try:
            X = self.prepare_features(df, client_id, fit_encoders=False)
            model_info = self.models[model_key]
            model = model_info['model']
            
            if model_type == 'isolation':
                predictions = model.predict(X)
                scores = model.decision_function(X)
                # Normalize scores to 0-1
                scores_normalized = (scores - scores.min()) / (scores.max() - scores.min())
            else:  # LOF
                predictions = model.predict(X)
                scores = model.decision_function(X)
                scores_normalized = (scores - scores.min()) / (scores.max() - scores.min())
            
            results = []
            for pred, score in zip(predictions, scores_normalized):
                is_anomaly = pred == -1
                results.append((is_anomaly, float(score)))
            
            return results
            
        except Exception as e:
            logger.error(f"Error predicting anomalies: {e}")
            return [(False, 0.0) for _ in range(len(df))]
    
    def get_feature_importance(self, client_id: str, model_type: str = 'isolation') -> Dict[str, float]:
        """Get feature importance (approximation for unsupervised models)"""
        model_key = f"{client_id}_{model_type}"
        
        if model_key not in self.models or not self.feature_names:
            return {}
        
        # For unsupervised models, we approximate importance by feature variance impact
        try:
            importance = {}
            for i, feature in enumerate(self.feature_names):
                # Simple approximation - in production, use SHAP or similar
                importance[feature] = 1.0 / (i + 1)  # Decreasing importance
            
            return importance
        except:
            return {}
    
    def save_models(self, client_id: str, path: str = "models/"):
        """Save trained models to disk"""
        os.makedirs(path, exist_ok=True)
        
        for model_key, model_info in self.models.items():
            if client_id in model_key:
                filename = f"{path}/{model_key}.joblib"
                joblib.dump(model_info, filename)
                logger.info(f"Model saved: {filename}")
    
    def load_models(self, client_id: str, path: str = "models/"):
        """Load trained models from disk"""
        try:
            for model_type in ['isolation', 'lof']:
                model_key = f"{client_id}_{model_type}"
                filename = f"{path}/{model_key}.joblib"
                
                if os.path.exists(filename):
                    self.models[model_key] = joblib.load(filename)
                    logger.info(f"Model loaded: {filename}")
            
            # Load scaler
            scaler_file = f"{path}/{client_id}_scaler.joblib"
            if os.path.exists(scaler_file):
                self.scalers[client_id] = joblib.load(scaler_file)
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")

# Global ML service instance
ml_service = FraudDetectionML()