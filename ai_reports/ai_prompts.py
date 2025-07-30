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
    
    Gera prompts otimizados para análise de escalações em empresa de contabilidade
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
Você é um analista de operações de uma empresa de contabilidade.

CONTEXTO DO SISTEMA:
- AtendePro registra escalações de casos complexos para supervisores
- Agentes atendem clientes, quando não conseguem resolver, escalam para supervisores
- Também registra atendimentos internos (questões trabalhistas dos funcionários)
- Cada atendimento representa um caso que exigiu conhecimento especializado

DADOS REAIS DO PERÍODO:
- Período analisado: {period}
- Total de escalações/atendimentos: {current_tickets}
- Período anterior: {previous_tickets}
- Variação: {change:+d} ({change_percent:+.1f}%)
- Supervisores ativos: {active_supervisors}

ANÁLISE SOLICITADA:

1. INTERPRETAÇÃO DA VARIAÇÃO
   - O que significa {change_percent:+.1f}% de variação nas escalações?
   - Indica melhoria ou piora na autonomia dos agentes?

2. POSSÍVEIS CAUSAS
   - Agentes precisando mais suporte técnico?
   - Casos mais complexos surgindo?
   - Mudanças na legislação contábil?

3. IMPACTO OPERACIONAL
   - Como isso afeta a carga dos supervisores?
   - Indica necessidade de treinamento dos agentes?

4. RECOMENDAÇÕES
   - Ações para otimizar escalações
   - Como melhorar autonomia dos agentes

FORMATO: Use apenas os dados fornecidos, máximo 140 palavras, foque em contabilidade.
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
Você é um gestor de operações de contabilidade analisando escalações de casos.

CONTEXTO:
- {supervisor} é supervisor que resolve casos complexos escalados pelos agentes
- Agentes escalam quando não conseguem resolver problemas dos clientes
- Sistema também registra atendimentos internos (questões de funcionários)

DADOS EXATOS:
- Supervisor: {supervisor} {ranking_text}
- Período: {weekly_data['metadata']['current_week']['period_label']}
- Escalações recebidas: {current} (anterior: {previous})
- Variação: {change:+d} ({change_percent:+.1f}%)
- Agentes que escalaram: {agents_count}

ESCALAÇÕES POR AGENTE:
"""
        
        # Adicionar dados dos agentes
        for agent in agents[:5]:  # Top 5 agentes
            agent_change = agent['change']
            prompt += f"• {agent['agent']['name']}: {agent['current_tickets']} escalações ({agent_change:+d})\n"
        
        prompt += f"""
ANÁLISE ESPECÍFICA:

1. PERFORMANCE DO SUPERVISOR
   - {current} escalações indica sobrecarga ou demanda normal?
   - Variação de {change_percent:+.1f}% é preocupante?

2. ANÁLISE DOS AGENTES
   - Quais agentes estão escalando mais casos?
   - Indica necessidade de treinamento específico?
   - Algum agente demonstrando evolução/autonomia?

3. DISTRIBUIÇÃO DE CARGA
   - A distribuição entre agentes está equilibrada?
   - Algum agente pode estar sobrecarregado ou ocioso?

4. RECOMENDAÇÕES PRÁTICAS
   - Como reduzir escalações desnecessárias?
   - Quais agentes precisam de suporte adicional?
   - Ações para próxima semana

FORMATO: Use apenas dados fornecidos, máximo 120 palavras, foque em contabilidade.
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
        high_load = [s for s in supervisors if s['comparison']['percent_change'] >= 20]
        decreasing_load = [s for s in supervisors if s['comparison']['percent_change'] <= -20]
        stable = [s for s in supervisors if abs(s['comparison']['percent_change']) < 20]
        
        # Supervisor com mais escalações
        top_supervisor = max(supervisors, key=lambda x: x['current_week']['total_tickets']) if supervisors else None
        
        prompt = f"""
Você é diretor de operações de empresa de contabilidade analisando escalações.

CONTEXTO:
- Sistema registra casos complexos escalados pelos agentes para supervisores
- Cada escalação indica que agente não conseguiu resolver sozinho
- Meta: reduzir escalações melhorando autonomia dos agentes

DADOS DO SISTEMA:
- Período: {weekly_data['metadata']['current_week']['period_label']}
- Total de escalações: {global_stats['current_week']['total_tickets']}
- Variação geral: {global_stats['comparison']['absolute_change']:+d} ({global_stats['comparison']['percent_change']:+.1f}%)
- Supervisores ativos: {total_supervisors}

DISTRIBUIÇÃO DE CARGA:
- Supervisores com aumento de escalações (+20%): {len(high_load)}
- Supervisores com carga estável: {len(stable)}
- Supervisores com redução de escalações (-20%): {len(decreasing_load)}
"""
        
        if top_supervisor:
            prompt += f"• Maior volume: {top_supervisor['supervisor']['name']} ({top_supervisor['current_week']['total_tickets']} escalações)\n"
        
        prompt += f"""
RECOMENDAÇÕES ESTRATÉGICAS:

1. REDISTRIBUIÇÃO DE CARGA
   - Como balancear escalações entre supervisores?
   - Realocação de agentes entre equipes?

2. CAPACITAÇÃO DE AGENTES
   - Quais agentes precisam de treinamento técnico?
   - Temas de contabilidade que geram mais escalações?

3. OTIMIZAÇÃO DE PROCESSOS
   - Como reduzir escalações desnecessárias?
   - Ferramentas para aumentar autonomia dos agentes?

4. MONITORAMENTO DE PERFORMANCE
   - Indicadores para detectar sobrecarga precocemente?
   - Métricas de evolução dos agentes?

5. GESTÃO DE COMPLEXIDADE
   - Como identificar casos que sempre escalam?
   - Especialização de supervisores por tipo de problema?

FORMATO: 5 recomendações específicas, máximo 160 palavras, foque em contabilidade.
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
                           abs(s['key_metrics']['change_percent']) >= 25]
        else:
            top_performer = None
            high_variance = []
        
        prompt = f"""
Você é executivo de empresa de contabilidade analisando escalações operacionais.

CONTEXTO:
- Sistema registra casos complexos que agentes escalam para supervisores
- Escalações indicam necessidade de conhecimento especializado
- Meta empresarial: desenvolver autonomia dos agentes

DADOS EXECUTIVOS - {period}:
- Total de escalações: {total_tickets}
- Variação: {change:+d} ({change_percent:+.1f}%)
- Supervisores monitorados: {len(supervisors_analysis)}
- Supervisores com variação alta: {len(high_variance)}
"""
        
        if top_performer:
            prompt += f"• Maior volume: {top_performer['supervisor_name']} ({top_performer['key_metrics']['current_tickets']} escalações)\n"
        
        prompt += f"""
RESUMO EXECUTIVO:

1. STATUS OPERACIONAL
   - Situação geral das escalações na contabilidade
   - Impacto na produtividade dos supervisores

2. PONTOS CRÍTICOS
   - Supervisores sobrecarregados com escalações
   - Agentes que precisam de desenvolvimento urgente

3. TENDÊNCIAS IDENTIFICADAS
   - Padrões nas escalações (tipos de casos, complexidade)
   - Evolução da autonomia dos agentes

4. DECISÕES NECESSÁRIAS
   - Investimentos em treinamento
   - Redistribuição de equipes ou especialização

5. PRÓXIMAS AÇÕES
   - Metas para redução de escalações
   - Plano de capacitação dos agentes

FORMATO: Linguagem executiva, máximo 140 palavras, foque em resultados de contabilidade.
"""
        return prompt.strip()
    
    @staticmethod
    def agent_workload_analysis(agents_data: List[Dict[str, Any]], 
                               supervisor_name: str) -> str:
        """
        👥 Prompt para análise de carga de trabalho dos agentes
        """
        if not agents_data:
            return "Nenhuma escalação de agente registrada."
        
        total_tickets = sum(agent['current_tickets'] for agent in agents_data)
        avg_tickets = total_tickets / len(agents_data) if agents_data else 0
        
        prompt = f"""
Você é gestor de equipe de contabilidade analisando escalações dos agentes.

CONTEXTO:
- Agentes escalam casos complexos para supervisor {supervisor_name}
- Escalações indicam dificuldade técnica ou casos incomuns
- Meta: desenvolver autonomia dos agentes

DADOS DA EQUIPE:
- Agentes ativos: {len(agents_data)}
- Total de escalações: {total_tickets}
- Média por agente: {avg_tickets:.1f}

ESCALAÇÕES POR AGENTE:
"""
        
        for agent in agents_data:
            current = agent['current_tickets']
            change = agent.get('change', 0)
            status = "🔴" if current >= avg_tickets * 1.8 else "🟡" if current >= avg_tickets * 1.2 else "🟢"
            prompt += f"• {status} {agent['agent']['name']}: {current} escalações ({change:+d})\n"
        
        prompt += f"""
ANÁLISE DE DESENVOLVIMENTO:

1. AUTONOMIA DOS AGENTES
   - Quais agentes estão evoluindo (menos escalações)?
   - Quais agentes precisam de mais suporte técnico?

2. DISTRIBUIÇÃO DE DIFICULDADES
   - Carga de escalações está equilibrada?
   - Algum agente está sobrecarregando supervisores?

3. OPORTUNIDADES DE TREINAMENTO
   - Temas de contabilidade que geram mais escalações?
   - Agentes prontos para casos mais complexos?

4. AÇÕES RECOMENDADAS
   - Redistribuição de responsabilidades?
   - Treinamentos específicos necessários?

FORMATO: Recomendações práticas para contabilidade, máximo 100 palavras.
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
            anomalies.append(f"Variação extrema de {change_percent:+.1f}% nas escalações")
        
        if current_tickets >= 40:
            anomalies.append(f"Volume alto: {current_tickets} escalações (possível sobrecarga)")
        
        for agent in agents:
            if agent['current_tickets'] >= 15:
                anomalies.append(f"{agent['agent']['name']}: {agent['current_tickets']} escalações (necessita treinamento?)")
            
            agent_change_percent = (agent['change'] / agent['previous_tickets'] * 100) if agent['previous_tickets'] > 0 else 0
            if agent_change_percent >= 100:
                anomalies.append(f"{agent['agent']['name']}: aumento de {agent_change_percent:.0f}% nas escalações")
        
        prompt = f"""
Você é analista de qualidade de empresa de contabilidade.

CONTEXTO:
- {supervisor} recebe escalações de casos complexos dos agentes
- Anomalias podem indicar problemas de treinamento ou sobrecarga

DADOS:
- Supervisor: {supervisor}
- Escalações atuais: {current_tickets}
- Variação: {change_percent:+.1f}%
- Agentes na equipe: {len(agents)}

ANOMALIAS DETECTADAS: {len(anomalies)}
"""
        
        for i, anomaly in enumerate(anomalies, 1):
            prompt += f"{i}. {anomaly}\n"
        
        prompt += f"""
INVESTIGAÇÃO:

1. CAUSAS POSSÍVEIS
   - Casos mais complexos aparecendo?
   - Agentes precisando de mais treinamento?
   - Mudanças na legislação contábil?

2. IMPACTO OPERACIONAL
   - Risco de sobrecarga do supervisor?
   - Qualidade do atendimento comprometida?

3. AÇÕES IMEDIATAS
   - Redistribuição temporária de casos?
   - Suporte adicional necessário?

4. PREVENÇÃO
   - Treinamentos específicos?
   - Monitoramento mais frequente?

FORMATO: Análise objetiva para contabilidade, máximo 110 palavras.
"""
        return prompt.strip()
    
    @staticmethod
    def custom_insight_prompt(context: str, data_summary: str, question: str) -> str:
        """
        🎨 Prompt personalizado para insights específicos
        """
        prompt = f"""
Você é consultor especializado em operações de contabilidade.

CONTEXTO: {context}

DADOS: {data_summary}

PERGUNTA: {question}

REGRAS:
- Foque em escalações e desenvolvimento de agentes
- Use apenas dados fornecidos
- Contexto: empresa de contabilidade

ANÁLISE: Resposta prática, máximo 80 palavras.
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