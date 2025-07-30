# ai_reports/ai_prompts.py
"""
🔤 AI Prompts - Prompts Estruturados para Análise IA
Coleção de prompts especializados para diferentes tipos de análise
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class PromptBuilder:
    """
    🔤 Construtor de prompts especializados para análise IA
    
    Gera prompts para análise de produtividade e demanda de atendimentos em contabilidade
    """
    
    @staticmethod
    def global_trend_analysis(global_stats: Dict[str, Any], weekly_data: Dict[str, Any]) -> str:
        """
        🌍 Prompt para análise de tendências globais
        """
        current_tickets = global_stats['current_week']['total_tickets']
        previous_tickets = global_stats['previous_week']['total_tickets']
        change = global_stats['comparison']['absolute_change']
        change_percent = global_stats['comparison']['percent_change']
        active_supervisors = global_stats['current_week']['active_supervisors']
        period = weekly_data['metadata']['current_week']['period_label']
        
        prompt = f"""
Você é um analista de produtividade de empresa de contabilidade.

DADOS REAIS DO SISTEMA:
- Período atual: {period}
- Total de atendimentos prestados por supervisores: {current_tickets}
- Período anterior: {previous_tickets} atendimentos
- Variação real: {change:+d} atendimentos ({change_percent:+.1f}%)
- Supervisores ativos: {active_supervisors}

CONTEXTO:
- Cada atendimento = supervisor ajudou agente/funcionário com caso complexo
- Aumento = agentes precisaram mais suporte (possível sobrecarga ou casos complexos)
- Redução = agentes mais autônomos ou menor demanda de clientes

ANÁLISE SOLICITADA:

1. INTERPRETAÇÃO DOS NÚMEROS REAIS
   - {change_percent:+.1f}% significa que supervisores prestaram {change:+d} atendimentos a mais/menos
   - Indica maior/menor dependência dos agentes?

2. POSSÍVEIS CAUSAS OPERACIONAIS
   - Se aumentou: agentes com dificuldades ou casos mais complexos?
   - Se reduziu: agentes mais capacitados ou menor demanda?

3. IMPACTO NA PRODUTIVIDADE
   - Como isso afeta a eficiência geral da contabilidade?
   - Supervisores sobrecarregados ou com capacidade ociosa?

4. RECOMENDAÇÕES PRÁTICAS
   - Ações para otimizar a demanda de atendimentos
   - Como equilibrar autonomia vs suporte necessário

REGRAS: Use APENAS os números fornecidos. Máximo 120 palavras. Foque em produtividade da contabilidade.
"""
        return prompt.strip()
    
    @staticmethod
    def supervisor_performance_analysis(supervisor_data: Dict[str, Any], 
                                       weekly_data: Dict[str, Any],
                                       ranking_position: Optional[int] = None) -> str:
        """
        👤 Prompt para análise de performance de supervisor
        """
        supervisor = supervisor_data['supervisor']['name']
        current = supervisor_data['current_week']['total_tickets']
        previous = supervisor_data['previous_week']['total_tickets']
        change = supervisor_data['comparison']['absolute_change']
        change_percent = supervisor_data['comparison']['percent_change']
        
        agents = supervisor_data['current_week']['agents_performance']
        agents_count = len(agents)
        
        ranking_text = f"(#{ranking_position} no ranking)" if ranking_position else ""
        
        prompt = f"""
Você é um gestor de contabilidade analisando produtividade individual.

DADOS REAIS DO SUPERVISOR {supervisor} {ranking_text}:
- Período: {weekly_data['metadata']['current_week']['period_label']}
- Atendimentos prestados agora: {current}
- Atendimentos prestados antes: {previous}
- Variação real: {change:+d} atendimentos ({change_percent:+.1f}%)
- Agentes/funcionários atendidos: {agents_count}

DETALHAMENTO POR AGENTE (quem mais solicitou atendimento):
"""
        
        # Adicionar dados dos agentes com foco em variação individual
        for i, agent in enumerate(agents[:5], 1):
            agent_name = agent['agent']['name']
            current_requests = agent['current_tickets']
            previous_requests = agent['previous_tickets']
            agent_change = agent['change']
            
            # Calcular porcentagem individual
            if previous_requests > 0:
                agent_percent = (agent_change / previous_requests) * 100
                prompt += f"• {agent_name}: {current_requests} atendimentos (anterior: {previous_requests}) = {agent_change:+d} ({agent_percent:+.1f}%)\n"
            else:
                prompt += f"• {agent_name}: {current_requests} atendimentos (anterior: {previous_requests}) = {agent_change:+d}\n"
        
        prompt += f"""
ANÁLISE INDIVIDUAL SOLICITADA:

1. PERFORMANCE DO SUPERVISOR {supervisor}
   - {current} atendimentos prestados representa sobrecarga ou demanda normal?
   - Variação de {change_percent:+.1f}% indica que agentes precisaram mais/menos suporte

2. ANÁLISE POR AGENTE (foque nos números acima)
   - Qual agente mais solicitou atendimento e por quê?
   - Quais agentes tiveram maior variação percentual?
   - Algum agente demonstra necessidade de treinamento urgente?

3. IDENTIFICAÇÃO DE PADRÕES
   - Agentes com aumento >30%: precisam capacitação?
   - Agentes com redução >30%: estão mais autônomos ou ociosos?
   - Distribuição equilibrada entre a equipe?

4. RECOMENDAÇÕES ESPECÍFICAS
   - Quais agentes treinar prioritariamente?
   - Como redistribuir demanda entre agentes?
   - Ações para próxima semana

REGRAS: Use APENAS os números reais fornecidos. Cite nomes dos agentes. Máximo 110 palavras.
"""
        return prompt.strip()
    
    @staticmethod
    def strategic_recommendations(weekly_data: Dict[str, Any]) -> str:
        """
        🎯 Prompt para recomendações estratégicas
        """
        supervisors = weekly_data['supervisors_data']
        global_stats = weekly_data['global_stats']
        
        # Análise dos supervisores
        total_supervisors = len(supervisors)
        overloaded = [s for s in supervisors if s['current_week']['total_tickets'] >= 50]
        high_demand_increase = [s for s in supervisors if s['comparison']['percent_change'] >= 25]
        demand_decrease = [s for s in supervisors if s['comparison']['percent_change'] <= -25]
        
        # Top supervisor por volume
        top_supervisor = max(supervisors, key=lambda x: x['current_week']['total_tickets']) if supervisors else None
        
        prompt = f"""
Você é diretor de contabilidade preparando relatório para diretoria.

DADOS EXECUTIVOS REAIS:
- Período: {weekly_data['metadata']['current_week']['period_label']}
- Total de atendimentos prestados por supervisores: {global_stats['current_week']['total_tickets']}
- Variação geral: {global_stats['comparison']['absolute_change']:+d} ({global_stats['comparison']['percent_change']:+.1f}%)
- Supervisores monitorados: {total_supervisors}

DISTRIBUIÇÃO DE CARGA ATUAL:
- Supervisores com alta demanda (≥50 atendimentos): {len(overloaded)}
- Supervisores com aumento significativo (+25%): {len(high_demand_increase)}
- Supervisores com redução significativa (-25%): {len(demand_decrease)}
"""
        
        if top_supervisor:
            top_change = top_supervisor['comparison']['absolute_change']
            top_percent = top_supervisor['comparison']['percent_change']
            prompt += f"• Maior volume: {top_supervisor['supervisor']['name']} prestou {top_supervisor['current_week']['total_tickets']} atendimentos ({top_change:+d}, {top_percent:+.1f}%)\n"
        
        prompt += f"""
RECOMENDAÇÕES ESTRATÉGICAS PARA DIRETORIA:

1. GESTÃO DE PRODUTIVIDADE
   - Como balancear demanda de atendimentos entre supervisores?
   - Redistribuição de agentes entre equipes sobrecarregadas?

2. CAPACITAÇÃO URGENTE
   - Agentes que mais demandam atendimento precisam treinamento?
   - Temas técnicos que geram mais solicitações de suporte?

3. OTIMIZAÇÃO OPERACIONAL
   - Como reduzir dependência dos agentes nos supervisores?
   - Ferramentas para aumentar autonomia dos funcionários?

4. MONITORAMENTO DE EFICIÊNCIA
   - KPIs para detectar sobrecarga de supervisores precocemente?
   - Métricas de evolução da autonomia dos agentes?

5. PLANEJAMENTO DE RECURSOS
   - Necessidade de contratação ou redistribuição?
   - Investimento em treinamento vs contratação de pessoal?

REGRAS: Foque em decisões executivas baseadas nos números reais. Máximo 140 palavras.
"""
        return prompt.strip()
    
    @staticmethod
    def executive_summary(weekly_data: Dict[str, Any], 
                         global_analysis: Dict[str, Any],
                         supervisors_analysis: List[Dict[str, Any]]) -> str:
        """
        📋 Prompt para resumo executivo
        """
        period = weekly_data['metadata']['current_week']['period_label']
        total_tickets = weekly_data['global_stats']['current_week']['total_tickets']
        change = weekly_data['global_stats']['comparison']['absolute_change']
        change_percent = weekly_data['global_stats']['comparison']['percent_change']
        
        # Análise dos supervisores
        if supervisors_analysis:
            top_performer = max(supervisors_analysis, key=lambda x: x['key_metrics']['current_tickets'])
            high_variance = [s for s in supervisors_analysis if 
                           abs(s['key_metrics']['change_percent']) >= 30]
        else:
            top_performer = None
            high_variance = []
        
        prompt = f"""
Você é CEO/diretor apresentando resultados para conselho administrativo.

RESUMO EXECUTIVO - PRODUTIVIDADE CONTÁBIL ({period}):

NÚMEROS PRINCIPAIS:
- Total de atendimentos prestados: {total_tickets}
- Variação operacional: {change:+d} ({change_percent:+.1f}%)
- Supervisores monitorados: {len(supervisors_analysis)}
- Situações que requerem atenção: {len(high_variance)}
"""
        
        if top_performer:
            prompt += f"• Supervisor com maior demanda: {top_performer['supervisor_name']} ({top_performer['key_metrics']['current_tickets']} atendimentos)\n"
        
        prompt += f"""
APRESENTAÇÃO PARA CONSELHO:

1. SITUAÇÃO OPERACIONAL
   - Status da produtividade na contabilidade
   - Eficiência dos supervisores vs demanda dos agentes

2. PONTOS CRÍTICOS
   - Supervisores sobrecarregados que impactam produtividade
   - Agentes com alta dependência (precisam desenvolvimento urgente)

3. TENDÊNCIAS OBSERVADAS
   - Padrões na demanda por suporte técnico
   - Evolução da autonomia dos funcionários

4. DECISÕES ESTRATÉGICAS
   - Investimentos necessários em capacitação
   - Necessidade de contratação ou redistribuição

5. METAS PRÓXIMO PERÍODO
   - Objetivos de redução da dependência
   - KPIs para monitorar eficiência

REGRAS: Linguagem executiva para conselho. Use apenas números reais. Máximo 120 palavras.
"""
        return prompt.strip()
    
    @staticmethod
    def agent_workload_analysis(agents_data: List[Dict[str, Any]], 
                               supervisor_name: str) -> str:
        """
        👥 Prompt para análise detalhada dos agentes
        """
        if not agents_data:
            return "Nenhum atendimento registrado para agentes."
        
        total_tickets = sum(agent['current_tickets'] for agent in agents_data)
        
        prompt = f"""
Você é coordenador de RH analisando produtividade individual dos agentes.

ANÁLISE DA EQUIPE DO SUPERVISOR {supervisor_name}:
- Total de agentes: {len(agents_data)}
- Total de atendimentos solicitados: {total_tickets}

PERFORMANCE INDIVIDUAL (comparação semanal):
"""
        
        for agent in agents_data:
            name = agent['agent']['name']
            current = agent['current_tickets']
            previous = agent['previous_tickets']
            change = agent.get('change', 0)
            
            if previous > 0:
                percent_change = (change / previous) * 100
                prompt += f"• {name}: {current} atendimentos (anterior: {previous}) = {change:+d} ({percent_change:+.1f}%)\n"
            else:
                prompt += f"• {name}: {current} atendimentos (anterior: {previous}) = {change:+d}\n"
        
        prompt += f"""
ANÁLISE INDIVIDUAL SOLICITADA:

1. IDENTIFICAÇÃO DE NECESSIDADES
   - Quais agentes tiveram maior aumento percentual (precisam treinamento)?
   - Quais agentes tiveram redução significativa (mais autônomos ou ociosos)?

2. DISTRIBUIÇÃO DE PRODUTIVIDADE
   - A demanda está concentrada em poucos agentes?
   - Algum agente demonstra sobrecarga de trabalho?

3. OPORTUNIDADES DE DESENVOLVIMENTO
   - Agentes prontos para assumir casos mais complexos?
   - Necessidades específicas de capacitação técnica?

4. RECOMENDAÇÕES PRÁTICAS
   - Redistribuição de responsabilidades entre agentes?
   - Plano de treinamento individualizado?

REGRAS: Cite nomes dos agentes nos insights. Use números reais. Máximo 90 palavras.
"""
        return prompt.strip()
    
    @staticmethod
    def anomaly_detection(supervisor_data: Dict[str, Any], 
                         historical_context: Optional[Dict] = None) -> str:
        """
        🔍 Prompt para detecção de anomalias
        """
        supervisor = supervisor_data['supervisor']['name']
        change_percent = supervisor_data['comparison']['percent_change']
        current_tickets = supervisor_data['current_week']['total_tickets']
        agents = supervisor_data['current_week']['agents_performance']
        
        # Identificar anomalias reais
        anomalies = []
        
        if abs(change_percent) >= 60:
            anomalies.append(f"Supervisor {supervisor}: variação extrema de {change_percent:+.1f}% nos atendimentos")
        
        if current_tickets >= 60:
            anomalies.append(f"Supervisor {supervisor}: volume muito alto ({current_tickets} atendimentos)")
        
        for agent in agents:
            agent_change_percent = (agent['change'] / agent['previous_tickets'] * 100) if agent['previous_tickets'] > 0 else 0
            if abs(agent_change_percent) >= 100:
                anomalies.append(f"Agente {agent['agent']['name']}: variação de {agent_change_percent:+.1f}% nos atendimentos")
            if agent['current_tickets'] >= 25:
                anomalies.append(f"Agente {agent['agent']['name']}: {agent['current_tickets']} atendimentos (possível sobrecarga)")
        
        prompt = f"""
Você é analista de qualidade investigando padrões atípicos na produtividade.

ANOMALIAS DETECTADAS: {len(anomalies)}
"""
        
        for i, anomaly in enumerate(anomalies, 1):
            prompt += f"{i}. {anomaly}\n"
        
        prompt += f"""
INVESTIGAÇÃO NECESSÁRIA:

1. CAUSAS PROVÁVEIS
   - Picos de demanda de clientes específicos?
   - Agentes enfrentando dificuldades técnicas incomuns?
   - Mudanças nos processos que afetaram produtividade?

2. IMPACTO OPERACIONAL
   - Risco de burnout ou sobrecarga?
   - Qualidade dos atendimentos comprometida?
   - Gargalos na operação?

3. AÇÕES CORRETIVAS IMEDIATAS
   - Redistribuição emergencial de carga?
   - Suporte adicional urgente?
   - Pausar novos casos complexos?

4. PREVENÇÃO FUTURA
   - Monitoramento mais frequente?
   - Ajustes nos processos de distribuição?
   - Treinamentos preventivos?

REGRAS: Foque em causas operacionais reais. Máximo 100 palavras.
"""
        return prompt.strip()
    
    @staticmethod
    def custom_insight_prompt(context: str, data_summary: str, question: str) -> str:
        """
        🎨 Prompt personalizado para insights específicos
        """
        prompt = f"""
Você é consultor de produtividade em contabilidade.

CONTEXTO: {context}
DADOS: {data_summary}
PERGUNTA: {question}

ANÁLISE: Resposta baseada em números reais, máximo 70 palavras, foque em produtividade.
"""
        return prompt.strip()


# Funções de conveniência para uso direto
def get_global_analysis_prompt(global_stats: Dict[str, Any], weekly_data: Dict[str, Any]) -> str:
    """🔧 Função utilitária para prompt de análise global"""
    return PromptBuilder.global_trend_analysis(global_stats, weekly_data)


def get_supervisor_analysis_prompt(supervisor_data: Dict[str, Any], weekly_data: Dict[str, Any], ranking: Optional[int] = None) -> str:
    """🔧 Função utilitária para prompt de análise de supervisor"""
    return PromptBuilder.supervisor_performance_analysis(supervisor_data, weekly_data, ranking)


def get_strategic_prompt(weekly_data: Dict[str, Any]) -> str:
    """🔧 Função utilitária para prompt estratégico"""
    return PromptBuilder.strategic_recommendations(weekly_data)