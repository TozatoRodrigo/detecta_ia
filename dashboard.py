import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import io

# Page config
st.set_page_config(
    page_title="Fraud Detection Platform",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
    }
    .suspicious-badge {
        background-color: #ff6b6b;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
    }
    .safe-badge {
        background-color: #51cf66;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Session state initialization
if 'token' not in st.session_state:
    st.session_state.token = None
if 'client_id' not in st.session_state:
    st.session_state.client_id = None
if 'duplicatas' not in st.session_state:
    st.session_state.duplicatas = []

def authenticate(client_id: str):
    """Authenticate with API"""
    try:
        response = requests.post(f"{API_BASE_URL}/auth/login", params={"client_id": client_id})
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]
            st.session_state.client_id = client_id
            return True
        return False
    except:
        return False

def get_headers():
    """Get authorization headers"""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

def upload_file(file_content, filename):
    """Upload file to API"""
    try:
        files = {"file": (filename, file_content, "text/csv")}
        response = requests.post(
            f"{API_BASE_URL}/upload",
            files=files,
            headers=get_headers()
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Erro no upload: {e}")
        return None

def get_duplicatas(suspicious_only=False):
    """Get duplicatas from API"""
    try:
        params = {"suspicious_only": suspicious_only}
        response = requests.get(
            f"{API_BASE_URL}/duplicatas",
            params=params,
            headers=get_headers()
        )
        return response.json() if response.status_code == 200 else []
    except:
        return []

def get_stats():
    """Get statistics from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", headers=get_headers())
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

def update_risk_appetite(sensitivity, enable_ml):
    """Update risk appetite configuration"""
    try:
        config = {
            "sensitivity": sensitivity,
            "enable_ml_detection": enable_ml
        }
        response = requests.post(
            f"{API_BASE_URL}/config/risk-appetite",
            json=config,
            headers=get_headers()
        )
        return response.status_code == 200
    except:
        return False

# Main app
def main():
    st.title("🔍 Plataforma de Detecção de Fraude em Duplicatas")
    st.markdown("---")
    
    # Authentication
    if not st.session_state.token:
        st.sidebar.header("🔐 Autenticação")
        client_id = st.sidebar.text_input("Client ID", placeholder="Digite seu Client ID")
        
        if st.sidebar.button("Login"):
            if authenticate(client_id):
                st.sidebar.success("Autenticado com sucesso!")
                st.rerun()
            else:
                st.sidebar.error("Falha na autenticação")
        
        st.info("👈 Faça login na barra lateral para continuar")
        return
    
    # Sidebar
    st.sidebar.header(f"👤 Cliente: {st.session_state.client_id}")
    
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.client_id = None
        st.session_state.duplicatas = []
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Risk Appetite Configuration
    st.sidebar.header("⚙️ Configuração de Risco")
    
    sensitivity = st.sidebar.selectbox(
        "Sensibilidade do Modelo",
        ["low", "medium", "high"],
        index=1,
        format_func=lambda x: {"low": "Baixa", "medium": "Média", "high": "Alta"}[x]
    )
    
    enable_ml = st.sidebar.checkbox("Habilitar Detecção ML", value=True)
    
    if st.sidebar.button("Atualizar Configuração"):
        if update_risk_appetite(sensitivity, enable_ml):
            st.sidebar.success("Configuração atualizada!")
        else:
            st.sidebar.error("Erro ao atualizar configuração")
    
    st.sidebar.markdown("---")
    
    # File Upload
    st.sidebar.header("📁 Upload de Dados")
    uploaded_file = st.sidebar.file_uploader(
        "Escolha um arquivo CSV",
        type=['csv'],
        help="Arquivo deve conter as colunas: id_duplicata, sacador, sacado, valor, data_emissao, data_vencimento, tipo_documento, documento_fiscal_vinculado, status"
    )
    
    if uploaded_file is not None:
        if st.sidebar.button("Processar Arquivo"):
            with st.spinner("Processando arquivo..."):
                result = upload_file(uploaded_file.getvalue(), uploaded_file.name)
                if result:
                    st.success(f"✅ Arquivo processado: {result['total_records']} registros, {result['suspicious_count']} suspeitos")
                    st.session_state.duplicatas = get_duplicatas()
                else:
                    st.error("❌ Erro no processamento do arquivo")
    
    # Main content
    if not st.session_state.duplicatas:
        st.session_state.duplicatas = get_duplicatas()
    
    if not st.session_state.duplicatas:
        st.info("📤 Faça upload de um arquivo CSV para começar a análise")
        
        # Sample data format
        st.subheader("📋 Formato dos Dados")
        sample_data = pd.DataFrame({
            'id_duplicata': ['DUP001', 'DUP002', 'DUP003'],
            'sacador': ['Empresa A', 'Empresa B', 'Empresa C'],
            'sacado': ['Cliente X', 'Cliente Y', 'Cliente Z'],
            'valor': [10000.00, 50000.00, 25000.00],
            'data_emissao': ['2024-01-15', '2024-01-16', '2024-01-17'],
            'data_vencimento': ['2024-02-15', '2024-02-16', '2024-02-17'],
            'tipo_documento': ['Duplicata', 'Duplicata', 'Duplicata'],
            'documento_fiscal_vinculado': [True, False, True],
            'status': ['Ativo', 'Ativo', 'Ativo']
        })
        st.dataframe(sample_data, use_container_width=True)
        return
    
    # Statistics
    stats = get_stats()
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Duplicatas",
            f"{stats.get('total_duplicatas', 0):,}",
            help="Número total de duplicatas processadas"
        )
    
    with col2:
        st.metric(
            "Duplicatas Suspeitas",
            f"{stats.get('suspicious_count', 0):,}",
            f"{stats.get('suspicious_percentage', 0):.1f}%",
            help="Número e percentual de duplicatas flagadas como suspeitas"
        )
    
    with col3:
        st.metric(
            "Sem Documento Fiscal",
            f"{stats.get('without_fiscal_doc', 0):,}",
            help="Duplicatas emitidas sem documento fiscal vinculado"
        )
    
    with col4:
        st.metric(
            "Score Médio de Risco",
            f"{stats.get('avg_risk_score', 0):.2f}",
            help="Score médio de risco das duplicatas (0-1)"
        )
    
    st.markdown("---")
    
    # Charts
    df = pd.DataFrame(st.session_state.duplicatas)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribuição por Status")
        
        status_counts = df['is_suspicious'].value_counts()
        status_labels = ['Seguras', 'Suspeitas']
        colors = ['#51cf66', '#ff6b6b']
        
        fig_pie = px.pie(
            values=status_counts.values,
            names=status_labels,
            color_discrete_sequence=colors,
            title="Distribuição de Duplicatas"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.subheader("💰 Distribuição de Valores")
        
        fig_hist = px.histogram(
            df,
            x='valor',
            nbins=20,
            title="Distribuição de Valores das Duplicatas",
            color='is_suspicious',
            color_discrete_map={True: '#ff6b6b', False: '#51cf66'}
        )
        fig_hist.update_layout(xaxis_title="Valor (R$)", yaxis_title="Frequência")
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # Time series and advanced analytics
    if 'data_emissao' in df.columns:
        st.subheader("📈 Análises Temporais")
        
        df['data_emissao_dt'] = pd.to_datetime(df['data_emissao'])
        
        # Tabs for different time analyses
        tab1, tab2, tab3 = st.tabs(["Tendência Diária", "Análise Semanal", "Heatmap Temporal"])
        
        with tab1:
            daily_counts = df.groupby([df['data_emissao_dt'].dt.date, 'is_suspicious']).size().reset_index(name='count')
            
            fig_line = px.line(
                daily_counts,
                x='data_emissao_dt',
                y='count',
                color='is_suspicious',
                title="Emissão de Duplicatas por Dia",
                color_discrete_map={True: '#ff6b6b', False: '#51cf66'}
            )
            fig_line.update_layout(xaxis_title="Data", yaxis_title="Número de Duplicatas")
            st.plotly_chart(fig_line, use_container_width=True)
        
        with tab2:
            # Weekly analysis
            df['weekday'] = df['data_emissao_dt'].dt.day_name()
            df['hour'] = df['data_emissao_dt'].dt.hour
            
            weekday_counts = df.groupby(['weekday', 'is_suspicious']).size().reset_index(name='count')
            
            fig_bar_week = px.bar(
                weekday_counts,
                x='weekday',
                y='count',
                color='is_suspicious',
                title="Emissões por Dia da Semana",
                color_discrete_map={True: '#ff6b6b', False: '#51cf66'},
                category_orders={'weekday': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}
            )
            st.plotly_chart(fig_bar_week, use_container_width=True)
        
        with tab3:
            # Heatmap of emissions by day and hour
            if 'hour' in df.columns:
                heatmap_data = df.pivot_table(
                    values='valor', 
                    index='weekday', 
                    columns='hour', 
                    aggfunc='count', 
                    fill_value=0
                )
                
                fig_heatmap = px.imshow(
                    heatmap_data,
                    title="Heatmap de Emissões (Dia da Semana vs Hora)",
                    color_continuous_scale="Reds"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Top sacadores/sacados
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏢 Top 5 Sacadores por Risco")
        sacador_risk = df.groupby('sacador').agg({
            'is_suspicious': 'sum',
            'risk_score': 'mean'
        }).sort_values('is_suspicious', ascending=False).head(5)
        
        fig_bar1 = px.bar(
            x=sacador_risk.index,
            y=sacador_risk['is_suspicious'],
            title="Sacadores com Mais Duplicatas Suspeitas",
            color=sacador_risk['risk_score'],
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_bar1, use_container_width=True)
    
    with col2:
        st.subheader("👥 Top 5 Sacados por Risco")
        sacado_risk = df.groupby('sacado').agg({
            'is_suspicious': 'sum',
            'risk_score': 'mean'
        }).sort_values('is_suspicious', ascending=False).head(5)
        
        fig_bar2 = px.bar(
            x=sacado_risk.index,
            y=sacado_risk['is_suspicious'],
            title="Sacados com Mais Duplicatas Suspeitas",
            color=sacado_risk['risk_score'],
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_bar2, use_container_width=True)
    
    st.markdown("---")
    
    # Data table
    st.subheader("📋 Tabela de Duplicatas")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_status = st.selectbox(
            "Filtrar por Status",
            ["Todas", "Apenas Suspeitas", "Apenas Seguras"]
        )
    
    with col2:
        filter_sacador = st.selectbox(
            "Filtrar por Sacador",
            ["Todos"] + sorted(df['sacador'].unique().tolist())
        )
    
    with col3:
        min_valor = st.number_input("Valor Mínimo (R$)", min_value=0.0, value=0.0)
    
    # Apply filters
    filtered_df = df.copy()
    
    if filter_status == "Apenas Suspeitas":
        filtered_df = filtered_df[filtered_df['is_suspicious'] == True]
    elif filter_status == "Apenas Seguras":
        filtered_df = filtered_df[filtered_df['is_suspicious'] == False]
    
    if filter_sacador != "Todos":
        filtered_df = filtered_df[filtered_df['sacador'] == filter_sacador]
    
    if min_valor > 0:
        filtered_df = filtered_df[filtered_df['valor'] >= min_valor]
    
    # Format display dataframe
    display_df = filtered_df.copy()
    display_df['Status'] = display_df['is_suspicious'].apply(
        lambda x: "🚨 Suspeita" if x else "✅ Segura"
    )
    display_df['Valor'] = display_df['valor'].apply(lambda x: f"R$ {x:,.2f}")
    display_df['Score de Risco'] = display_df['risk_score'].apply(lambda x: f"{x:.2f}")
    display_df['Motivos'] = display_df['fraud_reasons'].apply(lambda x: "; ".join(x) if x else "Nenhum")
    
    # Select columns to display
    display_columns = [
        'id_duplicata', 'sacador', 'sacado', 'Valor', 
        'data_emissao', 'data_vencimento', 'Status', 
        'Score de Risco', 'Motivos'
    ]
    
    st.dataframe(
        display_df[display_columns],
        use_container_width=True,
        hide_index=True
    )
    
    # Export functionality
    st.subheader("📤 Exportar Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Exportar Todas as Duplicatas"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"duplicatas_todas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("Exportar Apenas Suspeitas"):
            suspicious_df = df[df['is_suspicious'] == True]
            csv = suspicious_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"duplicatas_suspeitas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()