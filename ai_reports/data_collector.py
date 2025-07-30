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
    para alimentar a análise da IA com base nos últimos 15 dias
    """
    
    def __init__(self):
        """Inicializa o coletor de dados"""
        self.debug = Config.AI_REPORTS_DEBUG
        if self.debug:
            logger.info("🔍 DataCollector inicializado em modo DEBUG")
    
    def get_data_for_week_analysis(self, target_date: datetime = None) -> Dict[str, Any]:
        """
        📊 Coleta dados completos para análise dos últimos 15 dias
        
        Args:
            target_date: Data de referência (padrão: hoje)
            
        Returns:
            Dict com dados estruturados para análise IA
        """
        if target_date is None:
            target_date = datetime.now()
        
        try:
            # Nova lógica: últimos 15 dias divididos em 2 períodos de 7 dias cada
            current_period_start, current_period_end, previous_period_start, previous_period_end = self._get_15_days_periods(target_date)
            
            if self.debug:
                logger.info(f"📅 Período atual: {current_period_start.strftime('%d/%m')} até {current_period_end.strftime('%d/%m')}")
                logger.info(f"📅 Período anterior: {previous_period_start.strftime('%d/%m')} até {previous_period_end.strftime('%d/%m')}")
                logger.info(f"📅 Total: 15 dias de análise completa")
            
            # Coletar dados por supervisor
            supervisors_data = self._collect_supervisors_data(
                current_period_start, current_period_end,
                previous_period_start, previous_period_end
            )
            
            # Coletar dados globais
            global_stats = self._collect_global_stats(
                current_period_start, current_period_end,
                previous_period_start, previous_period_end
            )
            
            # NOVO: Gerar insights inteligentes baseados nos dados coletados
            intelligent_insights = self._generate_intelligent_insights(supervisors_data)
            
            # NOVO: Criar dashboard executivo para substituir análise IA problemática
            executive_dashboard = self._create_executive_dashboard(global_stats, intelligent_insights)
            
            # Estruturar dados finais
            analysis_data = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'target_date': target_date.isoformat(),
                    'analysis_type': '15_days_comparison',
                    'current_week': {
                        'start': current_period_start.isoformat(),
                        'end': current_period_end.isoformat(),
                        'period_label': f"{current_period_start.strftime('%d/%m')} a {current_period_end.strftime('%d/%m')}"
                    },
                    'previous_week': {
                        'start': previous_period_start.isoformat(),
                        'end': previous_period_end.isoformat(),
                        'period_label': f"{previous_period_start.strftime('%d/%m')} a {previous_period_end.strftime('%d/%m')}"
                    },
                    'total_analysis_period': {
                        'start': previous_period_start.isoformat(),
                        'end': current_period_end.isoformat(),
                        'period_label': f"Análise: {previous_period_start.strftime('%d/%m')} a {current_period_end.strftime('%d/%m')} (15 dias)",
                        'days_analyzed': 15
                    }
                },
                'supervisors_data': supervisors_data,
                'global_stats': global_stats,
                # NOVOS: Campos adicionados conforme o plano de implementação
                'intelligent_insights': intelligent_insights,
                'executive_dashboard': executive_dashboard
            }
            
            if self.debug:
                logger.info(f"✅ Dados coletados: {len(supervisors_data)} supervisores, {global_stats['current_week']['total_tickets']} atendimentos no período atual")
                logger.info(f"🧠 Insights gerados: {len(intelligent_insights['performance_alerts'])} alertas, {len(intelligent_insights['concentration_patterns'])} padrões")
                logger.info(f"📊 Dashboard executivo: {executive_dashboard['total_tickets']} atendimentos, {executive_dashboard['supervisor_count']} supervisores")
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"❌ Erro na coleta de dados: {e}")
            raise
    
    def _get_15_days_periods(self, target_date: datetime) -> Tuple[datetime, datetime, datetime, datetime]:
        """
        📅 Calcula os últimos 15 dias divididos em 2 períodos para comparação
        
        Args:
            target_date: Data de referência (hoje)
            
        Returns:
            Tuple com (atual_inicio, atual_fim, anterior_inicio, anterior_fim)
        """
        reference_date = target_date - timedelta(days=1)
        end_date = reference_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Período atual: 7 dias até ontem
        current_period_end = end_date
        current_period_start = (end_date - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Período anterior: 7 dias antes do período atual
        previous_period_end = (current_period_start - timedelta(seconds=1))
        previous_period_start = (previous_period_end - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        return current_period_start, current_period_end, previous_period_start, previous_period_end
        
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
            current_start, current_end: Período atual (últimos 7 dias)
            previous_start, previous_end: Período anterior (7 dias anteriores)
            
        Returns:
            Dict com dados do supervisor
        """
        # Atendimentos do período atual
        current_tickets = Atendimento.query.filter(
            and_(
                Atendimento.supervisor_id == supervisor.id,
                Atendimento.data_hora >= current_start,
                Atendimento.data_hora <= current_end
            )
        ).all()
        
        # Atendimentos do período anterior
        previous_tickets = Atendimento.query.filter(
            and_(
                Atendimento.supervisor_id == supervisor.id,
                Atendimento.data_hora >= previous_start,
                Atendimento.data_hora <= previous_end
            )
        ).count()
        
        # Analisar agentes do período atual
        agents_analysis = self._analyze_supervisor_agents(supervisor, current_tickets, previous_start, previous_end)
        
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
                'agents_performance': agents_analysis,
                'period_label': f"{current_start.strftime('%d/%m')} a {current_end.strftime('%d/%m')}"
            },
            'previous_week': {
                'total_tickets': previous_tickets,
                'period_label': f"{previous_start.strftime('%d/%m')} a {previous_end.strftime('%d/%m')}"
            },
            'comparison': {
                'absolute_change': change,
                'percent_change': round(change_percent, 1),
                'trend': 'increase' if change > 0 else 'decrease' if change < 0 else 'stable'
            },
            'insights': patterns
        }
        
        if self.debug:
            logger.info(f"👤 {supervisor.nome}: {current_total} atendimentos ({change:+d} vs período anterior)")
        
        return supervisor_data
    
    def _analyze_supervisor_agents(self, supervisor: User, tickets: List[Atendimento], 
                                  previous_start: datetime, previous_end: datetime) -> List[Dict[str, Any]]:
        """
        🧑‍💼 Analisa performance dos agentes de um supervisor
        
        Args:
            supervisor: Supervisor a analisar
            tickets: Lista de atendimentos do período atual
            previous_start, previous_end: Período anterior para comparação
            
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
            
            # Contar atendimentos do período anterior para comparação
            previous_count = Atendimento.query.filter(
                and_(
                    Atendimento.agente_id == agent_id,
                    Atendimento.supervisor_id == supervisor.id,
                    Atendimento.data_hora >= previous_start,
                    Atendimento.data_hora <= previous_end
                )
            ).count()
            
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
        🔍 Identifica padrões interessantes nos dados dos últimos 15 dias
        
        Args:
            current_tickets: Atendimentos do período atual
            previous_count: Total do período anterior
            agents_analysis: Análise dos agentes
            
        Returns:
            Lista de insights identificados
        """
        insights = []
        current_count = len(current_tickets)
        
        # Variação significativa entre períodos
        if previous_count > 0:
            change_percent = ((current_count - previous_count) / previous_count) * 100
            if abs(change_percent) >= 25:
                if change_percent > 0:
                    insights.append(f"Crescimento de {change_percent:.1f}% nos últimos 7 dias comparado aos 7 anteriores")
                else:
                    insights.append(f"Redução de {abs(change_percent):.1f}% nos últimos 7 dias comparado aos 7 anteriores")
        
        # Concentração em poucos agentes
        if len(agents_analysis) > 1:
            total_tickets = sum(agent['current_tickets'] for agent in agents_analysis)
            if total_tickets > 0:
                top_agent_percent = (agents_analysis[0]['current_tickets'] / total_tickets) * 100
                if top_agent_percent >= 50:
                    insights.append(f"Concentração: {agents_analysis[0]['agent']['name']} responsável por {top_agent_percent:.1f}% dos atendimentos")
        
        # Agentes com mudanças atípicas
        for agent in agents_analysis:
            if agent['previous_tickets'] > 0:
                agent_change_percent = ((agent['change'] / agent['previous_tickets']) * 100)
                if agent_change_percent >= 40:
                    insights.append(f"{agent['agent']['name']}: aumento de {agent_change_percent:.1f}% nos últimos 7 dias")
                elif agent_change_percent <= -40:
                    insights.append(f"{agent['agent']['name']}: redução de {abs(agent_change_percent):.1f}% nos últimos 7 dias")
        
        # Insights sobre volume total
        if current_count >= 50:
            insights.append(f"Alto volume: {current_count} atendimentos nos últimos 7 dias")
        elif current_count <= 5 and previous_count > 10:
            insights.append(f"Volume baixo: apenas {current_count} atendimentos nos últimos 7 dias")
        
        return insights
    
    def _collect_global_stats(self, current_start: datetime, current_end: datetime,
                             previous_start: datetime, previous_end: datetime) -> Dict[str, Any]:
        """
        🌍 Coleta estatísticas globais do sistema para os últimos 15 dias
        
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
        
        # Top supervisor do período atual
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
                'top_supervisor': top_supervisor,
                'period_label': f"{current_start.strftime('%d/%m')} a {current_end.strftime('%d/%m')}"
            },
            'previous_week': {
                'total_tickets': previous_total,
                'period_label': f"{previous_start.strftime('%d/%m')} a {previous_end.strftime('%d/%m')}"
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
            logger.info("🧪 Iniciando teste de coleta de dados (15 dias)...")
            
            # Contar registros básicos
            total_users = User.query.count()
            total_agents = Agente.query.count()
            total_tickets = Atendimento.query.count()
            supervisors = User.query.filter_by(tipo='supervisor').count()
            
            # Teste de coleta dos últimos 15 dias
            current_start, current_end, previous_start, previous_end = self._get_15_days_periods(datetime.now())
            
            current_tickets = Atendimento.query.filter(
                and_(
                    Atendimento.data_hora >= current_start,
                    Atendimento.data_hora <= current_end
                )
            ).count()
            
            previous_tickets = Atendimento.query.filter(
                and_(
                    Atendimento.data_hora >= previous_start,
                    Atendimento.data_hora <= previous_end
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
                'analysis_periods': {
                    'current_period': {
                        'period': f"{current_start.strftime('%d/%m')} a {current_end.strftime('%d/%m')}",
                        'tickets': current_tickets
                    },
                    'previous_period': {
                        'period': f"{previous_start.strftime('%d/%m')} a {previous_end.strftime('%d/%m')}",
                        'tickets': previous_tickets
                    },
                    'total_days_analyzed': 15
                },
                'database_status': 'Connected and accessible'
            }
            
            logger.info(f"✅ Teste concluído: {supervisors} supervisores, {current_tickets + previous_tickets} atendimentos nos últimos 15 dias")
            return test_result
            
        except Exception as e:
            logger.error(f"❌ Erro no teste de coleta: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    # ADICIONAR no final da classe DataCollector:

    def _generate_intelligent_insights(self, supervisors_data: List[Dict]) -> Dict[str, Any]:
        """Gera insights automáticos baseados em padrões reais"""
        insights = {
            'performance_alerts': [],
            'concentration_patterns': [],
            'recommendations': [],
            'ranking_summary': []
        }
        
        # Detectar supervisores com variação significativa
        for sup_data in supervisors_data:
            name = sup_data['supervisor']['name']
            change_percent = sup_data['comparison']['percent_change']
            current_tickets = sup_data['current_week']['total_tickets']
            
            if abs(change_percent) >= 25:
                insights['performance_alerts'].append(
                    f"{name}: {change_percent:+.1f}% - requer atenção"
                )
            
            # Analisar concentração de agentes
            agents = sup_data['current_week']['agents_performance']
            if agents and current_tickets > 0:
                top_agent = max(agents, key=lambda x: x['current_tickets'])
                concentration = (top_agent['current_tickets'] / current_tickets) * 100
                
                if concentration >= 35:
                    insights['concentration_patterns'].append(
                        f"{name}: {top_agent['agent']['name']} concentra {concentration:.0f}% dos casos"
                    )
        
        # Gerar ranking automaticamente
        sorted_supervisors = sorted(supervisors_data, 
                                key=lambda x: x['current_week']['total_tickets'], 
                                reverse=True)
        
        for i, sup in enumerate(sorted_supervisors[:3], 1):
            change = sup['comparison']['absolute_change']
            insights['ranking_summary'].append(
                f"{i}º {sup['supervisor']['name']}: {sup['current_week']['total_tickets']} ({change:+d})"
            )
        
        return insights

    def _create_executive_dashboard(self, global_stats: Dict, insights: Dict) -> Dict[str, Any]:
        """Cria dashboard executivo para substituir análise IA"""
        return {
            'total_tickets': global_stats['current_week']['total_tickets'],
            'variation': global_stats['comparison']['absolute_change'],
            'variation_percent': global_stats['comparison']['percent_change'],
            'supervisor_count': global_stats['current_week']['active_supervisors'],
            'ranking': insights['ranking_summary'],
            'alerts': insights['performance_alerts'],
            'patterns': insights['concentration_patterns'],
            'recommendations': insights['recommendations']
        }

# Função de conveniência para uso externo
def collect_weekly_data(target_date: datetime = None) -> Dict[str, Any]:
    """
    🔧 Função utilitária para coletar dados dos últimos 15 dias
    
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