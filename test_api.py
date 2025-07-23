#!/usr/bin/env python3
"""
Script de teste para a API de Detecção de Fraude
Demonstra o uso completo da plataforma via API
"""

import requests
import json
import pandas as pd
import time
from datetime import datetime

# Configuração
API_BASE_URL = "http://localhost:8000"
CLIENT_ID = "test_client_001"

def test_authentication():
    """Testa autenticação"""
    print("🔐 Testando autenticação...")
    
    response = requests.post(f"{API_BASE_URL}/auth/login", params={"client_id": CLIENT_ID})
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Autenticação bem-sucedida! Token: {token[:50]}...")
        return token
    else:
        print(f"❌ Falha na autenticação: {response.status_code}")
        return None

def test_upload(token):
    """Testa upload de arquivo"""
    print("\n📤 Testando upload de arquivo...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Usar arquivo de exemplo
    with open("sample_data.csv", "rb") as file:
        files = {"file": ("sample_data.csv", file, "text/csv")}
        response = requests.post(f"{API_BASE_URL}/upload", files=files, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload bem-sucedido!")
        print(f"   - Total de registros: {result['total_records']}")
        print(f"   - Registros suspeitos: {result['suspicious_count']}")
        print(f"   - Tempo de processamento: {result['processing_time']:.2f}s")
        return True
    else:
        print(f"❌ Falha no upload: {response.status_code}")
        print(f"   Erro: {response.text}")
        return False

def test_get_duplicatas(token):
    """Testa consulta de duplicatas"""
    print("\n📋 Testando consulta de duplicatas...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Buscar todas as duplicatas
    response = requests.get(f"{API_BASE_URL}/duplicatas", headers=headers)
    
    if response.status_code == 200:
        duplicatas = response.json()
        print(f"✅ Consulta bem-sucedida! {len(duplicatas)} duplicatas encontradas")
        
        # Mostrar algumas duplicatas suspeitas
        suspeitas = [d for d in duplicatas if d["is_suspicious"]]
        print(f"   - Duplicatas suspeitas: {len(suspeitas)}")
        
        if suspeitas:
            print("   - Exemplos de duplicatas suspeitas:")
            for dup in suspeitas[:3]:
                print(f"     * {dup['id_duplicata']}: {', '.join(dup['fraud_reasons'])}")
        
        return duplicatas
    else:
        print(f"❌ Falha na consulta: {response.status_code}")
        return []

def test_stats(token):
    """Testa consulta de estatísticas"""
    print("\n📊 Testando consulta de estatísticas...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/stats", headers=headers)
    
    if response.status_code == 200:
        stats = response.json()
        print("✅ Estatísticas obtidas:")
        print(f"   - Total de duplicatas: {stats['total_duplicatas']}")
        print(f"   - Duplicatas suspeitas: {stats['suspicious_count']} ({stats['suspicious_percentage']:.1f}%)")
        print(f"   - Sem documento fiscal: {stats['without_fiscal_doc']}")
        print(f"   - Score médio de risco: {stats['avg_risk_score']:.2f}")
        return stats
    else:
        print(f"❌ Falha na consulta de stats: {response.status_code}")
        return {}

def test_risk_config(token):
    """Testa configuração de apetite de risco"""
    print("\n⚙️ Testando configuração de apetite de risco...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Testar diferentes configurações
    configs = [
        {"sensitivity": "low", "enable_ml_detection": True},
        {"sensitivity": "medium", "enable_ml_detection": True},
        {"sensitivity": "high", "enable_ml_detection": True}
    ]
    
    for config in configs:
        print(f"\n   Testando configuração: {config['sensitivity']}")
        
        # Atualizar configuração
        response = requests.post(
            f"{API_BASE_URL}/config/risk-appetite",
            json=config,
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"   ✅ Configuração {config['sensitivity']} aplicada")
            
            # Verificar se foi aplicada
            response = requests.get(f"{API_BASE_URL}/config/risk-appetite", headers=headers)
            if response.status_code == 200:
                current_config = response.json()
                print(f"   📋 Configuração atual: {current_config['sensitivity']}")
        else:
            print(f"   ❌ Falha ao aplicar configuração: {response.status_code}")

def test_suspicious_only(token):
    """Testa filtro de duplicatas suspeitas"""
    print("\n🚨 Testando filtro de duplicatas suspeitas...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE_URL}/duplicatas",
        params={"suspicious_only": True},
        headers=headers
    )
    
    if response.status_code == 200:
        suspeitas = response.json()
        print(f"✅ Filtro aplicado! {len(suspeitas)} duplicatas suspeitas")
        
        if suspeitas:
            print("   Detalhes das duplicatas suspeitas:")
            for dup in suspeitas:
                print(f"   - {dup['id_duplicata']}: R$ {dup['valor']:,.2f}")
                print(f"     Motivos: {', '.join(dup['fraud_reasons'])}")
                print(f"     Score de risco: {dup['risk_score']:.2f}")
                print()
    else:
        print(f"❌ Falha no filtro: {response.status_code}")

def main():
    """Executa todos os testes"""
    print("🧪 TESTE COMPLETO DA API DE DETECÇÃO DE FRAUDE")
    print("=" * 50)
    
    # Verificar se API está rodando
    try:
        response = requests.get(f"{API_BASE_URL}/docs")
        if response.status_code != 200:
            print("❌ API não está rodando. Execute: uvicorn backend.main:app --reload")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar à API. Verifique se está rodando em http://localhost:8000")
        return
    
    # Executar testes
    token = test_authentication()
    if not token:
        return
    
    if test_upload(token):
        test_get_duplicatas(token)
        test_stats(token)
        test_risk_config(token)
        test_suspicious_only(token)
    
    print("\n🎉 Testes concluídos!")
    print("\n📖 Para usar o dashboard web, acesse: http://localhost:8501")
    print("📚 Para ver a documentação da API, acesse: http://localhost:8000/docs")

if __name__ == "__main__":
    main()