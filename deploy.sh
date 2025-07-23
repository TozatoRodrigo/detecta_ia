#!/bin/bash

# Script de Deploy para Plataforma de Detecção de Fraude
# Suporta deploy local, staging e produção

set -e  # Exit on any error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
APP_NAME="fraud-detection-platform"
VERSION=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"

# Funções utilitárias
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Função para verificar dependências
check_dependencies() {
    log_info "Verificando dependências..."
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 não encontrado"
        exit 1
    fi
    
    # Verificar pip
    if ! command -v pip &> /dev/null; then
        log_error "pip não encontrado"
        exit 1
    fi
    
    # Verificar Docker (opcional)
    if command -v docker &> /dev/null; then
        log_success "Docker encontrado"
        DOCKER_AVAILABLE=true
    else
        log_warning "Docker não encontrado - deploy sem containerização"
        DOCKER_AVAILABLE=false
    fi
    
    log_success "Dependências verificadas"
}

# Função para executar testes
run_tests() {
    log_info "Executando testes..."
    
    # Ativar ambiente virtual se existir
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Instalar dependências de teste
    pip install pytest pytest-cov
    
    # Executar testes
    if python -m pytest tests/ -v --cov=backend/app --cov-report=html; then
        log_success "Todos os testes passaram"
    else
        log_error "Alguns testes falharam"
        exit 1
    fi
}

# Função para fazer backup
create_backup() {
    log_info "Criando backup..."
    
    mkdir -p $BACKUP_DIR
    
    # Backup do banco de dados (se SQLite)
    if [ -f "fraud_detection.db" ]; then
        cp fraud_detection.db "$BACKUP_DIR/fraud_detection_$VERSION.db"
        log_success "Backup do banco criado"
    fi
    
    # Backup dos logs
    if [ -f "app.log" ]; then
        cp app.log "$BACKUP_DIR/app_$VERSION.log"
    fi
    
    if [ -f "audit.log" ]; then
        cp audit.log "$BACKUP_DIR/audit_$VERSION.log"
    fi
    
    log_success "Backup criado em $BACKUP_DIR/"
}

# Função para deploy local
deploy_local() {
    log_info "Iniciando deploy local..."
    
    # Criar ambiente virtual se não existir
    if [ ! -d "venv" ]; then
        log_info "Criando ambiente virtual..."
        python3 -m venv venv
    fi
    
    # Ativar ambiente virtual
    source venv/bin/activate
    
    # Atualizar pip
    pip install --upgrade pip
    
    # Instalar dependências
    log_info "Instalando dependências..."
    pip install -r backend/requirements.txt
    
    # Criar arquivo .env se não existir
    if [ ! -f ".env" ]; then
        log_info "Criando arquivo .env..."
        cp .env.example .env
        log_warning "Configure o arquivo .env antes de usar em produção"
    fi
    
    # Executar migrações do banco (se necessário)
    log_info "Configurando banco de dados..."
    python -c "from backend.app.database import create_tables; create_tables()"
    
    log_success "Deploy local concluído!"
    log_info "Para iniciar a aplicação:"
    log_info "  Backend: uvicorn backend.main:app --reload"
    log_info "  Dashboard: streamlit run dashboard.py"
}

# Função para deploy com Docker
deploy_docker() {
    log_info "Iniciando deploy com Docker..."
    
    # Construir imagem
    log_info "Construindo imagem Docker..."
    docker build -t $APP_NAME:$VERSION .
    docker tag $APP_NAME:$VERSION $APP_NAME:latest
    
    # Parar containers existentes
    log_info "Parando containers existentes..."
    docker-compose down || true
    
    # Iniciar novos containers
    log_info "Iniciando containers..."
    docker-compose up -d
    
    # Verificar se os containers estão rodando
    sleep 5
    if docker-compose ps | grep -q "Up"; then
        log_success "Containers iniciados com sucesso"
    else
        log_error "Falha ao iniciar containers"
        exit 1
    fi
    
    log_success "Deploy Docker concluído!"
}

# Função para deploy em produção
deploy_production() {
    log_info "Iniciando deploy de produção..."
    
    # Verificações de segurança
    if [ ! -f ".env" ]; then
        log_error "Arquivo .env não encontrado"
        exit 1
    fi
    
    # Verificar se SECRET_KEY foi alterada
    if grep -q "your-secret-key-change-in-production" .env; then
        log_error "SECRET_KEY deve ser alterada para produção"
        exit 1
    fi
    
    # Verificar se está usando banco de produção
    if grep -q "sqlite" .env; then
        log_warning "SQLite não é recomendado para produção"
    fi
    
    # Executar testes
    run_tests
    
    # Criar backup
    create_backup
    
    # Deploy baseado na disponibilidade do Docker
    if [ "$DOCKER_AVAILABLE" = true ]; then
        deploy_docker
    else
        deploy_local
    fi
    
    # Configurar monitoramento
    setup_monitoring
    
    log_success "Deploy de produção concluído!"
}

# Função para configurar monitoramento
setup_monitoring() {
    log_info "Configurando monitoramento..."
    
    # Criar script de health check
    cat > health_check.sh << 'EOF'
#!/bin/bash
# Health check script

API_URL="http://localhost:8000"
DASHBOARD_URL="http://localhost:8501"

# Verificar API
if curl -f -s "$API_URL/docs" > /dev/null; then
    echo "✅ API está respondendo"
else
    echo "❌ API não está respondendo"
    exit 1
fi

# Verificar Dashboard
if curl -f -s "$DASHBOARD_URL" > /dev/null; then
    echo "✅ Dashboard está respondendo"
else
    echo "❌ Dashboard não está respondendo"
    exit 1
fi

echo "🎉 Todos os serviços estão funcionando"
EOF
    
    chmod +x health_check.sh
    
    # Criar script de monitoramento de logs
    cat > monitor_logs.sh << 'EOF'
#!/bin/bash
# Monitor de logs

LOG_FILE="app.log"
AUDIT_FILE="audit.log"

echo "📊 Monitoramento de Logs - $(date)"
echo "=================================="

if [ -f "$LOG_FILE" ]; then
    echo "📝 Últimas 10 linhas do log da aplicação:"
    tail -n 10 "$LOG_FILE"
    echo ""
fi

if [ -f "$AUDIT_FILE" ]; then
    echo "🔍 Últimas 5 linhas do log de auditoria:"
    tail -n 5 "$AUDIT_FILE"
    echo ""
fi

# Verificar erros recentes
if [ -f "$LOG_FILE" ]; then
    ERROR_COUNT=$(grep -c "ERROR" "$LOG_FILE" 2>/dev/null || echo 0)
    echo "⚠️  Total de erros no log: $ERROR_COUNT"
fi
EOF
    
    chmod +x monitor_logs.sh
    
    log_success "Scripts de monitoramento criados"
}

# Função para rollback
rollback() {
    log_info "Iniciando rollback..."
    
    # Parar serviços atuais
    if [ "$DOCKER_AVAILABLE" = true ]; then
        docker-compose down
    else
        pkill -f "uvicorn"
        pkill -f "streamlit"
    fi
    
    # Restaurar backup do banco
    LATEST_BACKUP=$(ls -t $BACKUP_DIR/fraud_detection_*.db 2>/dev/null | head -n1)
    if [ -n "$LATEST_BACKUP" ]; then
        cp "$LATEST_BACKUP" fraud_detection.db
        log_success "Banco de dados restaurado"
    fi
    
    log_success "Rollback concluído"
}

# Função para limpeza
cleanup() {
    log_info "Executando limpeza..."
    
    # Remover backups antigos (manter apenas os 5 mais recentes)
    if [ -d "$BACKUP_DIR" ]; then
        find $BACKUP_DIR -name "*.db" -type f | sort -r | tail -n +6 | xargs rm -f
        find $BACKUP_DIR -name "*.log" -type f | sort -r | tail -n +6 | xargs rm -f
    fi
    
    # Limpar logs antigos
    if [ -f "app.log" ] && [ $(stat -f%z "app.log" 2>/dev/null || stat -c%s "app.log") -gt 104857600 ]; then
        mv app.log "app_$(date +%Y%m%d).log"
        touch app.log
    fi
    
    log_success "Limpeza concluída"
}

# Função principal
main() {
    echo "🚀 Deploy da Plataforma de Detecção de Fraude"
    echo "=============================================="
    
    # Verificar argumentos
    case "${1:-local}" in
        "local")
            check_dependencies
            deploy_local
            ;;
        "docker")
            check_dependencies
            deploy_docker
            ;;
        "production")
            check_dependencies
            deploy_production
            ;;
        "test")
            check_dependencies
            run_tests
            ;;
        "backup")
            create_backup
            ;;
        "rollback")
            rollback
            ;;
        "cleanup")
            cleanup
            ;;
        "monitor")
            ./health_check.sh
            ./monitor_logs.sh
            ;;
        *)
            echo "Uso: $0 {local|docker|production|test|backup|rollback|cleanup|monitor}"
            echo ""
            echo "Comandos disponíveis:"
            echo "  local      - Deploy local (desenvolvimento)"
            echo "  docker     - Deploy com Docker"
            echo "  production - Deploy de produção"
            echo "  test       - Executar apenas os testes"
            echo "  backup     - Criar backup dos dados"
            echo "  rollback   - Fazer rollback para versão anterior"
            echo "  cleanup    - Limpar arquivos antigos"
            echo "  monitor    - Verificar status dos serviços"
            exit 1
            ;;
    esac
}

# Executar função principal
main "$@"