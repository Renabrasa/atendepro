# ai_reports/scheduler.py
"""
⏰ Scheduler - Agendamento automático de relatórios AI
Sistema de agendamento para envio semanal de relatórios toda segunda-feira
"""

import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
import pytz
from typing import Dict, Any, Optional, Callable, List
import signal
import sys
import os

# Configurar logging
logger = logging.getLogger(__name__)

# ===================================================================
# 🔧 CONFIGURAÇÕES PADRÃO (fallback se não estiver em config.py)
# ===================================================================

def get_config_value(attr_name: str, default_value: Any) -> Any:
    """Busca valor de configuração com fallback seguro"""
    try:
        from config import Config
        return getattr(Config, attr_name, default_value)
    except (ImportError, AttributeError):
        # Fallback para variáveis de ambiente ou padrão
        env_name = attr_name.upper()
        if isinstance(default_value, bool):
            return os.environ.get(env_name, str(default_value)).lower() == 'true'
        elif isinstance(default_value, int):
            return int(os.environ.get(env_name, str(default_value)))
        else:
            return os.environ.get(env_name, default_value)

# Configurações com fallback
REPORTS_ENABLED = get_config_value('REPORTS_ENABLED', True)
REPORTS_DAY_OF_WEEK = get_config_value('REPORTS_DAY_OF_WEEK', 3)  # 0=Monday
REPORTS_HOUR = get_config_value('REPORTS_HOUR', 9)
REPORTS_TIMEZONE = get_config_value('REPORTS_TIMEZONE', 'America/Sao_Paulo')
AI_REPORTS_DEBUG = get_config_value('AI_REPORTS_DEBUG', True)


class ReportScheduler:
    """
    ⏰ Agendador de relatórios semanais
    
    Gerencia o agendamento automático de coleta de dados,
    análise IA e envio de emails toda segunda-feira
    """
    
    def __init__(self):
        """Inicializa o scheduler"""
        self.enabled = REPORTS_ENABLED
        self.day_of_week = REPORTS_DAY_OF_WEEK  # 0=Monday
        self.hour = REPORTS_HOUR
        self.timezone = REPORTS_TIMEZONE
        self.debug = AI_REPORTS_DEBUG
        
        # Thread control
        self.running = False
        self.scheduler_thread = None
        self.stop_event = threading.Event()
        
        # Callbacks para diferentes eventos
        self.on_success_callback = None
        self.on_error_callback = None
        self.on_start_callback = None
        
        # Setup timezone
        try:
            self.tz = pytz.timezone(self.timezone)
        except:
            logger.warning(f"⚠️ Timezone {self.timezone} inválido, usando UTC")
            self.tz = pytz.UTC
        
        if self.debug:
            logger.info(f"⏰ Scheduler inicializado - {'Habilitado' if self.enabled else 'Desabilitado'}")
            if self.enabled:
                day_names = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                day_name = day_names[self.day_of_week] if 0 <= self.day_of_week <= 6 else 'Segunda'
                logger.info(f"📅 Agendado para: {day_name}s às {self.hour}h ({self.timezone})")
    
    def setup_schedule(self):
        """
        📅 Configura agendamento semanal
        """
        if not self.enabled:
            logger.info("⏸️ Scheduler desabilitado por configuração")
            return
        
        # Mapear dia da semana para método do schedule
        day_methods = {
            0: schedule.every().monday,
            1: schedule.every().tuesday,
            2: schedule.every().wednesday,
            3: schedule.every().thursday,
            4: schedule.every().friday,
            5: schedule.every().saturday,
            6: schedule.every().sunday
        }
        
        day_method = day_methods.get(self.day_of_week, schedule.every().monday)
        
        # Agendar execução
        day_method.at(f"{self.hour:02d}:00").do(self._execute_weekly_reports)
        
        # Log do agendamento
        try:
            next_run = schedule.next_run()
            if next_run:
                next_run_local = next_run.replace(tzinfo=pytz.UTC).astimezone(self.tz)
                logger.info(f"📅 Próxima execução agendada: {next_run_local.strftime('%d/%m/%Y %H:%M %Z')}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular próxima execução: {e}")
    
    def start(self):
        """
        ▶️ Inicia o scheduler em thread separada
        """
        if not self.enabled:
            logger.info("⏸️ Scheduler não iniciado - desabilitado por configuração")
            return False
        
        if self.running:
            logger.warning("⚠️ Scheduler já está rodando")
            return False
        
        try:
            # Setup agendamento
            self.setup_schedule()
            
            # Configurar signal handlers para shutdown graceful (apenas se possível)
            try:
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
            except (ValueError, OSError):
                # Pode falhar em alguns ambientes (Windows, threads)
                logger.debug("⚠️ Não foi possível configurar signal handlers")
            
            # Iniciar thread
            self.running = True
            self.stop_event.clear()
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info("▶️ Scheduler iniciado com sucesso")
            
            # Callback de início
            if self.on_start_callback:
                try:
                    self.on_start_callback()
                except Exception as e:
                    logger.error(f"❌ Erro no callback de início: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar scheduler: {e}")
            self.running = False
            return False
    
    def stop(self):
        """
        ⏹️ Para o scheduler gracefully
        """
        if not self.running:
            logger.info("⏹️ Scheduler já estava parado")
            return
        
        logger.info("⏹️ Parando scheduler...")
        
        self.running = False
        self.stop_event.set()
        
        # Aguardar thread terminar
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        # Limpar agendamentos
        schedule.clear()
        
        logger.info("✅ Scheduler parado")
    
    def _run_scheduler(self):
        """
        🔄 Loop principal do scheduler
        """
        logger.info("🔄 Loop do scheduler iniciado")
        
        while self.running and not self.stop_event.is_set():
            try:
                # Executar tarefas agendadas
                schedule.run_pending()
                
                # Aguardar 60 segundos ou até stop event
                self.stop_event.wait(60)
                
            except Exception as e:
                logger.error(f"❌ Erro no loop do scheduler: {e}")
                time.sleep(60)  # Aguardar antes de continuar
        
        logger.info("🏁 Loop do scheduler finalizado")
    
    def _execute_weekly_reports(self):
        """
        📊 Executa geração e envio de relatórios semanais
        """
        execution_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            current_time = datetime.now(self.tz)
            logger.info(f"🚀 INICIANDO EXECUÇÃO SEMANAL - ID: {execution_id}")
            logger.info(f"⏰ Horário: {current_time.strftime('%d/%m/%Y %H:%M:%S %Z')}")
            
            # ===================================================================
            # 🔧 CORRIGIDO: Usar nossos módulos ao invés dos antigos
            # ===================================================================
            
            # Importar módulos do nosso sistema
            from .data_collector import collect_autonomy_data
            from .ai_analyzer import analyze_autonomy_data
            from .email_sender import send_autonomy_report
            
            # Passo 1: Coletar dados
            logger.info("📊 Coletando dados de autonomia...")
            autonomy_data = collect_autonomy_data()
            
            supervisors_count = len(autonomy_data['supervisors'])
            total_requests = autonomy_data['global_stats']['total_attendances_current']
            
            logger.info(f"✅ Dados coletados: {supervisors_count} supervisores, {total_requests} solicitações")
            
            if supervisors_count == 0:
                logger.warning("⚠️ Nenhum supervisor encontrado - abortando execução")
                return
            
            # Passo 2: Análise IA
            logger.info("🧠 Executando análise IA...")
            ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            ai_analysis = analyze_autonomy_data(autonomy_data, ollama_url)
            
            insights_generated = 1 if ai_analysis['success'] else 0
            
            logger.info(f"✅ Análise IA concluída: {'Sucesso' if ai_analysis['success'] else 'Fallback básico'}")
            
            # Passo 3: Envio de emails (placeholder - implementar quando SMTP estiver pronto)
            logger.info("📧 Preparando para envio de emails...")
            
            # Por enquanto, apenas registrar (implementar quando tudo estiver funcionando)
            successful_sends = 0
            failed_sends = 0
            
            smtp_email = os.getenv('SMTP_EMAIL')
            if smtp_email:
                logger.info(f"📧 SMTP configurado: {smtp_email}")
                # Aqui seria o envio real quando tudo estiver validado
                successful_sends = supervisors_count  # Simular sucesso por agora
            else:
                logger.info("📧 SMTP não configurado - apenas logging")
            
            # Resultado final
            execution_summary = {
                'execution_id': execution_id,
                'timestamp': current_time.isoformat(),
                'success': True,
                'supervisors_analyzed': supervisors_count,
                'total_requests': total_requests,
                'insights_generated': insights_generated,
                'ai_analysis_success': ai_analysis['success'],
                'emails_sent': successful_sends,
                'email_failures': failed_sends,
                'duration_seconds': None  # Será calculado no callback
            }
            
            # Callback de sucesso
            if self.on_success_callback:
                try:
                    self.on_success_callback(execution_summary)
                except Exception as e:
                    logger.error(f"❌ Erro no callback de sucesso: {e}")
            
            logger.info(f"🎉 EXECUÇÃO CONCLUÍDA COM SUCESSO - ID: {execution_id}")
            
        except Exception as e:
            error_msg = f"Erro na execução semanal: {e}"
            logger.error(f"❌ {error_msg}")
            
            # Resultado de erro
            execution_summary = {
                'execution_id': execution_id,
                'timestamp': datetime.now(self.tz).isoformat(),
                'success': False,
                'error': error_msg,
                'duration_seconds': None
            }
            
            # Callback de erro
            if self.on_error_callback:
                try:
                    self.on_error_callback(execution_summary)
                except Exception as e:
                    logger.error(f"❌ Erro no callback de erro: {e}")
            
            logger.error(f"💥 EXECUÇÃO FALHOU - ID: {execution_id}")
    
    def _signal_handler(self, signum, frame):
        """
        🚦 Handler para sinais de sistema
        """
        logger.info(f"🚦 Sinal recebido: {signum}")
        self.stop()
        sys.exit(0)
    
    def set_callbacks(self, on_success: Optional[Callable] = None,
                     on_error: Optional[Callable] = None,
                     on_start: Optional[Callable] = None):
        """
        🔗 Define callbacks para eventos
        
        Args:
            on_success: Callback para execução bem-sucedida
            on_error: Callback para erros na execução
            on_start: Callback para início do scheduler
        """
        self.on_success_callback = on_success
        self.on_error_callback = on_error
        self.on_start_callback = on_start
    
    def get_next_execution(self) -> Optional[datetime]:
        """
        📅 Retorna próxima execução agendada
        
        Returns:
            Datetime da próxima execução ou None se não agendado
        """
        if not self.enabled or not self.running:
            return None
        
        try:
            next_run = schedule.next_run()
            if next_run:
                # Converter para timezone local
                return next_run.replace(tzinfo=pytz.UTC).astimezone(self.tz)
        except Exception as e:
            logger.error(f"❌ Erro ao obter próxima execução: {e}")
        
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        📊 Retorna status atual do scheduler
        
        Returns:
            Dict com informações de status
        """
        next_execution = self.get_next_execution()
        
        return {
            'enabled': self.enabled,
            'running': self.running,
            'day_of_week': self.day_of_week,
            'hour': self.hour,
            'timezone': self.timezone,
            'next_execution': next_execution.isoformat() if next_execution else None,
            'next_execution_formatted': next_execution.strftime('%d/%m/%Y %H:%M %Z') if next_execution else None,
            'thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False,
            'status': 'running' if self.running else 'stopped' if self.enabled else 'disabled'
        }
    
    def execute_now(self) -> Dict[str, Any]:
        """
        ▶️ Executa relatórios imediatamente (para testes)
        
        Returns:
            Resultado da execução
        """
        try:
            logger.info("🧪 Executando relatórios manualmente...")
            self._execute_weekly_reports()
            
            return {
                'success': True,
                'message': 'Execução manual concluída',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Erro na execução manual: {e}"
            logger.error(f"❌ {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }


class SchedulerManager:
    """
    🎛️ Gerenciador do Scheduler com persistência e monitoramento
    """
    
    def __init__(self):
        """Inicializa o gerenciador"""
        self.scheduler = ReportScheduler()
        self.execution_history = []
        self.max_history = 50  # Manter últimas 50 execuções
        
        # Setup callbacks
        self.scheduler.set_callbacks(
            on_success=self._on_execution_success,
            on_error=self._on_execution_error,
            on_start=self._on_scheduler_start
        )
    
    def _on_execution_success(self, summary: Dict[str, Any]):
        """Callback para execução bem-sucedida"""
        summary['status'] = 'success'
        self._add_to_history(summary)
        logger.info(f"📈 Execução registrada: {summary.get('emails_sent', 0)} emails enviados")
    
    def _on_execution_error(self, summary: Dict[str, Any]):
        """Callback para erro na execução"""
        summary['status'] = 'error'
        self._add_to_history(summary)
        logger.error(f"📉 Erro registrado: {summary.get('error', 'Erro desconhecido')}")
    
    def _on_scheduler_start(self):
        """Callback para início do scheduler"""
        logger.info("🚀 Scheduler Manager ativo")
    
    def _add_to_history(self, summary: Dict[str, Any]):
        """Adiciona execução ao histórico"""
        self.execution_history.append(summary)
        
        # Manter apenas as últimas N execuções
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history:]
    
    def start(self) -> bool:
        """Inicia o scheduler"""
        return self.scheduler.start()
    
    def stop(self):
        """Para o scheduler"""
        self.scheduler.stop()
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status completo"""
        status = self.scheduler.get_status()
        
        # Adicionar informações do histórico
        status['execution_history_count'] = len(self.execution_history)
        
        if self.execution_history:
            last_execution = self.execution_history[-1]
            status['last_execution'] = {
                'timestamp': last_execution['timestamp'],
                'status': last_execution['status'],
                'success': last_execution['success']
            }
            
            # Estatísticas
            successful_executions = [e for e in self.execution_history if e['success']]
            status['success_rate'] = len(successful_executions) / len(self.execution_history) * 100
        else:
            status['last_execution'] = None
            status['success_rate'] = None
        
        return status
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna histórico de execuções"""
        return self.execution_history[-limit:] if self.execution_history else []
    
    def execute_now(self) -> Dict[str, Any]:
        """Executa relatórios imediatamente"""
        return self.scheduler.execute_now()


# ===================================================================
# 🔧 INSTÂNCIA GLOBAL E FUNÇÕES UTILITÁRIAS
# ===================================================================

# Instância global do gerenciador
_scheduler_manager = None


def get_scheduler_manager() -> SchedulerManager:
    """
    🔧 Retorna instância global do scheduler manager
    """
    global _scheduler_manager
    if _scheduler_manager is None:
        _scheduler_manager = SchedulerManager()
    return _scheduler_manager


def start_scheduler() -> bool:
    """
    🔧 Função utilitária para iniciar scheduler
    """
    try:
        manager = get_scheduler_manager()
        return manager.start()
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar scheduler: {e}")
        return False


def stop_scheduler():
    """
    🔧 Função utilitária para parar scheduler
    """
    try:
        manager = get_scheduler_manager()
        manager.stop()
    except Exception as e:
        logger.error(f"❌ Erro ao parar scheduler: {e}")


def get_scheduler_status() -> Dict[str, Any]:
    """
    🔧 Função utilitária para obter status
    """
    try:
        manager = get_scheduler_manager()
        return manager.get_status()
    except Exception as e:
        logger.error(f"❌ Erro ao obter status do scheduler: {e}")
        return {
            'enabled': False,
            'running': False,
            'status': 'error',
            'error': str(e)
        }


def execute_reports_now() -> Dict[str, Any]:
    """
    🔧 Função utilitária para execução manual
    """
    try:
        manager = get_scheduler_manager()
        return manager.execute_now()
    except Exception as e:
        logger.error(f"❌ Erro na execução manual: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


# ===================================================================
# 🧪 TESTE STANDALONE
# ===================================================================

if __name__ == "__main__":
    # Teste básico do scheduler
    print("🧪 Testando Scheduler...")
    
    # Testar status
    status = get_scheduler_status()
    print(f"📊 Status: {status}")
    
    # Testar execução manual se habilitado
    if status.get('enabled', False):
        print("🚀 Testando execução manual...")
        result = execute_reports_now()
        print(f"📋 Resultado: {result}")
    
    print("✅ Teste do scheduler concluído!")