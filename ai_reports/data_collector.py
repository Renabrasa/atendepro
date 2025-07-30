# ai_reports/data_collector.py
"""
📊 Data Collector - Sistema AI Reports
Coleta e processa dados de atendimentos para análise de autonomia
"""

from datetime import datetime, timedelta
from models.models import db, User, Agente, Atendimento
from sqlalchemy import func, and_
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class AutonomyDataCollector:
   """Coleta dados de autonomia semanal para análise IA"""
   
   def __init__(self):
       self.current_date = datetime.now()
   
   def get_data_for_week_analysis(self, target_date=None):
       """
       Coleta dados completos para análise semanal de autonomia
       
       Args:
           target_date: Data específica para análise (padrão: hoje)
           
       Returns:
           dict: Dados estruturados para análise IA
       """
       if target_date is None:
           target_date = self.current_date
           
       try:
           # Calcula períodos de 7 dias (últimos vs penúltimos)
           periodo_atual, periodo_anterior = self._get_7_days_periods(target_date)
           
           # Coleta dados de todos os supervisores
           supervisors_data = self._collect_supervisors_data(periodo_atual, periodo_anterior)
           
           # Estatísticas globais
           global_stats = self._collect_global_stats(periodo_atual, periodo_anterior)
           
           return {
               'periodo_atual': {
                   'inicio': periodo_atual[0].strftime('%Y-%m-%d'),
                   'fim': periodo_atual[1].strftime('%Y-%m-%d')
               },
               'periodo_anterior': {
                   'inicio': periodo_anterior[0].strftime('%Y-%m-%d'),
                   'fim': periodo_anterior[1].strftime('%Y-%m-%d')
               },
               'supervisors': supervisors_data,
               'global_stats': global_stats,
               'total_supervisors': len(supervisors_data),
               'data_collection_timestamp': datetime.now().isoformat()
           }
           
       except Exception as e:
           logger.error(f"Erro ao coletar dados para análise: {e}")
           raise
   
   def _get_7_days_periods(self, target_date):
       """Calcula últimos 7 dias vs penúltimos 7 dias, excluindo o dia atual"""
       # Últimos 7 dias (até ontem - não incluir hoje)
       fim_atual = (target_date - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
       inicio_atual = fim_atual - timedelta(days=6)
       
       # Penúltimos 7 dias
       fim_anterior = inicio_atual - timedelta(days=1)
       inicio_anterior = fim_anterior - timedelta(days=6)
       
       return (inicio_atual, fim_atual), (inicio_anterior, fim_anterior)
   
   def _collect_supervisors_data(self, periodo_atual, periodo_anterior):
       """Coleta dados detalhados de todos os supervisores"""
       supervisors_data = []
       
       # Busca todos os supervisores ativos
       supervisors = User.query.filter(
           User.tipo.in_(['supervisor', 'coordenadora'])
       ).all()
       
       for supervisor in supervisors:
           try:
               supervisor_data = self._collect_supervisor_period_data(
                   supervisor, periodo_atual, periodo_anterior
               )
               if supervisor_data:  # Só adiciona se houver dados
                   supervisors_data.append(supervisor_data)
                   
           except Exception as e:
               logger.error(f"Erro ao processar supervisor {supervisor.nome}: {e}")
               continue
       
       return supervisors_data
   
   def _collect_supervisor_period_data(self, supervisor, periodo_atual, periodo_anterior):
       """Coleta dados detalhados de um supervisor específico"""
       
       # Atendimentos período atual
       atendimentos_atual = self._get_supervisor_attendances(supervisor.id, periodo_atual)
       
       # Atendimentos período anterior
       atendimentos_anterior = self._get_supervisor_attendances(supervisor.id, periodo_anterior)
       
       # Se não há atendimentos em nenhum período, pular
       if not atendimentos_atual and not atendimentos_anterior:
           return None
       
       # Agrupa por agente
       agents_atual = self._group_by_agent(atendimentos_atual)
       agents_anterior = self._group_by_agent(atendimentos_anterior)
       
       # Calcula dados por agente
       agents_analysis = self._calculate_agents_analysis(agents_atual, agents_anterior)
       
       # Calcula métricas do supervisor
       supervisor_metrics = self._calculate_supervisor_metrics(
           agents_analysis, len(atendimentos_atual), len(atendimentos_anterior)
       )
       
       return {
           'supervisor_id': supervisor.id,
           'supervisor_name': supervisor.nome,
           'supervisor_type': supervisor.tipo,
           'total_attendances_current': len(atendimentos_atual),
           'total_attendances_previous': len(atendimentos_anterior),
           'variation_percent': supervisor_metrics['variation_percent'],
           'autonomy_rate': supervisor_metrics['autonomy_rate'],
           'strategic_time_percent': supervisor_metrics['strategic_time_percent'],
           'agents': agents_analysis,
           'risk_classification': supervisor_metrics['risk_classification'],
           'evolution_trend': supervisor_metrics['evolution_trend']
       }
   
   def _get_supervisor_attendances(self, supervisor_id, periodo):
       """Busca atendimentos de um supervisor em período específico"""
       inicio, fim = periodo
       
       atendimentos = db.session.query(Atendimento).filter(
           and_(
               Atendimento.supervisor_id == supervisor_id,
               Atendimento.data_hora >= inicio,
               Atendimento.data_hora <= fim
           )
       ).all()
       
       return atendimentos
   
   def _group_by_agent(self, atendimentos):
    """Agrupa atendimentos por agente"""
    agents_count = defaultdict(int)
    agents_info = {}
    
    for atendimento in atendimentos:
        if atendimento.agente_id:
            agent_id = atendimento.agente_id
            agents_count[agent_id] += 1
            
            # Só busca info do agente se ainda não tiver
            if agent_id not in agents_info:
                try:
                    # Buscar agente diretamente pela query para evitar problema de relacionamento
                    from models.models import Agente
                    agente = db.session.query(Agente).filter(Agente.id == agent_id).first()
                    
                    if agente:
                        agents_info[agent_id] = {
                            'name': agente.nome,
                            'discord_id': agente.discord_id
                        }
                    else:
                        # Fallback se agente não existir
                        agents_info[agent_id] = {
                            'name': f'Agente {agent_id}',
                            'discord_id': None
                        }
                except Exception as e:
                    logger.warning(f"Erro ao buscar agente {agent_id}: {e}")
                    # Fallback em caso de erro
                    agents_info[agent_id] = {
                        'name': f'Agente {agent_id}',
                        'discord_id': None
                    }
    
    return {agent_id: {
        'count': count,
        'name': agents_info[agent_id]['name'],
        'discord_id': agents_info[agent_id]['discord_id']
    } for agent_id, count in agents_count.items() if agent_id in agents_info}
   
   def _calculate_agents_analysis(self, agents_atual, agents_anterior):
       """Calcula análise detalhada de cada agente"""
       agents_analysis = []
       
       # Combina agentes de ambos os períodos
       all_agent_ids = set(agents_atual.keys()) | set(agents_anterior.keys())
       
       for agent_id in all_agent_ids:
           current_count = agents_atual.get(agent_id, {}).get('count', 0)
           previous_count = agents_anterior.get(agent_id, {}).get('count', 0)
           
           # Informações do agente (prioriza período atual)
           agent_info = agents_atual.get(agent_id) or agents_anterior.get(agent_id)
           
           # Calcula variação
           variation = self._calculate_variation(current_count, previous_count)
           
           # Classifica risco
           risk_classification = self._classify_agent_risk(current_count, variation)
           
           # Identifica gaps prováveis
           probable_gaps = self._identify_probable_gaps(current_count, variation)
           
           agents_analysis.append({
               'agent_id': agent_id,
               'agent_name': agent_info['name'],
               'current_requests': current_count,
               'previous_requests': previous_count,
               'variation_percent': variation,
               'risk_level': risk_classification['level'],
               'risk_status': risk_classification['status'],
               'autonomy_status': risk_classification['autonomy_status'],
               'probable_gaps': probable_gaps,
               'recommended_action': risk_classification['action'],
               'is_new_agent': previous_count == 0 and current_count > 0,
               'is_improving': current_count < previous_count and previous_count > 0
           })
       
       return sorted(agents_analysis, key=lambda x: x['current_requests'], reverse=True)
   
   def _calculate_variation(self, current, previous):
       """Calcula variação percentual"""
       if previous == 0:
           return 100.0 if current > 0 else 0.0
       return round(((current - previous) / previous) * 100, 1)
   
   def _classify_agent_risk(self, current_count, variation):
       """Classifica risco do agente baseado em volume e variação"""
       
       if current_count > 6:
           return {
               'level': 'critical',
               'status': '🔴 CRÍTICO',
               'autonomy_status': 'Não consegue trabalhar sozinho',
               'action': 'Treinamento intensivo urgente'
           }
       elif current_count >= 3 and (variation > 50 or current_count >= 5):
           return {
               'level': 'attention',
               'status': '🟡 ATENÇÃO',
               'autonomy_status': 'Gap específico de conhecimento',
               'action': 'Identificar padrão e treinar pontualmente'
           }
       elif current_count <= 2:
           return {
               'level': 'autonomous',
               'status': '🟢 AUTÔNOMO',
               'autonomy_status': 'Trabalha independente',
               'action': 'Manter nível atual'
           }
       else:
           return {
               'level': 'monitor',
               'status': '🟡 MONITORAR',
               'autonomy_status': 'Situação intermediária',
               'action': 'Acompanhamento próximo'
           }
   
   def _identify_probable_gaps(self, current_count, variation):
       """Identifica prováveis gaps técnicos baseado em padrões"""
       gaps = []
       
       if current_count > 8:
           gaps.append("Deficiência geral grave - múltiplas áreas")
       elif current_count > 6:
           gaps.append("Gap em área técnica específica")
       elif variation > 100:
           gaps.append("Nova dificuldade emergente")
       elif 3 <= current_count <= 6:
           gaps.append("Dificuldade pontual específica")
       
       # Gaps específicos baseados em volume
       if current_count > 4:
           probable_areas = [
               "eSocial vs Alterdata",
               "SPED - Validação",
               "Report Builder",
               "Rotinas específicas"
           ]
           gaps.extend(probable_areas[:2])  # Adiciona as 2 áreas mais prováveis
       
       return gaps if gaps else ["Funcionamento normal"]
   
   def _calculate_supervisor_metrics(self, agents_analysis, total_atual, total_anterior):
       """Calcula métricas agregadas do supervisor"""
       
       # Taxa de autonomia (% de agentes autônomos)
       autonomous_agents = len([a for a in agents_analysis if a['risk_level'] == 'autonomous'])
       total_agents = len(agents_analysis)
       autonomy_rate = round((autonomous_agents / total_agents * 100), 1) if total_agents > 0 else 0
       
       # Variação total
       variation_percent = self._calculate_variation(total_atual, total_anterior)
       
       # Tempo estratégico (inverso do volume de atendimentos)
       # Supervisor com muitos atendimentos tem pouco tempo estratégico
       if total_atual <= 10:
           strategic_time = 85
       elif total_atual <= 20:
           strategic_time = 70
       elif total_atual <= 35:
           strategic_time = 50
       else:
           strategic_time = 25
       
       # Classificação de risco do supervisor
       critical_agents = len([a for a in agents_analysis if a['risk_level'] == 'critical'])
       if critical_agents >= 3:
           risk_classification = '🔴 CRÍTICO'
       elif critical_agents >= 1 or autonomy_rate < 60:
           risk_classification = '🟡 ATENÇÃO'
       else:
           risk_classification = '🟢 EFICIENTE'
       
       # Tendência de evolução
       if variation_percent < -15:
           evolution_trend = '📉 MELHORANDO'
       elif variation_percent > 25:
           evolution_trend = '📈 DETERIORANDO'
       else:
           evolution_trend = '📊 ESTÁVEL'
       
       return {
           'variation_percent': variation_percent,
           'autonomy_rate': autonomy_rate,
           'strategic_time_percent': strategic_time,
           'risk_classification': risk_classification,
           'evolution_trend': evolution_trend
       }
   
   def _collect_global_stats(self, periodo_atual, periodo_anterior):
       """Coleta estatísticas globais do sistema"""
       
       # Total de atendimentos
       total_atual = db.session.query(func.count(Atendimento.id)).filter(
           and_(
               Atendimento.data_hora >= periodo_atual[0],
               Atendimento.data_hora <= periodo_atual[1]
           )
       ).scalar() or 0
       
       total_anterior = db.session.query(func.count(Atendimento.id)).filter(
           and_(
               Atendimento.data_hora >= periodo_anterior[0],
               Atendimento.data_hora <= periodo_anterior[1]
           )
       ).scalar() or 0
       
       # Agentes únicos ativos
       agentes_ativos = db.session.query(func.count(func.distinct(Atendimento.agente_id))).filter(
           and_(
               Atendimento.data_hora >= periodo_atual[0],
               Atendimento.data_hora <= periodo_atual[1]
           )
       ).scalar() or 0
       
       return {
           'total_attendances_current': total_atual,
           'total_attendances_previous': total_anterior,
           'variation_percent': self._calculate_variation(total_atual, total_anterior),
           'active_agents': agentes_ativos,
           'average_requests_per_agent': round(total_atual / agentes_ativos, 1) if agentes_ativos > 0 else 0
       }

# Função auxiliar para facilitar uso
def collect_autonomy_data(target_date=None):
   """
   Função helper para coletar dados de autonomia
   
   Usage:
       from ai_reports.data_collector import collect_autonomy_data
       data = collect_autonomy_data()
   """
   collector = AutonomyDataCollector()
   return collector.get_data_for_week_analysis(target_date)

if __name__ == "__main__":
   # Teste rápido
   print("🧪 Testando Data Collector...")
   try:
       data = collect_autonomy_data()
       print(f"✅ Dados coletados: {len(data['supervisors'])} supervisores")
       print(f"📊 Total atendimentos: {data['global_stats']['total_attendances_current']}")
       print(f"📅 Período atual: {data['periodo_atual']['inicio']} - {data['periodo_atual']['fim']}")
       print(f"📅 Período anterior: {data['periodo_anterior']['inicio']} - {data['periodo_anterior']['fim']}")
   except Exception as e:
       print(f"❌ Erro: {e}")