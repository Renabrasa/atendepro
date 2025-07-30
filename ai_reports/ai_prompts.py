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
    
    Gera prompts ultra-específicos para análise de produtividade em contabilidade
    """
    
    @staticmethod
    def supervisor_performance_analysis(supervisor_data: Dict[str, Any], 
                                    weekly_data: Dict[str, Any],
                                    ranking_position: Optional[int] = None) -> str:
        """Análise conversacional e inteligente do supervisor"""
        
        supervisor = supervisor_data['supervisor']['name']
        current = supervisor_data['current_week']['total_tickets']
        
        # CORREÇÃO: Acessar dados do período anterior de forma segura
        previous = supervisor_data.get('previous_week', {}).get('total_tickets', 0)
        change = supervisor_data.get('comparison', {}).get('absolute_change', 0)
        change_percent = supervisor_data.get('comparison', {}).get('percent_change', 0)
        
        agents = supervisor_data['current_week']['agents_performance']
        
        # Análise automática de padrões
        top_agent = max(agents, key=lambda x: x['current_tickets']) if agents else None
        concern_agents = [a for a in agents if a.get('change', 0) > 5]
        improved_agents = [a for a in agents if a.get('change', 0) < -3]
        
        prompt = f"""
CONTEXTO: Empresa de contabilidade onde agentes escalam casos complexos para supervisores.

DADOS OBJETIVOS DE {supervisor}:
• Atendimentos prestados: {current} (anterior: {previous}) 
• Variação: {change:+d} ({change_percent:+.1f}%)
• Ranking: {ranking_position if ranking_position else 'N/A'}º posição
• Equipe: {len(agents)} agentes

DESTAQUE DOS AGENTES:
"""
        
        if top_agent:
            top_change = top_agent.get('change', 0)
            prompt += f"• {top_agent['agent']['name']}: {top_agent['current_tickets']} casos ({top_change:+d})\n"
        
        for agent in agents[1:3]:  # Próximos 2 agentes
            agent_change = agent.get('change', 0)
            prompt += f"• {agent['agent']['name']}: {agent['current_tickets']} casos ({agent_change:+d})\n"
        
        prompt += f"""
INSTRUÇÕES OBRIGATÓRIAS:
- NÃO mencione: férias, escola, sazonalidade, aulas, período escolar
- Foque APENAS em empresa de contabilidade
- Linguagem conversacional e profissional
- Máximo 70 palavras
- Insights acionáveis e específicos

GERE ANÁLISE CONVERSACIONAL:
Escreva como consultor experiente falando para {supervisor}:
- Comente a performance ({current} casos, {change:+d})
- Destaque agente principal e insights
- Sugira ação específica e prática
- Tom profissional mas humano

FORMATO EXEMPLO: "{supervisor}, sua equipe processou {current} casos esta semana. Destaque para [agente] que [insight específico]. Recomendo [ação concreta] para [resultado esperado]."
"""
        return prompt.strip()
    
    @staticmethod
    def strategic_recommendations(weekly_data: Dict[str, Any]) -> str:
        """
        🎯 Prompt para recomendações estratégicas - VERSÃO CORRIGIDA
        """
        supervisors = weekly_data['supervisors_data']
        global_stats = weekly_data['global_stats']
        
        # Encontrar supervisor com mais atendimentos
        top_supervisor = max(supervisors, key=lambda x: x['current_week']['total_tickets']) if supervisors else None
        
        # Contar supervisores sobrecarregados
        overloaded_count = len([s for s in supervisors if s['current_week']['total_tickets'] >= 40])
        
        # CORREÇÃO: Acessar dados globais de forma segura
        current_total = global_stats.get('current_week', {}).get('total_tickets', 0)
        change_abs = global_stats.get('comparison', {}).get('absolute_change', 0)
        change_pct = global_stats.get('comparison', {}).get('percent_change', 0)
        
        prompt = f"""
INSTRUÇÕES CRÍTICAS:
- Máximo 100 palavras
- Use APENAS dados fornecidos
- NÃO mencione férias, escola, sazonalidade
- Foque em ações práticas

DADOS EXECUTIVOS:
Total atendimentos: {current_total}
Variação: {change_abs:+d} ({change_pct:+.1f}%)
Supervisores: {len(supervisors)}
Sobrecarregados (≥40 atendimentos): {overloaded_count}
"""
        
        if top_supervisor:
            prompt += f"Maior volume: {top_supervisor['supervisor']['name']} ({top_supervisor['current_week']['total_tickets']} atendimentos)\n"
        
        prompt += f"""
RECOMENDAÇÕES OBRIGATÓRIAS (template fixo):

1. CAPACITAÇÃO: Treinar agentes que mais demandam atendimento
2. REDISTRIBUIÇÃO: Balancear carga entre supervisores{"s sobrecarregados" if overloaded_count > 0 else ""}  
3. MONITORAMENTO: Acompanhar evolução semanal dos agentes
4. EFICIÊNCIA: Criar processos para reduzir dependência
5. RECURSOS: {"Considerar reforço para supervisores com >40 atendimentos" if overloaded_count > 0 else "Manter estrutura atual"}
"""
        return prompt.strip()
    
    @staticmethod
    def executive_summary_simple(weekly_data: Dict[str, Any], 
                                supervisors_analysis: List[Dict[str, Any]]) -> str:
        """
        📋 Prompt para resumo executivo simplificado (sem global_analysis)
        """
        period = weekly_data['metadata']['current_week']['period_label']
        
        # CORREÇÃO: Acessar dados globais de forma segura
        global_stats = weekly_data.get('global_stats', {})
        current_week = global_stats.get('current_week', {})
        comparison = global_stats.get('comparison', {})
        
        total_tickets = current_week.get('total_tickets', 0)
        change = comparison.get('absolute_change', 0)
        change_percent = comparison.get('percent_change', 0)
        
        # Usar intelligent_insights se disponível
        intelligent_insights = weekly_data.get('intelligent_insights', {})
        alerts_count = len(intelligent_insights.get('performance_alerts', []))
        patterns_count = len(intelligent_insights.get('concentration_patterns', []))
        
        prompt = f"""
INSTRUÇÕES EXECUTIVAS:
- Máximo 80 palavras
- Use APENAS números fornecidos
- NÃO mencione férias, escola, sazonalidade
- Linguagem para diretoria
- Base-se em insights automáticos do sistema

RESUMO EXECUTIVO - {period}:

PRODUTIVIDADE: {total_tickets} atendimentos prestados por supervisores ({change:+d}, {change_percent:+.1f}%).

SITUAÇÃO: {"Supervisores com mais demanda" if change > 0 else "Supervisores com menos demanda"}.

INSIGHTS AUTOMÁTICOS: {alerts_count} alertas de performance, {patterns_count} padrões identificados.

CAUSA: {"Agentes precisando mais suporte" if change > 0 else "Agentes mais autônomos"}.

AÇÃO: {"Investir em treinamento dos agentes" if change > 0 else "Monitorar produtividade dos agentes"}.

STATUS: {"Atenção para sobrecarga" if total_tickets > 200 else "Operação normal"}.
"""
        return prompt.strip()
    
    @staticmethod
    def agent_workload_analysis(agents_data: List[Dict[str, Any]], 
                               supervisor_name: str) -> str:
        """
        👥 Prompt para análise dos agentes - VERSÃO CORRIGIDA
        """
        if not agents_data:
            return "Nenhum agente com atendimentos registrados."
        
        prompt = f"""
INSTRUÇÕES:
- Máximo 70 palavras
- Cite nomes dos agentes
- Use APENAS dados fornecidos

AGENTES DO SUPERVISOR {supervisor_name}:
"""
        
        for agent in agents_data[:3]:
            name = agent['agent']['name']
            current = agent.get('current_tickets', 0)
            change = agent.get('change', 0)
            
            # CORREÇÃO: Acessar previous_tickets de forma segura
            previous_tickets = 0
            if 'previous_tickets' in agent:
                previous_tickets = agent['previous_tickets']
            elif hasattr(agent, 'previous_tickets'):
                previous_tickets = agent.previous_tickets
            else:
                # Calcular baseado no change
                previous_tickets = current - change if change != 0 else 0
            
            # Calcular percentual de forma segura
            try:
                if previous_tickets > 0:
                    percent = (change / previous_tickets * 100)
                    prompt += f"{name}: {current} atendimentos ({change:+d}, {percent:+.1f}%)\n"
                else:
                    prompt += f"{name}: {current} atendimentos ({change:+d})\n"
            except (ZeroDivisionError, TypeError):
                prompt += f"{name}: {current} atendimentos ({change:+d})\n"
        
        prompt += f"""
RECOMENDAÇÃO: {"Treinar agentes com maior aumento" if any(a.get('change', 0) > 5 for a in agents_data) else "Monitorar evolução"}.
"""
        return prompt.strip()
    
    @staticmethod
    def anomaly_detection(supervisor_data: Dict[str, Any], 
                         historical_context: Optional[Dict] = None) -> str:
        """
        🔍 Prompt para detecção de anomalias - VERSÃO CORRIGIDA
        """
        supervisor = supervisor_data['supervisor']['name']
        
        # CORREÇÃO: Acessar dados de comparação de forma segura
        comparison = supervisor_data.get('comparison', {})
        change_percent = comparison.get('percent_change', 0)
        current_tickets = supervisor_data['current_week']['total_tickets']
        
        prompt = f"""
INSTRUÇÕES:
- Máximo 60 palavras
- Use APENAS dados fornecidos

ANOMALIA DETECTADA:
Supervisor {supervisor}: {current_tickets} atendimentos ({change_percent:+.1f}%).

AÇÃO: {"Investigar sobrecarga urgente" if current_tickets > 50 else "Monitorar evolução normal"}.
"""
        return prompt.strip()
    
    @staticmethod
    def custom_insight_prompt(context: str, data_summary: str, question: str) -> str:
        """
        🎨 Prompt personalizado
        """
        prompt = f"""
CONTEXTO: {context}
DADOS: {data_summary}
PERGUNTA: {question}

RESPOSTA (máximo 50 palavras): Use apenas dados fornecidos.
"""
        return prompt.strip()


# Funções de conveniência - VERSÕES CORRIGIDAS
def get_supervisor_analysis_prompt(supervisor_data: Dict[str, Any], weekly_data: Dict[str, Any], ranking: Optional[int] = None) -> str:
    """Função de conveniência para análise de supervisor"""
    return PromptBuilder.supervisor_performance_analysis(supervisor_data, weekly_data, ranking)

def get_strategic_prompt(weekly_data: Dict[str, Any]) -> str:
    """Função de conveniência para recomendações estratégicas"""
    return PromptBuilder.strategic_recommendations(weekly_data)

def get_executive_summary_prompt(weekly_data: Dict[str, Any], supervisors_analysis: List[Dict[str, Any]]) -> str:
    """Função de conveniência para resumo executivo"""
    return PromptBuilder.executive_summary_simple(weekly_data, supervisors_analysis)