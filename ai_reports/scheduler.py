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

from config import Config

# Configurar logging
logger = logging.getLogger(__name__)


class ReportScheduler:
    """
    ⏰ Agendador de relatórios semanais
    
    Gerencia o agendamento automático de coleta de dados,
    análise IA e envio de emails toda segunda-feira
    """
    
    def __init__(self):
        """Inicializa o scheduler"""
        self.enabled = Config.REPORTS_ENABLED
        self.day_of_week = Config.REPORTS_DAY_OF_WEEK  # 0=Monday
        self.hour = Config.REPORTS_HOUR
        self.timezone = Config.REPORTS_TIMEZONE
        self.debug = Config.AI_REPORTS_DEBUG
        
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
                day_name = day_names[self.day_of_week]
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
        next_run = schedule.next_run()
        if next_run:
            next_run_local = next_run.replace(tzinfo=pytz.UTC).astimezone(self.tz)
            logger.info(f"📅 Próxima execução agendada: {next_run_local.strftime('%d/%m/%Y %H:%M %Z')}")
    
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
            
            # Configurar signal handlers para shutdown graceful
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Iniciar thread
            self.running = True
            self.stop_event.clear()
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info("▶️ Scheduler iniciado com sucesso")
            
            # Callback de início
            if self.on_start_callback:
                self.on_start_callback()
            
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
            
            # Importar módulos necessários
            from .data_collector import collect_weekly_data
            from .ai_analyzer import analyze_weekly_data
            from .email_sender import send_weekly_reports
            
            # Passo 1: Coletar dados
            logger.info("📊 Coletando dados semanais...")
            weekly_data = collect_weekly_data()
            
            supervisors_count = len(weekly_data['supervisors_data'])
            total_tickets = weekly_data['global_stats']['current_week']['total_tickets']
            
            logger.info(f"✅ Dados coletados: {supervisors_count} supervisores, {total_tickets} atendimentos")
            
            if supervisors_count == 0:
                logger.warning("⚠️ Nenhum supervisor encontrado - abortando execução")
                return
            
            # Passo 2: Análise IA
            logger.info("🧠 Executando análise IA...")
            ai_analysis = analyze_weekly_data(weekly_data)
            
            # CORRIGIDO: Usar intelligent_insights ao invés de global_analysis
            intelligent_insights = ai_analysis.get('intelligent_insights', {})
            insights_count = len(intelligent_insights.get('performance_alerts', [])) + len(intelligent_insights.get('concentration_patterns', []))
            
            logger.info(f"✅ Análise IA concluída: {insights_count} insights automáticos gerados")
            logger.info(f"📊 Detalhes: {len(intelligent_insights.get('performance_alerts', []))} alertas, {len(intelligent_insights.get('concentration_patterns', []))} padrões")
            
            # Passo 3: Envio de emails
            logger.info("📧 Enviando relatórios por email...")
            email_results = send_weekly_reports(weekly_data, ai_analysis)
            
            successful_sends = email_results['successful_sends']
            failed_sends = email_results['failed_sends']
            
            logger.info(f"✅ Emails enviados: {successful_sends} sucessos, {failed_sends} falhas")
            
            # Resultado final
            execution_summary = {
                'execution_id': execution_id,
                'timestamp': current_time.isoformat(),
                'success': True,
                'supervisors_analyzed': supervisors_count,
                'total_tickets': total_tickets,
                'insights_generated': insights_count,
                'alerts_detected': len(intelligent_insights.get('performance_alerts', [])),
                'patterns_identified': len(intelligent_insights.get('concentration_patterns', [])),
                'emails_sent': successful_sends,
                'email_failures': failed_sends,
                'duration_seconds': None  # Será calculado no callback
            }
            
            # Callback de sucesso
            if self.on_success_callback:
                self.on_success_callback(execution_summary)
            
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
                self.on_error_callback(execution_summary)
            
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
        
        next_run = schedule.next_run()
        if next_run:
            # Converter para timezone local
            return next_run.replace(tzinfo=pytz.UTC).astimezone(self.tz)
        
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
            'thread_alive': self.scheduler_thread.is_alive() if self.scheduler_thread else False
        }
    
    def execute_now(self) -> Dict[str, Any]:
        """
        ▶️ Executa relatórios imediatamente (para testes)
        
        Returns:
            Resultado da execução
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'Scheduler está desabilitado'
            }
        
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
        logger.info(f"📈 Execução registrada: {summary['emails_sent']} emails enviados")
    
    def _on_execution_error(self, summary: Dict[str, Any]):
        """Callback para erro na execução"""
        summary['status'] = 'error'
        self._add_to_history(summary)
        logger.error(f"📉 Erro registrado: {summary['error']}")
    
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
    manager = get_scheduler_manager()
    return manager.start()


def stop_scheduler():
    """
    🔧 Função utilitária para parar scheduler
    """
    manager = get_scheduler_manager()
    manager.stop()


def get_scheduler_status() -> Dict[str, Any]:
    """
    🔧 Função utilitária para obter status
    """
    manager = get_scheduler_manager()
    return manager.get_status()


def execute_reports_now() -> Dict[str, Any]:
    """
    🔧 Função utilitária para execução manual
    """
    manager = get_scheduler_manager()
    return manager.execute_now()