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
    
    Gera prompts otimizados para diferentes cenários de análise
    de dados de atendimento e performance de equipes
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
        
        # Determinar contexto da variação
        if abs(change_percent) >= 30:
            intensity = "significativa"
        elif abs(change_percent) >= 15:
            intensity = "moderada"
        else:
            intensity = "leve"
        
        prompt = f"""
Você é um analista sênior de operações de atendimento. Analise os dados semanais abaixo:

PERÍODO DE ANÁLISE: {period}
• Atendimentos esta semana: {current_tickets}
• Atendimentos semana anterior: {previous_tickets}
• Variação: {change:+d} atendimentos ({change_percent:+.1f}%)
• Supervisores ativos: {active_supervisors}
• Intensidade da mudança: {intensity}

TAREFA: Forneça uma análise profissional focada em:

1. INTERPRETAÇÃO DA TENDÊNCIA
   - O que essa variação representa operacionalmente?
   - É um padrão esperado ou atípico?

2. POSSÍVEIS CAUSAS
   - Fatores que podem explicar essa mudança
   - Sazonalidade ou eventos específicos

3. IMPACTO OPERACIONAL
   - Como isso afeta a carga de trabalho das equipes?
   - Riscos ou oportunidades identificadas

4. RECOMENDAÇÕES IMEDIATAS
   - Ações que devem ser tomadas nesta semana
   - Pontos de atenção para monitoramento

FORMATO: Resposta direta e actionable, máximo 180 palavras.
FOCO: Insights práticos para gestão operacional.
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
        
        # Análise da distribuição entre agentes
        if agents:
            total_agent_tickets = sum(a['current_tickets'] for a in agents)
            top_agent = max(agents, key=lambda x: x['current_tickets'])
            concentration = (top_agent['current_tickets'] / total_agent_tickets * 100) if total_agent_tickets > 0 else 0
        else:
            concentration = 0
            top_agent = None
        
        # Contexto de performance
        if change_percent >= 25:
            performance_context = "alta crescimento"
        elif change_percent >= 10:
            performance_context = "crescimento moderado"
        elif change_percent <= -25:
            performance_context = "redução significativa"
        elif change_percent <= -10:
            performance_context = "redução moderada"
        else:
            performance_context = "estabilidade"
        
        ranking_text = f"(posição #{ranking_position} no ranking)" if ranking_position else ""
        
        prompt = f"""
Você é um consultor de gestão de equipes. Analise a performance do supervisor abaixo:

SUPERVISOR: {supervisor} {ranking_text}
PERÍODO: {weekly_data['metadata']['current_week']['period_label']}

MÉTRICAS PRINCIPAIS:
• Atendimentos: {current} (anterior: {previous})
• Variação: {change:+d} ({change_percent:+.1f}%)
• Contexto: {performance_context}
• Agentes na equipe: {agents_count}
• Concentração no top agente: {concentration:.1f}%

DISTRIBUIÇÃO POR AGENTE:
"""
        
        # Adicionar dados dos agentes
        for i, agent in enumerate(agents[:5], 1):  # Top 5 agentes
            agent_change = agent['change']
            agent_change_percent = (agent_change / agent['previous_tickets'] * 100) if agent['previous_tickets'] > 0 else 0
            
            prompt += f"• {agent['agent']['name']}: {agent['current_tickets']} atendimentos ({agent_change:+d}, {agent_change_percent:+.1f}%)\n"
        
        prompt += f"""
ANÁLISE SOLICITADA:

1. AVALIAÇÃO GERAL
   - Como avaliar esta performance no contexto atual?
   - A distribuição de trabalho está equilibrada?

2. ANÁLISE DOS AGENTES
   - Identifique padrões na equipe
   - Sinalize agentes que precisam de atenção

3. OPORTUNIDADES DE MELHORIA
   - Sugestões para otimizar a distribuição
   - Como apoiar melhor a equipe

4. RECOMENDAÇÕES ESPECÍFICAS
   - Ações concretas para esta semana
   - Pontos de monitoramento contínuo

FORMATO: Análise estruturada e prática, máximo 160 palavras.
FOCO: Actionable insights para gestão da equipe.
"""
        return prompt.strip()
    
    @staticmethod
    def agent_workload_analysis(agents_data: List[Dict[str, Any]], 
                               supervisor_name: str) -> str:
        """
        👥 Prompt para análise de carga de trabalho dos agentes
        """
        if not agents_data:
            return "Nenhum agente ativo para análise."
        
        total_tickets = sum(agent['current_tickets'] for agent in agents_data)
        avg_tickets = total_tickets / len(agents_data) if agents_data else 0
        
        # Identificar agentes com carga atípica
        overloaded = [a for a in agents_data if a['current_tickets'] >= avg_tickets * 1.5]
        underloaded = [a for a in agents_data if a['current_tickets'] <= avg_tickets * 0.5 and a['current_tickets'] > 0]
        big_changes = [a for a in agents_data if abs(a.get('change', 0)) >= 10]
        
        prompt = f"""
Você é um especialista em distribuição de carga de trabalho. Analise a equipe do supervisor {supervisor_name}:

CENÁRIO ATUAL:
• Total de agentes: {len(agents_data)}
• Total de atendimentos: {total_tickets}
• Média por agente: {avg_tickets:.1f}
• Agentes sobrecarregados: {len(overloaded)}
• Agentes com baixa demanda: {len(underloaded)}
• Agentes com mudanças significativas: {len(big_changes)}

DETALHAMENTO POR AGENTE:
"""
        
        for agent in agents_data:
            current = agent['current_tickets']
            change = agent.get('change', 0)
            status = "⚠️" if current >= avg_tickets * 1.5 else "⬇️" if current <= avg_tickets * 0.5 else "✅"
            
            prompt += f"• {status} {agent['agent']['name']}: {current} atendimentos ({change:+d})\n"
        
        prompt += f"""
ANÁLISE NECESSÁRIA:

1. DISTRIBUIÇÃO DE CARGA
   - A distribuição atual é eficiente?
   - Identifique desequilíbrios problemáticos

2. IDENTIFICAÇÃO DE RISCOS
   - Agentes em risco de sobrecarga ou burnout
   - Capacidade ociosa subutilizada

3. REDISTRIBUIÇÃO SUGERIDA
   - Como reequilibrar a carga de trabalho?
   - Critérios para redistribuição

4. AÇÕES PREVENTIVAS
   - Como evitar desequilíbrios futuros?
   - Monitoramento recomendado

FORMATO: Recomendações práticas, máximo 140 palavras.
FOCO: Otimização da distribuição e bem-estar da equipe.
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
        high_performers = [s for s in supervisors if s['comparison']['percent_change'] >= 20]
        struggling = [s for s in supervisors if s['comparison']['percent_change'] <= -20]
        stable = [s for s in supervisors if abs(s['comparison']['percent_change']) < 20]
        
        # Top e bottom performers
        top_supervisor = max(supervisors, key=lambda x: x['current_week']['total_tickets']) if supervisors else None
        bottom_supervisor = min(supervisors, key=lambda x: x['current_week']['total_tickets']) if supervisors else None
        
        # Análise de variabilidade
        if supervisors:
            ticket_counts = [s['current_week']['total_tickets'] for s in supervisors]
            max_tickets = max(ticket_counts)
            min_tickets = min(ticket_counts)
            variability = ((max_tickets - min_tickets) / max_tickets * 100) if max_tickets > 0 else 0
        else:
            variability = 0
        
        prompt = f"""
Você é um diretor de operações analisando performance semanal. Elabore recomendações estratégicas baseadas nos dados:

CENÁRIO ORGANIZACIONAL:
• Período: {weekly_data['metadata']['current_week']['period_label']}
• Total de atendimentos: {global_stats['current_week']['total_tickets']}
• Variação global: {global_stats['comparison']['absolute_change']:+d} ({global_stats['comparison']['percent_change']:+.1f}%)
• Supervisores ativos: {total_supervisors}

DISTRIBUIÇÃO DE PERFORMANCE:
• Alto desempenho (+20%): {len(high_performers)} supervisores
• Performance estável: {len(stable)} supervisores  
• Necessitam apoio (-20%): {len(struggling)} supervisores
• Variabilidade entre equipes: {variability:.1f}%
"""
        
        if top_supervisor:
            prompt += f"• Top performer: {top_supervisor['supervisor']['name']} ({top_supervisor['current_week']['total_tickets']} atendimentos)\n"
        
        if bottom_supervisor and bottom_supervisor != top_supervisor:
            prompt += f"• Menor volume: {bottom_supervisor['supervisor']['name']} ({bottom_supervisor['current_week']['total_tickets']} atendimentos)\n"
        
        prompt += f"""
ESTRATÉGIAS SOLICITADAS:

1. REDISTRIBUIÇÃO DE RECURSOS
   - Como otimizar alocação entre equipes?
   - Transferência de agentes ou responsabilidades

2. DESENVOLVIMENTO DE EQUIPES
   - Quais supervisores precisam de mentoria?
   - Programas de capacitação recomendados

3. PROCESSOS E FERRAMENTAS
   - Melhorias nos processos de atendimento
   - Ferramentas para aumentar eficiência

4. PREVENÇÃO E MONITORAMENTO
   - Indicadores para acompanhar semanalmente
   - Alertas antecipados de problemas

5. RECONHECIMENTO E MOTIVAÇÃO
   - Como reconhecer boas performances?
   - Estratégias para manter engajamento

FORMATO: 5 recomendações estratégicas específicas e implementáveis.
FOCO: Ações de médio prazo com impacto mensurável.
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
            attention_needed = [s for s in supervisors_analysis if 
                              abs(s['key_metrics']['change_percent']) >= 30 or 
                              any(agent.get('needs_attention', False) for agent in s.get('agents_insights', []))]
        else:
            top_performer = None
            attention_needed = []
        
        prompt = f"""
Você é um C-level executivo preparando um briefing para a diretoria. Crie um resumo executivo conciso:

PERFORMANCE SEMANAL - {period}

INDICADORES CHAVE:
• Volume total: {total_tickets} atendimentos
• Variação semanal: {change:+d} ({change_percent:+.1f}%)
• Supervisores monitorados: {len(supervisors_analysis)}
• Equipes requerendo atenção: {len(attention_needed)}
"""
        
        if top_performer:
            prompt += f"• Melhor performance: {top_performer['supervisor_name']} ({top_performer['key_metrics']['current_tickets']} atendimentos)\n"
        
        prompt += f"""
RESUMO EXECUTIVO SOLICITADO:

1. SITUAÇÃO ATUAL
   - Status geral das operações
   - Principais conquistas da semana

2. PONTOS DE ATENÇÃO
   - Riscos operacionais identificados
   - Supervisores/equipes que precisam de suporte

3. TENDÊNCIAS OBSERVADAS
   - Padrões emergentes
   - Mudanças no comportamento operacional

4. DECISÕES NECESSÁRIAS
   - Ações que requerem aprovação executiva
   - Recursos adicionais necessários

5. OUTLOOK PRÓXIMA SEMANA
   - Expectativas e preparações
   - Métricas para monitoramento

FORMATO: Linguagem executiva, máximo 200 palavras.
FOCO: Insights estratégicos e tomada de decisão.
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
        
        # Identificar anomalias
        anomalies = []
        
        if abs(change_percent) >= 50:
            anomalies.append(f"Variação extrema de {change_percent:+.1f}%")
        
        for agent in agents:
            agent_change_percent = (agent['change'] / agent['previous_tickets'] * 100) if agent['previous_tickets'] > 0 else 0
            if abs(agent_change_percent) >= 100:
                anomalies.append(f"{agent['agent']['name']}: mudança de {agent_change_percent:+.1f}%")
            if agent['current_tickets'] >= 50:
                anomalies.append(f"{agent['agent']['name']}: {agent['current_tickets']} atendimentos (possível sobrecarga)")
        
        prompt = f"""
Você é um analista de dados especializado em detecção de anomalias operacionais. Investigue as anomalias identificadas:

SUPERVISOR: {supervisor}
ANOMALIAS DETECTADAS: {len(anomalies)}
"""
        
        for i, anomaly in enumerate(anomalies, 1):
            prompt += f"{i}. {anomaly}\n"
        
        prompt += f"""
CONTEXTO OPERACIONAL:
• Atendimentos atuais: {current_tickets}
• Variação semanal: {change_percent:+.1f}%
• Agentes na equipe: {len(agents)}

INVESTIGAÇÃO REQUERIDA:

1. ANÁLISE DAS ANOMALIAS
   - Quais são as possíveis causas?
   - São eventos pontuais ou tendências?

2. CLASSIFICAÇÃO DE RISCO
   - Grau de criticidade de cada anomalia
   - Impacto potencial nas operações

3. AÇÕES IMEDIATAS
   - O que deve ser feito imediatamente?
   - Quem deve ser notificado?

4. PREVENÇÃO FUTURA
   - Como detectar sinais precoces?
   - Medidas preventivas recomendadas

FORMATO: Análise investigativa, máximo 150 palavras.
FOCO: Identificação de causas e ações corretivas.
"""
        return prompt.strip()
    
    @staticmethod
    def custom_insight_prompt(context: str, data_summary: str, question: str) -> str:
        """
        🎨 Prompt personalizado para insights específicos
        """
        prompt = f"""
Você é um consultor sênior de operações de atendimento. Analise a situação abaixo:

CONTEXTO: {context}

DADOS DISPONÍVEIS:
{data_summary}

PERGUNTA ESPECÍFICA:
{question}

ANÁLISE SOLICITADA:
• Forneça uma resposta fundamentada nos dados
• Seja específico e actionable
• Máximo 120 palavras
• Foco em insights práticos para gestão

FORMATO: Resposta direta com recomendações concretas.
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