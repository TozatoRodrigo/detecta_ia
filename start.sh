#!/bin/bash

echo "🚀 Iniciando Plataforma de Detecção de Fraude"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Install dependencies
echo "📚 Instalando dependências..."
pip install -r backend/requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Criando arquivo .env..."
    cp .env.example .env
fi

echo ""
echo "✅ Setup concluído!"
echo ""
echo "Para iniciar a aplicação:"
echo "1. Backend API: uvicorn backend.main:app --reload"
echo "2. Dashboard: streamlit run dashboard.py"
echo ""
echo "Ou execute os comandos abaixo em terminais separados:"
echo ""

# Start backend in background
echo "🔥 Iniciando Backend API..."
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start dashboard
echo "🎨 Iniciando Dashboard..."
cd ..
streamlit run dashboard.py --server.port 8501 &
DASHBOARD_PID=$!

echo ""
echo "🌐 Aplicação rodando em:"
echo "   - API: http://localhost:8000"
echo "   - Dashboard: http://localhost:8501"
echo "   - Documentação API: http://localhost:8000/docs"
echo ""
echo "Para parar a aplicação, pressione Ctrl+C"

# Wait for user to stop
wait $BACKEND_PID $DASHBOARD_PID