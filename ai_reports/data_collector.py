# ai_reports/data_collector.py
"""
🔍 Módulo de Coleta de Dados para AI Reports
Extrai dados do banco AtendePro para análise da IA
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc
from typing import Dict, List, Any, Tuple, Optional
import logging

# Importar modelos do sistema principal
from models.models import db, User, Agente, Atendimento, Equipe
from config import Config

# Configurar logging
logger = logging.getLogger(__name__)


class DataCollector:
    """
    🔍 Coletor de dados para relatórios AI
    
    Responsável por extrair dados estruturados do banco de dados
    para alimentar a análise da IA
    """
    
    def __init__(self):
        """Inicializa o coletor de dados"""
        self.debug = Config.AI_REPORTS_DEBUG
        if self.debug:
            logger.info("🔍 DataCollector inicializado em modo DEBUG")
    
    def get_data_for_week_analysis(self, target_date: datetime = None) -> Dict[str, Any]:
        """
        📊 Coleta dados completos para análise semanal
        
        Args:
            target_date: Data de referência (padrão: hoje)
            
        Returns:
            Dict com dados estruturados para análise IA
        """
        if target_date is None:
            target_date = datetime.now()
        
        try:
            # Definir períodos da semana atual e anterior
            current_week_start, current_week_end = self._get_week_boundaries(target_date)
            previous_week_start = current_week_start - timedelta(days=7)
            previous_week_end = current_week_start - timedelta(seconds=1)
            
            if self.debug:
                logger.info(f"📅 Analisando semana: {current_week_start.strftime('%d/%m')} até {current_week_end.strftime('%d/%m')}")
                logger.info(f"📅 Comparando com: {previous_week_start.strftime('%d/%m')} até {previous_week_end.strftime('%d/%m')}")
            
            # Coletar dados por supervisor
            supervisors_data = self._collect_supervisors_data(
                current_week_start, current_week_end,
                previous_week_start, previous_week_end
            )
            
            # Coletar dados globais
            global_stats = self._collect_global_stats(
                current_week_start, current_week_end,
                previous_week_start, previous_week_end
            )
            
            # Estruturar dados finais
            analysis_data = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'target_date': target_date.isoformat(),
                    'current_week': {
                        'start': current_week_start.isoformat(),
                        'end': current_week_end.isoformat(),
                        'period_label': f"{current_week_start.strftime('%d/%m')} a {current_week_end.strftime('%d/%m')}"
                    },
                    'previous_week': {
                        'start': previous_week_start.isoformat(),
                        'end': previous_week_end.isoformat(),
                        'period_label': f"{previous_week_start.strftime('%d/%m')} a {previous_week_end.strftime('%d/%m')}"
                    }
                },
                'supervisors_data': supervisors_data,
                'global_stats': global_stats
            }
            
            if self.debug:
                logger.info(f"✅ Dados coletados: {len(supervisors_data)} supervisores, {global_stats['current_week']['total_tickets']} atendimentos")
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"❌ Erro na coleta de dados: {e}")
            raise
    
    def _get_week_boundaries(self, target_date: datetime) -> Tuple[datetime, datetime]:
        """
        📅 Calcula início e fim da semana (Segunda a Domingo)
        
        Args:
            target_date: Data de referência
            
        Returns:
            Tuple com (início_semana, fim_semana)
        """
        # Calcular início da semana (segunda-feira)
        days_since_monday = target_date.weekday()  # 0=segunda, 6=domingo
        week_start = target_date - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calcular fim da semana (domingo)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        return week_start, week_end
    
    def _collect_supervisors_data(self, current_start: datetime, current_end: datetime,
                                 previous_start: datetime, previous_end: datetime) -> List[Dict[str, Any]]:
        """
        👥 Coleta dados de todos os supervisores
        
        Returns:
            Lista com dados de cada supervisor
        """
        supervisors_data = []
        
        # Buscar todos os supervisores ativos
        supervisors = User.query.filter_by(tipo='supervisor').all()
        
        for supervisor in supervisors:
            try:
                supervisor_data = self._collect_single_supervisor_data(
                    supervisor, current_start, current_end, previous_start, previous_end
                )
                supervisors_data.append(supervisor_data)
                
            except Exception as e:
                logger.error(f"❌ Erro ao coletar dados do supervisor {supervisor.nome}: {e}")
                # Continuar com outros supervisores mesmo se um falhar
                continue
        
        # Ordenar por total de atendimentos (decrescente)
        supervisors_data.sort(key=lambda x: x['current_week']['total_tickets'], reverse=True)
        
        return supervisors_data
    
    def _collect_single_supervisor_data(self, supervisor: User, current_start: datetime, current_end: datetime,
                                       previous_start: datetime, previous_end: datetime) -> Dict[str, Any]:
        """
        👤 Coleta dados de um supervisor específico
        
        Args:
            supervisor: Objeto User do supervisor
            current_start, current_end: Período da semana atual
            previous_start, previous_end: Período da semana anterior
            
        Returns:
            Dict com dados do supervisor
        """
        # Atendimentos da semana atual
        current_tickets = Atendimento.query.filter(
            and_(
                Atendimento.supervisor_id == supervisor.id,
                Atendimento.data_hora >= current_start,
                Atendimento.data_hora <= current_end
            )
        ).all()
        
        # Atendimentos da semana anterior
        previous_tickets = Atendimento.query.filter(
            and_(
                Atendimento.supervisor_id == supervisor.id,
                Atendimento.data_hora >= previous_start,
                Atendimento.data_hora <= previous_end
            )
        ).count()
        
        # Analisar agentes da semana atual
        agents_analysis = self._analyze_supervisor_agents(supervisor, current_tickets)
        
        # Calcular métricas
        current_total = len(current_tickets)
        change = current_total - previous_tickets
        change_percent = ((change / previous_tickets) * 100) if previous_tickets > 0 else 0
        
        # Identificar padrões
        patterns = self._identify_patterns(current_tickets, previous_tickets, agents_analysis)
        
        supervisor_data = {
            'supervisor': {
                'id': supervisor.id,
                'name': supervisor.nome,
                'email': supervisor.email
            },
            'current_week': {
                'total_tickets': current_total,
                'tickets_by_day': self._group_by_day(current_tickets),
                'agents_performance': agents_analysis
            },
            'previous_week': {
                'total_tickets': previous_tickets
            },
            'comparison': {
                'absolute_change': change,
                'percent_change': round(change_percent, 1),
                'trend': 'increase' if change > 0 else 'decrease' if change < 0 else 'stable'
            },
            'insights': patterns
        }
        
        if self.debug:
            logger.info(f"👤 {supervisor.nome}: {current_total} atendimentos ({change:+d} vs anterior)")
        
        return supervisor_data
    
    def _analyze_supervisor_agents(self, supervisor: User, tickets: List[Atendimento]) -> List[Dict[str, Any]]:
        """
        🧑‍💼 Analisa performance dos agentes de um supervisor
        
        Args:
            supervisor: Supervisor a analisar
            tickets: Lista de atendimentos da semana
            
        Returns:
            Lista com dados de cada agente
        """
        # Agrupar atendimentos por agente
        agents_tickets = {}
        for ticket in tickets:
            agent_id = ticket.agente_id
            if agent_id not in agents_tickets:
                agents_tickets[agent_id] = []
            agents_tickets[agent_id].append(ticket)
        
        # Buscar dados dos agentes
        agents_analysis = []
        
        for agent_id, agent_tickets in agents_tickets.items():
            agent = Agente.query.get(agent_id)
            if not agent:
                continue
            
            # Contar atendimentos semana anterior para comparação
            previous_count = self._get_agent_previous_week_count(agent_id, supervisor.id)
            
            current_count = len(agent_tickets)
            change = current_count - previous_count
            
            agent_data = {
                'agent': {
                    'id': agent.id,
                    'name': agent.nome,
                    'discord_id': agent.discord_id,
                    'active': agent.ativo
                },
                'current_tickets': current_count,
                'previous_tickets': previous_count,
                'change': change,
                'tickets_by_day': self._group_by_day(agent_tickets)
            }
            
            agents_analysis.append(agent_data)
        
        # Ordenar por número de atendimentos (decrescente)
        agents_analysis.sort(key=lambda x: x['current_tickets'], reverse=True)
        
        return agents_analysis
    
    def _get_agent_previous_week_count(self, agent_id: int, supervisor_id: int) -> int:
        """
        📊 Conta atendimentos do agente na semana anterior
        
        Args:
            agent_id: ID do agente
            supervisor_id: ID do supervisor
            
        Returns:
            Número de atendimentos na semana anterior
        """
        # Calcular semana anterior
        target_date = datetime.now() - timedelta(days=7)
        prev_start, prev_end = self._get_week_boundaries(target_date)
        
        count = Atendimento.query.filter(
            and_(
                Atendimento.agente_id == agent_id,
                Atendimento.supervisor_id == supervisor_id,
                Atendimento.data_hora >= prev_start,
                Atendimento.data_hora <= prev_end
            )
        ).count()
        
        return count
    
    def _group_by_day(self, tickets: List[Atendimento]) -> Dict[str, int]:
        """
        📊 Agrupa atendimentos por dia da semana
        
        Args:
            tickets: Lista de atendimentos
            
        Returns:
            Dict com contagem por dia
        """
        days_count = {
            'Monday': 0, 'Tuesday': 0, 'Wednesday': 0, 'Thursday': 0,
            'Friday': 0, 'Saturday': 0, 'Sunday': 0
        }
        
        for ticket in tickets:
            day_name = ticket.data_hora.strftime('%A')
            if day_name in days_count:
                days_count[day_name] += 1
        
        return days_count
    
    def _identify_patterns(self, current_tickets: List[Atendimento], previous_count: int,
                          agents_analysis: List[Dict]) -> List[str]:
        """
        🔍 Identifica padrões interessantes nos dados
        
        Args:
            current_tickets: Atendimentos da semana atual
            previous_count: Total da semana anterior
            agents_analysis: Análise dos agentes
            
        Returns:
            Lista de insights identificados
        """
        insights = []
        current_count = len(current_tickets)
        
        # Variação significativa
        if previous_count > 0:
            change_percent = ((current_count - previous_count) / previous_count) * 100
            if abs(change_percent) >= 30:
                if change_percent > 0:
                    insights.append(f"Aumento significativo de {change_percent:.1f}% nos atendimentos")
                else:
                    insights.append(f"Redução significativa de {abs(change_percent):.1f}% nos atendimentos")
        
        # Concentração em poucos agentes
        if len(agents_analysis) > 1:
            total_tickets = sum(agent['current_tickets'] for agent in agents_analysis)
            if total_tickets > 0:
                top_agent_percent = (agents_analysis[0]['current_tickets'] / total_tickets) * 100
                if top_agent_percent >= 60:
                    insights.append(f"Concentração alta: {agents_analysis[0]['agent']['name']} responsável por {top_agent_percent:.1f}% dos atendimentos")
        
        # Agentes com mudanças atípicas
        for agent in agents_analysis:
            if agent['previous_tickets'] > 0:
                agent_change_percent = ((agent['change'] / agent['previous_tickets']) * 100)
                if agent_change_percent >= 50:
                    insights.append(f"{agent['agent']['name']}: aumento atípico de {agent_change_percent:.1f}%")
                elif agent_change_percent <= -50:
                    insights.append(f"{agent['agent']['name']}: redução atípica de {abs(agent_change_percent):.1f}%")
        
        return insights
    
    def _collect_global_stats(self, current_start: datetime, current_end: datetime,
                             previous_start: datetime, previous_end: datetime) -> Dict[str, Any]:
        """
        🌍 Coleta estatísticas globais do sistema
        
        Returns:
            Dict com estatísticas gerais
        """
        # Atendimentos globais
        current_total = Atendimento.query.filter(
            and_(
                Atendimento.data_hora >= current_start,
                Atendimento.data_hora <= current_end
            )
        ).count()
        
        previous_total = Atendimento.query.filter(
            and_(
                Atendimento.data_hora >= previous_start,
                Atendimento.data_hora <= previous_end
            )
        ).count()
        
        # Supervisores ativos
        active_supervisors = User.query.filter_by(tipo='supervisor').count()
        
        # Agentes ativos
        active_agents = Agente.query.filter_by(ativo=True).count()
        
        # Top supervisor da semana
        top_supervisor_data = db.session.query(
            User.nome,
            func.count(Atendimento.id).label('ticket_count')
        ).join(
            Atendimento, User.id == Atendimento.supervisor_id
        ).filter(
            and_(
                Atendimento.data_hora >= current_start,
                Atendimento.data_hora <= current_end
            )
        ).group_by(User.id, User.nome).order_by(desc('ticket_count')).first()
        
        top_supervisor = {
            'name': top_supervisor_data.nome if top_supervisor_data else 'N/A',
            'tickets': top_supervisor_data.ticket_count if top_supervisor_data else 0
        }
        
        global_change = current_total - previous_total
        global_change_percent = ((global_change / previous_total) * 100) if previous_total > 0 else 0
        
        return {
            'current_week': {
                'total_tickets': current_total,
                'active_supervisors': active_supervisors,
                'active_agents': active_agents,
                'top_supervisor': top_supervisor
            },
            'previous_week': {
                'total_tickets': previous_total
            },
            'comparison': {
                'absolute_change': global_change,
                'percent_change': round(global_change_percent, 1),
                'trend': 'increase' if global_change > 0 else 'decrease' if global_change < 0 else 'stable'
            }
        }
    
    def test_data_collection(self) -> Dict[str, Any]:
        """
        🧪 Testa a coleta de dados com informações básicas
        
        Returns:
            Dict com resultado do teste
        """
        try:
            logger.info("🧪 Iniciando teste de coleta de dados...")
            
            # Contar registros básicos
            total_users = User.query.count()
            total_agents = Agente.query.count()
            total_tickets = Atendimento.query.count()
            supervisors = User.query.filter_by(tipo='supervisor').count()
            
            # Teste de coleta semanal (só metadata)
            current_week_start, current_week_end = self._get_week_boundaries(datetime.now())
            
            weekly_tickets = Atendimento.query.filter(
                and_(
                    Atendimento.data_hora >= current_week_start,
                    Atendimento.data_hora <= current_week_end
                )
            ).count()
            
            test_result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'basic_counts': {
                    'total_users': total_users,
                    'total_agents': total_agents,
                    'total_tickets': total_tickets,
                    'supervisors': supervisors
                },
                'current_week': {
                    'period': f"{current_week_start.strftime('%d/%m')} a {current_week_end.strftime('%d/%m')}",
                    'tickets': weekly_tickets
                },
                'database_status': 'Connected and accessible'
            }
            
            logger.info(f"✅ Teste concluído: {supervisors} supervisores, {weekly_tickets} atendimentos esta semana")
            return test_result
            
        except Exception as e:
            logger.error(f"❌ Erro no teste de coleta: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Função de conveniência para uso externo
def collect_weekly_data(target_date: datetime = None) -> Dict[str, Any]:
    """
    🔧 Função utilitária para coletar dados semanais
    
    Args:
        target_date: Data de referência (padrão: hoje)
        
    Returns:
        Dados estruturados para análise IA
    """
    collector = DataCollector()
    return collector.get_data_for_week_analysis(target_date)


def test_data_collection() -> Dict[str, Any]:
    """
    🧪 Função utilitária para testar coleta de dados
    
    Returns:
        Resultado do teste
    """
    collector = DataCollector()
    return collector.test_data_collection()