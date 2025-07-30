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
    de dados de atendimento interno de RH e performance de equipes
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
Você é um analista de RH especializado em atendimento interno de funcionários.

SISTEMA: AtendePro - Sistema interno onde supervisores de RH atendem solicitações de funcionários (questões trabalhistas, dúvidas, suporte interno).

DADOS EXATOS DO PERÍODO:
- Período atual: {period}
- Atendimentos período atual: {current_tickets}
- Atendimentos período anterior: {previous_tickets}
- Variação exata: {change:+d} atendimentos ({change_percent:+.1f}%)
- Supervisores ativos: {active_supervisors}

REGRAS IMPORTANTES:
- Use APENAS os números fornecidos acima
- NÃO invente ou estime números diferentes
- Foque em atendimento INTERNO de RH, não clientes externos

ANÁLISE SOLICITADA:

1. INTERPRETAÇÃO DOS DADOS REAIS
   - O que significa esta variação de {change_percent:+.1f}% no atendimento interno?
   - É normal para um sistema de RH interno?

2. POSSÍVEIS CAUSAS INTERNAS
   - Fatores que afetam demanda de funcionários por suporte
   - Sazonalidade empresarial ou eventos internos

3. IMPACTO NA EQUIPE DE RH
   - Como essa carga afeta os supervisores?
   - Distribuição de trabalho entre {active_supervisors} supervisores

4. RECOMENDAÇÕES PRÁTICAS
   - Ações para otimizar atendimento interno
   - Pontos de atenção para próximo período

FORMATO: Máximo 150 palavras, foque apenas nos dados fornecidos.
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
Você é um consultor de gestão de RH analisando performance de supervisor interno.

CONTEXTO: {supervisor} é supervisor de RH que atende funcionários internos com questões trabalhistas, dúvidas corporativas e suporte geral.

DADOS EXATOS DO SUPERVISOR:
- Nome: {supervisor} {ranking_text}
- Período: {weekly_data['metadata']['current_week']['period_label']}
- Atendimentos atuais: {current}
- Atendimentos anteriores: {previous}
- Variação exata: {change:+d} ({change_percent:+.1f}%)
- Agentes na equipe: {agents_count}

DISTRIBUIÇÃO REAL POR AGENTE:
"""
        
        # Adicionar dados dos agentes
        for agent in agents[:5]:  # Top 5 agentes
            agent_change = agent['change']
            prompt += f"• {agent['agent']['name']}: {agent['current_tickets']} atendimentos ({agent_change:+d} vs anterior)\n"
        
        prompt += f"""
REGRAS IMPORTANTES:
- Use APENAS os números exatos fornecidos acima
- NÃO crie números que não existem
- Foque em atendimento INTERNO de funcionários

ANÁLISE ESPECÍFICA:

1. PERFORMANCE GERAL
   - Como avaliar {current} atendimentos com variação de {change_percent:+.1f}%?
   - Esta carga é adequada para um supervisor de RH?

2. DISTRIBUIÇÃO DA EQUIPE
   - A distribuição entre os {agents_count} agentes está equilibrada?
   - Algum agente precisa de redistribuição de carga?

3. OPORTUNIDADES DE MELHORIA
   - Como otimizar atendimento interno aos funcionários?
   - Sugestões para melhorar eficiência da equipe

4. RECOMENDAÇÕES CONCRETAS
   - Ações específicas para próxima semana
   - Pontos de monitoramento contínuo

FORMATO: Máximo 130 palavras, seja específico e prático.
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
        high_performers = [s for s in supervisors if s['comparison']['percent_change'] >= 15]
        struggling = [s for s in supervisors if s['comparison']['percent_change'] <= -15]
        stable = [s for s in supervisors if abs(s['comparison']['percent_change']) < 15]
        
        # Top performer
        top_supervisor = max(supervisors, key=lambda x: x['current_week']['total_tickets']) if supervisors else None
        
        prompt = f"""
Você é um diretor de RH analisando performance do sistema interno de atendimento.

CONTEXTO: AtendePro é sistema interno onde supervisores de RH atendem funcionários com questões trabalhistas, dúvidas corporativas e suporte.

DADOS REAIS DO SISTEMA:
- Período: {weekly_data['metadata']['current_week']['period_label']}
- Total de atendimentos internos: {global_stats['current_week']['total_tickets']}
- Variação do sistema: {global_stats['comparison']['absolute_change']:+d} ({global_stats['comparison']['percent_change']:+.1f}%)
- Supervisores ativos: {total_supervisors}

DISTRIBUIÇÃO DE PERFORMANCE:
- Supervisores com crescimento (+15%): {len(high_performers)}
- Supervisores estáveis: {len(stable)}
- Supervisores em declínio (-15%): {len(struggling)}
"""
        
        if top_supervisor:
            prompt += f"• Melhor performance: {top_supervisor['supervisor']['name']} ({top_supervisor['current_week']['total_tickets']} atendimentos)\n"
        
        prompt += f"""
REGRAS IMPORTANTES:
- Use APENAS os dados fornecidos acima
- Foque em otimização de RH interno
- NÃO invente números

RECOMENDAÇÕES ESTRATÉGICAS:

1. REDISTRIBUIÇÃO DE CARGA
   - Como balancear atendimentos entre supervisores?
   - Transferência de responsabilidades entre equipes

2. CAPACITAÇÃO DE EQUIPE
   - Supervisores que precisam de treinamento
   - Programas de desenvolvimento interno

3. OTIMIZAÇÃO DE PROCESSOS
   - Melhorias no atendimento aos funcionários
   - Ferramentas para aumentar eficiência

4. MONITORAMENTO CONTÍNUO
   - Indicadores chave para acompanhar
   - Alertas para problemas futuros

5. RECONHECIMENTO DE PERFORMANCE
   - Como valorizar bons resultados
   - Estratégias de motivação da equipe

FORMATO: 5 recomendações específicas e implementáveis, máximo 180 palavras.
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
                              abs(s['key_metrics']['change_percent']) >= 25]
        else:
            top_performer = None
            attention_needed = []
        
        prompt = f"""
Você é um executivo de RH preparando briefing sobre sistema interno de atendimento.

CONTEXTO: AtendePro - sistema onde supervisores de RH atendem funcionários internos com questões trabalhistas e suporte corporativo.

DADOS EXATOS DO PERÍODO - {period}:
- Volume total de atendimentos internos: {total_tickets}
- Variação exata: {change:+d} ({change_percent:+.1f}%)
- Supervisores monitorados: {len(supervisors_analysis)}
- Equipes com variação significativa: {len(attention_needed)}
"""
        
        if top_performer:
            prompt += f"• Melhor performance: {top_performer['supervisor_name']} ({top_performer['key_metrics']['current_tickets']} atendimentos)\n"
        
        prompt += f"""
REGRAS CRÍTICAS:
- Use APENAS os números exatos fornecidos
- NÃO invente dados que não existem
- Foque em RH interno, não clientes externos

RESUMO EXECUTIVO SOLICITADO:

1. SITUAÇÃO ATUAL
   - Status do atendimento interno aos funcionários
   - Principais resultados do período

2. PONTOS DE ATENÇÃO
   - Supervisores/equipes que precisam de suporte
   - Riscos operacionais identificados

3. TENDÊNCIAS OBSERVADAS
   - Padrões na demanda dos funcionários
   - Mudanças no comportamento de atendimento

4. DECISÕES NECESSÁRIAS
   - Ações que requerem aprovação executiva
   - Recursos adicionais para RH

5. PRÓXIMOS PASSOS
   - Preparações para próximo período
   - Métricas para monitoramento

FORMATO: Linguagem executiva, máximo 160 palavras, use apenas dados reais.
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
        
        prompt = f"""
Você é especialista em distribuição de carga de trabalho em RH.

CONTEXTO: Analise equipe do supervisor {supervisor_name} que atende funcionários internos.

DADOS EXATOS DA EQUIPE:
- Total de agentes: {len(agents_data)}
- Total de atendimentos: {total_tickets}
- Média por agente: {avg_tickets:.1f}

DISTRIBUIÇÃO REAL POR AGENTE:
"""
        
        for agent in agents_data:
            current = agent['current_tickets']
            change = agent.get('change', 0)
            prompt += f"• {agent['agent']['name']}: {current} atendimentos ({change:+d})\n"
        
        prompt += f"""
REGRAS:
- Use APENAS os números fornecidos
- Foque em atendimento interno de RH

ANÁLISE SOLICITADA:

1. DISTRIBUIÇÃO ATUAL
   - A carga está equilibrada entre agentes?
   - Identifique desequilíbrios problemáticos

2. IDENTIFICAÇÃO DE RISCOS
   - Agentes sobrecarregados ou subutilizados
   - Riscos para qualidade do atendimento

3. REDISTRIBUIÇÃO SUGERIDA
   - Como rebalancear a carga entre agentes?
   - Critérios para redistribuição

4. AÇÕES PREVENTIVAS
   - Como manter equilíbrio futuro?
   - Monitoramento recomendado

FORMATO: Recomendações práticas, máximo 120 palavras.
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
        
        if abs(change_percent) >= 40:
            anomalies.append(f"Variação extrema de {change_percent:+.1f}% nos atendimentos")
        
        for agent in agents:
            agent_change_percent = (agent['change'] / agent['previous_tickets'] * 100) if agent['previous_tickets'] > 0 else 0
            if abs(agent_change_percent) >= 75:
                anomalies.append(f"{agent['agent']['name']}: variação de {agent_change_percent:+.1f}%")
            if agent['current_tickets'] >= 30:
                anomalies.append(f"{agent['agent']['name']}: {agent['current_tickets']} atendimentos (alta carga)")
        
        prompt = f"""
Você é analista de dados de RH especializado em detecção de padrões atípicos.

CONTEXTO: Sistema interno onde supervisor {supervisor} atende funcionários.

DADOS EXATOS:
- Supervisor: {supervisor}
- Atendimentos atuais: {current_tickets}
- Variação: {change_percent:+.1f}%
- Agentes na equipe: {len(agents)}

ANOMALIAS DETECTADAS: {len(anomalies)}
"""
        
        for i, anomaly in enumerate(anomalies, 1):
            prompt += f"{i}. {anomaly}\n"
        
        prompt += f"""
REGRAS:
- Use APENAS os dados fornecidos
- Foque em causas internas de RH

INVESTIGAÇÃO:

1. ANÁLISE DAS ANOMALIAS
   - Possíveis causas internas
   - Eventos pontuais ou tendências?

2. CLASSIFICAÇÃO DE RISCO
   - Criticidade para operação de RH
   - Impacto no atendimento aos funcionários

3. AÇÕES IMEDIATAS
   - O que fazer agora?
   - Quem deve ser notificado?

4. PREVENÇÃO FUTURA
   - Como detectar precocemente?
   - Medidas preventivas

FORMATO: Análise objetiva, máximo 130 palavras.
"""
        return prompt.strip()
    
    @staticmethod
    def custom_insight_prompt(context: str, data_summary: str, question: str) -> str:
        """
        🎨 Prompt personalizado para insights específicos
        """
        prompt = f"""
Você é consultor sênior de RH especializado em atendimento interno.

CONTEXTO: {context}

DADOS DISPONÍVEIS:
{data_summary}

PERGUNTA ESPECÍFICA:
{question}

REGRAS:
- Use APENAS dados fornecidos
- Foque em RH interno
- Seja específico e actionável

ANÁLISE:
- Resposta fundamentada nos dados reais
- Máximo 100 palavras
- Recomendações práticas para gestão

FORMATO: Resposta direta e concreta.
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