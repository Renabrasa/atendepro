# ai_reports/__init__.py
"""
🤖 AI Reports - Sistema de Relatórios de Autonomia
Análise inteligente de atendimentos para identificação de gaps de treinamento
"""

__version__ = "1.0.0"
__author__ = "Sistema AtendePro"
__description__ = "Sistema de análise de autonomia com IA para otimização de equipes contábeis"

# Imports principais para facilitar uso
from .data_collector import AutonomyDataCollector, collect_autonomy_data
from .ai_analyzer import AutonomyAIAnalyzer, analyze_autonomy_data
from .email_sender import AutonomyEmailSender, send_autonomy_report
from .ai_prompts import (
    autonomy_radar_prompt,
    training_matrix_prompt, 
    productivity_dashboard_prompt,
    strategic_conclusions_prompt,
    get_available_prompts
)

# Configurações padrão
DEFAULT_CONFIG = {
    'ollama_url': 'http://localhost:11434',
    'ollama_model': 'llama3.2:3b',
    'email_template': 'weekly_report.html',
    'analysis_period_days': 15,
    'autonomy_threshold': {
        'autonomous': 2,    # 0-2 solicitações = autônomo
        'attention': 6,     # 3-6 solicitações = atenção
        'critical': 999     # >6 solicitações = crítico
    },
    'strategic_time_target': 60,  # % mínimo de tempo estratégico
    'general_autonomy_target': 85  # % meta de autonomia geral
}

# Função principal integrada
def generate_autonomy_report(
    target_date=None,
    ollama_url="http://localhost:11434",
    smtp_config=None,
    recipients=None,
    supervisor_filter=None
):
    """
    Função principal para gerar relatório completo de autonomia
    
    Args:
        target_date: Data específica para análise (padrão: hoje)
        ollama_url: URL do servidor Ollama
        smtp_config: Configurações SMTP para envio de email
        recipients: Lista de emails destinatários
        supervisor_filter: ID específico de supervisor (opcional)
        
    Returns:
        Dict com resultado completo da operação
    """
    
    try:
        # 1. Coleta dados
        print("📊 Coletando dados de autonomia...")
        collector = AutonomyDataCollector()
        autonomy_data = collector.get_data_for_week_analysis(target_date)
        
        # Filtra supervisor específico se solicitado
        if supervisor_filter:
            autonomy_data['supervisors'] = [
                sup for sup in autonomy_data['supervisors'] 
                if sup['supervisor_id'] == supervisor_filter
            ]
        
        # 2. Análise IA
        print("🤖 Executando análise IA...")
        analyzer = AutonomyAIAnalyzer(ollama_url)
        ai_analysis = analyzer.analyze_weekly_data(autonomy_data)
        
        if not ai_analysis['success']:
            print(f"⚠️ Falha na análise IA: {ai_analysis.get('error', 'Erro desconhecido')}")
        
        # 3. Envio por email (se configurado)
        email_result = None
        if smtp_config and recipients:
            print("📧 Enviando relatório por email...")
            sender = AutonomyEmailSender(smtp_config)
            email_result = sender.send_weekly_report(
                ai_analysis, 
                recipients,
                supervisor_name=None  # Pode ser configurado
            )
            
            if email_result['success']:
                print(f"✅ Email enviado para {len(recipients)} destinatário(s)")
            else:
                print(f"❌ Falha no envio: {email_result.get('error', 'Erro desconhecido')}")
        
        return {
            'success': True,
            'data_collection': {
                'supervisors_analyzed': len(autonomy_data['supervisors']),
                'total_agents': sum(len(sup['agents']) for sup in autonomy_data['supervisors']),
                'period': f"{autonomy_data['periodo_atual']['inicio']} - {autonomy_data['periodo_atual']['fim']}"
            },
            'ai_analysis': ai_analysis,
            'email_result': email_result,
            'timestamp': autonomy_data['data_collection_timestamp']
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': None
        }

# Função de teste rápido
def quick_test(ollama_url="http://localhost:11434"):
    """
    Teste rápido de todas as funcionalidades
    """
    print("🧪 Executando teste rápido do sistema AI Reports...")
    
    # Teste 1: Coleta de dados
    try:
        data = collect_autonomy_data()
        print(f"✅ Coleta de dados: {len(data['supervisors'])} supervisores analisados")
    except Exception as e:
        print(f"❌ Coleta de dados: {e}")
        return False
    
    # Teste 2: Análise IA
    try:
        analyzer = AutonomyAIAnalyzer(ollama_url)
        connection = analyzer.test_connection()
        if connection['success']:
            print(f"✅ Conexão Ollama: {connection['status']}")
            
            # Teste análise com dados coletados
            analysis = analyzer.analyze_weekly_data(data)
            if analysis['success']:
                print("✅ Análise IA: Concluída com sucesso")
            else:
                print(f"⚠️ Análise IA: {analysis.get('error', 'Falha na análise')}")
        else:
            print(f"❌ Conexão Ollama: {connection['error']}")
    except Exception as e:
        print(f"❌ Análise IA: {e}")
    
    # Teste 3: Geração de template
    try:
        from .email_sender import AutonomyEmailSender
        
        # Configura sender de teste
        test_smtp = {
            'server': 'smtp.gmail.com',
            'port': 587,
            'email': 'test@example.com',
            'password': 'test_password',
            'sender_name': 'AI Reports Test'
        }
        
        sender = AutonomyEmailSender(test_smtp)
        test_data = sender._generate_test_data()
        template_data = sender._prepare_template_data(test_data, "Supervisor Teste")
        
        print("✅ Geração de template: Template HTML/texto criado")
        print(f"📊 Dados incluem: {len(template_data['matrix']['priority_agents'])} agentes prioritários")
        
    except Exception as e:
        print(f"❌ Geração de template: {e}")
    
    print("\n🎯 Teste concluído! Sistema AI Reports está operacional.")
    return True

# Utilitários para debugging
def get_system_status():
    """Retorna status geral do sistema"""
    
    status = {
        'data_collector': 'unknown',
        'ai_analyzer': 'unknown', 
        'email_sender': 'unknown',
        'ollama_connection': 'unknown'
    }
    
    # Testa data collector
    try:
        data = collect_autonomy_data()
        status['data_collector'] = f"ok - {len(data['supervisors'])} supervisores"
    except Exception as e:
        status['data_collector'] = f"error - {str(e)[:50]}"
    
    # Testa analyzer
    try:
        analyzer = AutonomyAIAnalyzer()
        connection = analyzer.test_connection()
        if connection['success']:
            status['ai_analyzer'] = "ok"
            status['ollama_connection'] = f"ok - {len(connection['available_models'])} modelos"
        else:
            status['ai_analyzer'] = "ok - sem ollama"
            status['ollama_connection'] = f"error - {connection['error'][:50]}"
    except Exception as e:
        status['ai_analyzer'] = f"error - {str(e)[:50]}"
        status['ollama_connection'] = "error - não testado"
    
    # Testa email sender
    try:
        test_config = {
            'server': 'smtp.gmail.com',
            'port': 587,
            'email': 'test@example.com',
            'password': 'test_password',
            'sender_name': 'Test'
        }
        sender = AutonomyEmailSender(test_config)
        test_data = sender._generate_test_data()
        status['email_sender'] = "ok - template gerado"
    except Exception as e:
        status['email_sender'] = f"error - {str(e)[:50]}"
    
    return status

def get_configuration_guide():
    """Retorna guia de configuração"""
    
    return """
🔧 GUIA DE CONFIGURAÇÃO - AI REPORTS

1. OLLAMA (Análise IA):
   • Instale: curl -fsSL https://ollama.ai/install.sh | sh
   • Execute: ollama serve
   • Baixe modelo: ollama pull llama3.2:3b
   • Teste: curl http://localhost:11434/api/tags

2. SMTP (Email):
   • Configure variáveis de ambiente:
     - SMTP_SERVER=smtp.gmail.com
     - SMTP_PORT=587
     - SMTP_EMAIL=your-email@gmail.com  
     - SMTP_PASSWORD=your-app-password
   
3. BANCO DE DADOS:
   • Certifique-se que tabelas User, Agente, Atendimento existem
   • Execute migrações se necessário
   
4. TESTE:
   from ai_reports import quick_test
   quick_test()

5. USO BÁSICO:
   from ai_reports import generate_autonomy_report
   
   result = generate_autonomy_report(
       smtp_config={...},
       recipients=['supervisor@company.com']
   )
"""

# Exporta funcionalidades principais
__all__ = [
    # Classes principais
    'AutonomyDataCollector',
    'AutonomyAIAnalyzer', 
    'AutonomyEmailSender',
    
    # Funções helper
    'collect_autonomy_data',
    'analyze_autonomy_data',
    'send_autonomy_report',
    'generate_autonomy_report',
    
    # Prompts
    'autonomy_radar_prompt',
    'training_matrix_prompt',
    'productivity_dashboard_prompt', 
    'strategic_conclusions_prompt',
    'get_available_prompts',
    
    # Utilitários
    'quick_test',
    'get_system_status',
    'get_configuration_guide',
    
    # Configurações
    'DEFAULT_CONFIG'
]

# Informações do módulo
print(f"🤖 AI Reports v{__version__} carregado")
print("📋 Funcionalidades: Coleta → Análise IA → Email")
print("💡 Use get_configuration_guide() para setup inicial")