"""
Testes automatizados para o sistema de detecção de fraude
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Adicionar o diretório backend ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.ml_service import FraudDetectionML
from backend.main import detect_fraud_simple, DuplicataBase

class TestFraudDetection:
    """Testes para detecção de fraude"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.ml_service = FraudDetectionML()
        
        # Dados de teste
        self.sample_data = pd.DataFrame({
            'id_duplicata': ['DUP001', 'DUP002', 'DUP003', 'DUP004', 'DUP005'],
            'sacador': ['Empresa A', 'Empresa B', 'Empresa C', 'Empresa A', 'Empresa D'],
            'sacado': ['Cliente X', 'Cliente Y', 'Cliente Z', 'Cliente W', 'Cliente V'],
            'valor': [10000.0, 2000000.0, 50.0, 15000.0, 100000.0],
            'data_emissao': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19'],
            'data_vencimento': ['2024-02-15', '2024-01-18', '2024-02-17', '2024-02-18', '2024-01-20'],
            'tipo_documento': ['Duplicata', 'Duplicata', 'Duplicata', 'Duplicata', 'Duplicata'],
            'documento_fiscal_vinculado': [True, False, True, True, False],
            'status': ['Ativo', 'Ativo', 'Ativo', 'Ativo', 'Ativo']
        })
    
    def test_simple_fraud_detection_no_fiscal_doc(self):
        """Testa detecção de fraude por falta de documento fiscal"""
        duplicata = DuplicataBase(
            id_duplicata="DUP001",
            sacador="Empresa A",
            sacado="Cliente X",
            valor=10000.0,
            data_emissao="2024-01-15",
            data_vencimento="2024-02-15",
            tipo_documento="Duplicata",
            documento_fiscal_vinculado=False,
            status="Ativo"
        )
        
        is_suspicious, reasons = detect_fraud_simple(duplicata)
        
        assert is_suspicious == True
        assert "Sem documento fiscal vinculado" in reasons
    
    def test_simple_fraud_detection_high_value(self):
        """Testa detecção de fraude por valor alto"""
        duplicata = DuplicataBase(
            id_duplicata="DUP002",
            sacador="Empresa B",
            sacado="Cliente Y",
            valor=2000000.0,
            data_emissao="2024-01-16",
            data_vencimento="2024-02-16",
            tipo_documento="Duplicata",
            documento_fiscal_vinculado=True,
            status="Ativo"
        )
        
        is_suspicious, reasons = detect_fraud_simple(duplicata)
        
        assert is_suspicious == True
        assert "Valor muito alto (acima de R$ 1M)" in reasons
    
    def test_simple_fraud_detection_low_value(self):
        """Testa detecção de fraude por valor baixo"""
        duplicata = DuplicataBase(
            id_duplicata="DUP003",
            sacador="Empresa C",
            sacado="Cliente Z",
            valor=50.0,
            data_emissao="2024-01-17",
            data_vencimento="2024-02-17",
            tipo_documento="Duplicata",
            documento_fiscal_vinculado=True,
            status="Ativo"
        )
        
        is_suspicious, reasons = detect_fraud_simple(duplicata)
        
        assert is_suspicious == True
        assert "Valor muito baixo (possível transação de teste)" in reasons
    
    def test_simple_fraud_detection_short_term(self):
        """Testa detecção de fraude por prazo muito curto"""
        duplicata = DuplicataBase(
            id_duplicata="DUP004",
            sacador="Empresa D",
            sacado="Cliente W",
            valor=100000.0,
            data_emissao="2024-01-16",
            data_vencimento="2024-01-18",
            tipo_documento="Duplicata",
            documento_fiscal_vinculado=True,
            status="Ativo"
        )
        
        is_suspicious, reasons = detect_fraud_simple(duplicata)
        
        assert is_suspicious == True
        assert "Prazo de vencimento muito curto (< 7 dias)" in reasons
    
    def test_simple_fraud_detection_safe_case(self):
        """Testa caso seguro (sem fraude)"""
        duplicata = DuplicataBase(
            id_duplicata="DUP005",
            sacador="Empresa E",
            sacado="Cliente V",
            valor=15000.0,
            data_emissao="2024-01-15",
            data_vencimento="2024-02-15",
            tipo_documento="Duplicata",
            documento_fiscal_vinculado=True,
            status="Ativo"
        )
        
        is_suspicious, reasons = detect_fraud_simple(duplicata)
        
        assert is_suspicious == False
        assert len(reasons) == 0
    
    def test_feature_engineering(self):
        """Testa engenharia de features"""
        df_features = self.ml_service.engineer_features(self.sample_data)
        
        # Verificar se as features foram criadas
        expected_features = [
            'data_emissao_dt', 'data_vencimento_dt', 'days_to_maturity',
            'is_weekend_emission', 'emission_hour', 'emission_month', 'is_month_end',
            'valor_log', 'valor_zscore', 'sacador_frequency', 'sacado_frequency'
        ]
        
        for feature in expected_features:
            assert feature in df_features.columns, f"Feature {feature} não foi criada"
        
        # Verificar se os valores fazem sentido
        assert df_features['valor_log'].min() >= 0
        assert df_features['days_to_maturity'].dtype in ['int64', 'int32']
        assert df_features['is_weekend_emission'].dtype == bool
    
    def test_ml_model_training(self):
        """Testa treinamento do modelo ML"""
        client_id = "test_client"
        
        # Treinar modelo Isolation Forest
        success = self.ml_service.train_isolation_forest(
            self.sample_data, 
            client_id, 
            contamination=0.2
        )
        
        assert success == True
        assert f"{client_id}_isolation" in self.ml_service.models
        
        model_info = self.ml_service.models[f"{client_id}_isolation"]
        assert model_info['type'] == 'isolation_forest'
        assert model_info['contamination'] == 0.2
        assert model_info['n_samples'] == len(self.sample_data)
    
    def test_ml_predictions(self):
        """Testa predições do modelo ML"""
        client_id = "test_client"
        
        # Treinar modelo primeiro
        self.ml_service.train_isolation_forest(self.sample_data, client_id)
        
        # Fazer predições
        predictions = self.ml_service.predict_anomalies(
            self.sample_data, 
            client_id, 
            model_type='isolation'
        )
        
        assert len(predictions) == len(self.sample_data)
        
        for is_anomaly, score in predictions:
            assert isinstance(is_anomaly, bool)
            assert isinstance(score, float)
            assert 0 <= score <= 1
    
    def test_data_validation(self):
        """Testa validação de dados"""
        # Dados inválidos - valor negativo
        invalid_data = self.sample_data.copy()
        invalid_data.loc[0, 'valor'] = -1000
        
        # Dados inválidos - data futura demais
        invalid_data.loc[1, 'data_vencimento'] = '2030-01-01'
        
        # Em uma implementação real, haveria validação que rejeitaria esses dados
        # Por enquanto, apenas verificamos se os dados são processados
        df_features = self.ml_service.engineer_features(invalid_data)
        assert len(df_features) == len(invalid_data)

class TestMLService:
    """Testes específicos para o serviço de ML"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.ml_service = FraudDetectionML()
        
        # Criar dataset maior para testes de ML
        np.random.seed(42)
        n_samples = 100
        
        self.large_dataset = pd.DataFrame({
            'id_duplicata': [f'DUP{i:03d}' for i in range(n_samples)],
            'sacador': np.random.choice(['Empresa A', 'Empresa B', 'Empresa C', 'Empresa D'], n_samples),
            'sacado': np.random.choice(['Cliente X', 'Cliente Y', 'Cliente Z', 'Cliente W'], n_samples),
            'valor': np.random.lognormal(mean=10, sigma=1, size=n_samples),
            'data_emissao': pd.date_range('2024-01-01', periods=n_samples, freq='D').strftime('%Y-%m-%d'),
            'data_vencimento': (pd.date_range('2024-01-01', periods=n_samples, freq='D') + 
                              pd.to_timedelta(np.random.randint(1, 365, n_samples), unit='D')).strftime('%Y-%m-%d'),
            'tipo_documento': ['Duplicata'] * n_samples,
            'documento_fiscal_vinculado': np.random.choice([True, False], n_samples, p=[0.8, 0.2]),
            'status': ['Ativo'] * n_samples
        })
    
    def test_isolation_forest_training(self):
        """Testa treinamento do Isolation Forest"""
        client_id = "test_ml_client"
        
        success = self.ml_service.train_isolation_forest(
            self.large_dataset, 
            client_id, 
            contamination=0.1
        )
        
        assert success == True
        
        # Verificar se o modelo foi salvo corretamente
        model_key = f"{client_id}_isolation"
        assert model_key in self.ml_service.models
        
        model_info = self.ml_service.models[model_key]
        assert model_info['contamination'] == 0.1
        assert model_info['n_samples'] == len(self.large_dataset)
    
    def test_lof_training(self):
        """Testa treinamento do Local Outlier Factor"""
        client_id = "test_lof_client"
        
        success = self.ml_service.train_lof(
            self.large_dataset, 
            client_id, 
            contamination=0.15
        )
        
        assert success == True
        
        # Verificar se o modelo foi salvo corretamente
        model_key = f"{client_id}_lof"
        assert model_key in self.ml_service.models
        
        model_info = self.ml_service.models[model_key]
        assert model_info['contamination'] == 0.15
    
    def test_feature_importance(self):
        """Testa cálculo de importância das features"""
        client_id = "test_importance_client"
        
        # Treinar modelo
        self.ml_service.train_isolation_forest(self.large_dataset, client_id)
        
        # Obter importância das features
        importance = self.ml_service.get_feature_importance(client_id, 'isolation')
        
        assert isinstance(importance, dict)
        assert len(importance) > 0
        
        # Verificar se os valores estão no range esperado
        for feature, value in importance.items():
            assert isinstance(value, float)
            assert value >= 0

class TestPerformance:
    """Testes de performance"""
    
    def test_processing_time(self):
        """Testa tempo de processamento"""
        import time
        
        # Criar dataset grande
        n_samples = 1000
        large_data = pd.DataFrame({
            'id_duplicata': [f'DUP{i:04d}' for i in range(n_samples)],
            'sacador': np.random.choice(['Empresa A', 'Empresa B', 'Empresa C'], n_samples),
            'sacado': np.random.choice(['Cliente X', 'Cliente Y', 'Cliente Z'], n_samples),
            'valor': np.random.lognormal(mean=10, sigma=1, size=n_samples),
            'data_emissao': pd.date_range('2024-01-01', periods=n_samples, freq='H').strftime('%Y-%m-%d'),
            'data_vencimento': (pd.date_range('2024-01-01', periods=n_samples, freq='H') + 
                              pd.to_timedelta(np.random.randint(1, 365, n_samples), unit='D')).strftime('%Y-%m-%d'),
            'tipo_documento': ['Duplicata'] * n_samples,
            'documento_fiscal_vinculado': np.random.choice([True, False], n_samples),
            'status': ['Ativo'] * n_samples
        })
        
        ml_service = FraudDetectionML()
        
        # Medir tempo de feature engineering
        start_time = time.time()
        df_features = ml_service.engineer_features(large_data)
        feature_time = time.time() - start_time
        
        # Deve processar 1000 registros em menos de 5 segundos
        assert feature_time < 5.0, f"Feature engineering muito lenta: {feature_time:.2f}s"
        
        # Medir tempo de treinamento
        start_time = time.time()
        success = ml_service.train_isolation_forest(large_data, "perf_test_client")
        training_time = time.time() - start_time
        
        assert success == True
        # Treinamento deve ser rápido para datasets pequenos
        assert training_time < 10.0, f"Treinamento muito lento: {training_time:.2f}s"

if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v"])