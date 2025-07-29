# ai_reports/ai_refinements.py
"""
🔧 AI Refinements - Melhorias e otimizações para análise IA
Funções avançadas para refinar prompts e melhorar qualidade dos insights
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)


class PromptOptimizer:
    """
    🔧 Otimizador de prompts para melhor qualidade de resposta
    
    Aplica técnicas avançadas de prompt engineering para 
    maximizar a qualidade dos insights gerados pela IA
    """
    
    @staticmethod
    def enhance_global_prompt(base_prompt: str, context: Dict[str, Any]) -> str:
        """
        🌍 Melhora prompt de análise global com contexto adicional
        """
        # Adicionar contexto sazonal se disponível
        current_date = datetime.now()
        seasonal_context = PromptOptimizer._get_seasonal_context(current_date)
        
        # Adicionar contexto de urgência baseado em variações
        change_percent = context.get('change_percent', 0)
        urgency_context = PromptOptimizer._get_urgency_context(change_percent)
        
        enhanced_prompt = f"""
{base_prompt}

CONTEXTO ADICIONAL:
{seasonal_context}
{urgency_context}

INSTRUÇÕES ESPECÍFICAS:
- Seja específico sobre causas prováveis
- Quantifique o impacto sempre que possível
- Priorize ações por urgência (alta/média/baixa)
- Use linguagem clara e assertiva
- Evite generalizações vagas

FORMATO DE RESPOSTA:
1. SITUAÇÃO: [Resumo em 1 frase]
2. CAUSAS: [2-3 fatores principais]
3. IMPACTO: [Consequências operacionais]
4. AÇÕES: [Recomendações priorizadas]
"""
        return enhanced_prompt.strip()
    
    @staticmethod
    def enhance_supervisor_prompt(base_prompt: str, supervisor_data: Dict[str, Any]) -> str:
        """
        👤 Melhora prompt de análise de supervisor com insights específicos
        """
        # Analisar distribuição de carga
        agents = supervisor_data.get('current_week', {}).get('agents_performance', [])
        load_analysis = PromptOptimizer._analyze_load_distribution(agents)
        
        # Determinar foco da análise
        change_percent = supervisor_data.get('comparison', {}).get('percent_change', 0)
        analysis_focus = PromptOptimizer._get_analysis_focus(change_percent)
        
        enhanced_prompt = f"""
{base_prompt}

ANÁLISE DE DISTRIBUIÇÃO:
{load_analysis}

FOCO DA ANÁLISE:
{analysis_focus}

DIRETRIZES ESPECÍFICAS:
- Identifique o agente com melhor e pior performance
- Sugira redistribuição específica se necessário
- Avalie se há risco de burnout em algum agente
- Recomende ações concretas para próxima semana
- Considere capacidade de crescimento da equipe

ESTRUTURA DE RESPOSTA:
• PERFORMANCE GERAL: [Avaliação objetiva]
• DISTRIBUIÇÃO: [Equilibrada/Desbalanceada + detalhes]
• DESTAQUE POSITIVO: [Melhor performance]
• PONTO DE ATENÇÃO: [Maior preocupação]
• AÇÃO PRIORITÁRIA: [O que fazer esta semana]
"""
        return enhanced_prompt.strip()
    
    @staticmethod
    def enhance_strategic_prompt(base_prompt: str, strategic_context: Dict[str, Any]) -> str:
        """
        🎯 Melhora prompt estratégico com análise de tendências
        """
        # Análise de padrões entre supervisores
        supervisors_analysis = PromptOptimizer._analyze_supervisors_patterns(strategic_context)
        
        # Identificar oportunidades de otimização
        optimization_opportunities = PromptOptimizer._identify_optimization_opportunities(strategic_context)
        
        enhanced_prompt = f"""
{base_prompt}

ANÁLISE DE PADRÕES:
{supervisors_analysis}

OPORTUNIDADES IDENTIFICADAS:
{optimization_opportunities}

FRAMEWORK ESTRATÉGICO:
Aplique o framework SMART (Específico, Mensurável, Atingível, Relevante, Temporal) para cada recomendação.

CATEGORIAS DE RECOMENDAÇÃO:
1. REDISTRIBUIÇÃO: Balanceamento de carga entre equipes
2. CAPACITAÇÃO: Desenvolvimento de supervisores/agentes
3. PROCESSO: Melhorias operacionais e eficiência
4. TECNOLOGIA: Ferramentas e automação
5. GESTÃO: Políticas e governança

FORMATO OBRIGATÓRIO:
[CATEGORIA] - [RECOMENDAÇÃO ESPECÍFICA]
• Meta: [Objetivo mensurável]
• Prazo: [Timeline de implementação]
• Responsável: [Quem deve executar]
• Impacto esperado: [Resultado quantificado]
"""
        return enhanced_prompt.strip()
    
    @staticmethod
    def _get_seasonal_context(current_date: datetime) -> str:
        """📅 Determina contexto sazonal"""
        month = current_date.month
        
        if month in [12, 1, 2]:
            return "CONTEXTO: Período de final/início de ano - possível redução de atividade corporativa"
        elif month in [6, 7]:
            return "CONTEXTO: Período de férias escolares - possível aumento de demanda de suporte"
        elif month in [3, 4, 5]:
            return "CONTEXTO: Primeiro trimestre - período de planejamento e novos projetos"
        elif month in [9, 10, 11]:
            return "CONTEXTO: Último trimestre - período de intensificação e fechamento de metas"
        else:
            return "CONTEXTO: Período operacional normal"
    
    @staticmethod
    def _get_urgency_context(change_percent: float) -> str:
        """⚡ Determina contexto de urgência"""
        if abs(change_percent) >= 50:
            return "URGÊNCIA: ALTA - Mudança extrema requer ação imediata"
        elif abs(change_percent) >= 25:
            return "URGÊNCIA: MÉDIA - Mudança significativa necessita monitoramento"
        elif abs(change_percent) >= 10:
            return "URGÊNCIA: BAIXA - Variação normal, manter observação"
        else:
            return "URGÊNCIA: MÍNIMA - Situação estável"
    
    @staticmethod
    def _analyze_load_distribution(agents: List[Dict[str, Any]]) -> str:
        """📊 Analisa distribuição de carga entre agentes"""
        if not agents:
            return "Nenhum agente ativo para análise"
        
        total_tickets = sum(agent.get('current_tickets', 0) for agent in agents)
        avg_tickets = total_tickets / len(agents) if agents else 0
        
        # Classificar agentes
        overloaded = [a for a in agents if a.get('current_tickets', 0) >= avg_tickets * 1.5]
        underutilized = [a for a in agents if a.get('current_tickets', 0) <= avg_tickets * 0.5]
        balanced = [a for a in agents if a not in overloaded and a not in underutilized]
        
        analysis = f"Total agentes: {len(agents)} | Média: {avg_tickets:.1f} tickets/agente\n"
        analysis += f"• Sobrecarregados: {len(overloaded)} agentes\n"
        analysis += f"• Subutilizados: {len(underutilized)} agentes\n"
        analysis += f"• Balanceados: {len(balanced)} agentes"
        
        if overloaded:
            names = [a['agent']['name'] for a in overloaded]
            analysis += f"\n• ATENÇÃO: {', '.join(names)} com carga acima da média"
        
        return analysis
    
    @staticmethod
    def _get_analysis_focus(change_percent: float) -> str:
        """🎯 Determina foco da análise baseado na variação"""
        if change_percent >= 30:
            return "FOCO: Investigar causas do crescimento e capacidade de sustentação"
        elif change_percent <= -30:
            return "FOCO: Identificar causas da redução e plano de recuperação"
        elif 10 <= change_percent < 30:
            return "FOCO: Otimizar distribuição para manter crescimento saudável"
        elif -30 < change_percent <= -10:
            return "FOCO: Estabilizar operação e prevenir declínio maior"
        else:
            return "FOCO: Manter estabilidade e identificar oportunidades de melhoria"
    
    @staticmethod
    def _analyze_supervisors_patterns(context: Dict[str, Any]) -> str:
        """👥 Analisa padrões entre supervisores"""
        supervisors = context.get('supervisors_data', [])
        
        if len(supervisors) < 2:
            return "Dados insuficientes para análise de padrões"
        
        # Calcular métricas
        ticket_counts = [s['current_week']['total_tickets'] for s in supervisors]
        changes = [s['comparison']['percent_change'] for s in supervisors]
        
        max_tickets = max(ticket_counts)
        min_tickets = min(ticket_counts)
        variability = ((max_tickets - min_tickets) / max_tickets * 100) if max_tickets > 0 else 0
        
        avg_change = sum(changes) / len(changes)
        positive_trends = len([c for c in changes if c > 10])
        negative_trends = len([c for c in changes if c < -10])
        
        analysis = f"Variabilidade entre supervisores: {variability:.1f}%\n"
        analysis += f"Tendência média: {avg_change:+.1f}%\n"
        analysis += f"Supervisores em crescimento (+10%): {positive_trends}\n"
        analysis += f"Supervisores em declínio (-10%): {negative_trends}"
        
        return analysis
    
    @staticmethod
    def _identify_optimization_opportunities(context: Dict[str, Any]) -> str:
        """🔍 Identifica oportunidades de otimização"""
        supervisors = context.get('supervisors_data', [])
        global_stats = context.get('global_stats', {})
        
        opportunities = []
        
        # Oportunidade 1: Redistribuição
        if supervisors:
            ticket_counts = [s['current_week']['total_tickets'] for s in supervisors]
            if max(ticket_counts) > min(ticket_counts) * 2:
                opportunities.append("REDISTRIBUIÇÃO: Balancear carga entre supervisores")
        
        # Oportunidade 2: Capacitação
        declining = [s for s in supervisors if s['comparison']['percent_change'] < -20]
        if declining:
            opportunities.append("CAPACITAÇÃO: Apoiar supervisores com performance em declínio")
        
        # Oportunidade 3: Automatização
        total_tickets = global_stats.get('current_week', {}).get('total_tickets', 0)
        if total_tickets > 100:
            opportunities.append("AUTOMATIZAÇÃO: Volume alto sugere oportunidades de automação")
        
        # Oportunidade 4: Padronização
        if len(supervisors) > 2:
            opportunities.append("PADRONIZAÇÃO: Compartilhar melhores práticas entre supervisores")
        
        return "\n".join([f"• {opp}" for opp in opportunities]) if opportunities else "Nenhuma oportunidade específica identificada"


class ResponseEnhancer:
    """
    ✨ Melhorador de respostas da IA
    
    Processa e melhora as respostas da IA para torná-las
    mais actionable e estruturadas
    """
    
    @staticmethod
    def enhance_ai_response(raw_response: str, response_type: str) -> Dict[str, Any]:
        """
        ✨ Melhora resposta da IA com estruturação e validação
        
        Args:
            raw_response: Resposta original da IA
            response_type: Tipo de resposta (global, supervisor, strategic, etc.)
            
        Returns:
            Dict com resposta estruturada e melhorada
        """
        if not raw_response or raw_response.startswith("[Erro"):
            return ResponseEnhancer._create_fallback_response(response_type)
        
        # Limpar e estruturar resposta
        cleaned_response = ResponseEnhancer._clean_response(raw_response)
        
        # Extrair componentes específicos
        components = ResponseEnhancer._extract_components(cleaned_response, response_type)
        
        # Validar qualidade
        quality_score = ResponseEnhancer._assess_quality(components)
        
        # Adicionar métricas de confiança
        confidence_metrics = ResponseEnhancer._calculate_confidence(cleaned_response, components)
        
        return {
            'raw_response': raw_response,
            'cleaned_response': cleaned_response,
            'components': components,
            'quality_score': quality_score,
            'confidence_metrics': confidence_metrics,
            'enhancement_timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def _clean_response(raw_response: str) -> str:
        """🧹 Limpa e formata resposta"""
        # Remover caracteres especiais desnecessários
        cleaned = re.sub(r'\s+', ' ', raw_response)  # Múltiplos espaços
        cleaned = cleaned.strip()
        
        # Corrigir pontuação
        cleaned = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', cleaned)
        
        return cleaned
    
    @staticmethod
    def _extract_components(response: str, response_type: str) -> Dict[str, List[str]]:
        """🔍 Extrai componentes estruturados da resposta"""
        components = {
            'insights': [],
            'recommendations': [],
            'concerns': [],
            'metrics': []
        }
        
        # Dividir em sentenças
        sentences = [s.strip() for s in re.split(r'[.!?]+', response) if s.strip()]
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Classificar sentenças
            if any(word in sentence_lower for word in ['recomendo', 'sugiro', 'deve', 'deveria', 'necessário']):
                components['recommendations'].append(sentence)
            elif any(word in sentence_lower for word in ['atenção', 'cuidado', 'risco', 'problema', 'preocupa']):
                components['concerns'].append(sentence)
            elif any(word in sentence_lower for word in ['%', 'aumento', 'redução', 'tickets', 'atendimentos']):
                if len(sentence) > 15:  # Evitar sentenças muito curtas
                    components['insights'].append(sentence)
            elif len(sentence) > 20:  # Insights gerais
                components['insights'].append(sentence)
        
        # Limitar quantidade para evitar verbosidade
        for key in components:
            components[key] = components[key][:3]  # Máximo 3 itens por categoria
        
        return components
    
    @staticmethod
    def _assess_quality(components: Dict[str, List[str]]) -> Dict[str, Any]:
        """📊 Avalia qualidade da resposta"""
        total_items = sum(len(items) for items in components.values())
        
        # Critérios de qualidade
        has_recommendations = len(components['recommendations']) > 0
        has_insights = len(components['insights']) > 0
        sufficient_content = total_items >= 3
        balanced_content = len(components['insights']) >= len(components['recommendations'])
        
        score = sum([has_recommendations, has_insights, sufficient_content, balanced_content])
        
        quality_levels = {
            4: "Excelente",
            3: "Boa",
            2: "Adequada", 
            1: "Limitada",
            0: "Insuficiente"
        }
        
        return {
            'score': score,
            'max_score': 4,
            'percentage': (score / 4) * 100,
            'level': quality_levels.get(score, "Desconhecida"),
            'criteria': {
                'has_recommendations': has_recommendations,
                'has_insights': has_insights,
                'sufficient_content': sufficient_content,
                'balanced_content': balanced_content
            }
        }
    
    @staticmethod
    def _calculate_confidence(response: str, components: Dict[str, List[str]]) -> Dict[str, Any]:
        """📈 Calcula métricas de confiança"""
        # Métricas básicas
        word_count = len(response.split())
        sentence_count = len([s for s in re.split(r'[.!?]+', response) if s.strip()])
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Indicadores de especificidade
        specific_words = len(re.findall(r'\b\d+%|\b\d+\s+(tickets|atendimentos)', response.lower()))
        action_words = len(re.findall(r'\b(deve|precisa|recomendo|sugiro|implementar)', response.lower()))
        
        # Calcular confiança geral
        confidence_factors = [
            word_count >= 50,  # Resposta substantiva
            sentence_count >= 3,  # Múltiplas ideias
            specific_words > 0,  # Dados específicos
            action_words > 0,  # Ações concretas
            10 <= avg_sentence_length <= 25  # Sentenças bem formadas
        ]
        
        confidence_score = sum(confidence_factors) / len(confidence_factors)
        
        return {
            'overall_confidence': round(confidence_score * 100, 1),
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_sentence_length': round(avg_sentence_length, 1),
            'specific_references': specific_words,
            'action_oriented': action_words,
            'confidence_level': 'Alta' if confidence_score >= 0.8 else 'Média' if confidence_score >= 0.6 else 'Baixa'
        }
    
    @staticmethod
    def _create_fallback_response(response_type: str) -> Dict[str, Any]:
        """🔄 Cria resposta padrão quando IA falha"""
        fallback_responses = {
            'global': {
                'insights': ['Análise global temporariamente indisponível'],
                'recommendations': ['Monitorar tendências manualmente'],
                'concerns': [],
                'metrics': []
            },
            'supervisor': {
                'insights': ['Análise de supervisor temporariamente indisponível'],
                'recommendations': ['Revisar distribuição de agentes manualmente'],
                'concerns': [],
                'metrics': []
            },
            'strategic': {
                'insights': ['Análise estratégica temporariamente indisponível'],
                'recommendations': ['Manter monitoramento manual dos KPIs'],
                'concerns': [],
                'metrics': []
            }
        }
        
        components = fallback_responses.get(response_type, fallback_responses['global'])
        
        return {
            'raw_response': '[Análise IA indisponível]',
            'cleaned_response': 'Análise temporariamente indisponível',
            'components': components,
            'quality_score': {'score': 1, 'level': 'Fallback'},
            'confidence_metrics': {'overall_confidence': 0, 'confidence_level': 'Indisponível'},
            'enhancement_timestamp': datetime.now().isoformat(),
            'is_fallback': True
        }


# Funções de conveniência para uso direto
def optimize_global_prompt(base_prompt: str, context: Dict[str, Any]) -> str:
    """🔧 Função utilitária para otimizar prompt global"""
    return PromptOptimizer.enhance_global_prompt(base_prompt, context)


def optimize_supervisor_prompt(base_prompt: str, supervisor_data: Dict[str, Any]) -> str:
    """🔧 Função utilitária para otimizar prompt de supervisor"""
    return PromptOptimizer.enhance_supervisor_prompt(base_prompt, supervisor_data)


def enhance_ai_response(response: str, response_type: str) -> Dict[str, Any]:
    """🔧 Função utilitária para melhorar resposta da IA"""
    return ResponseEnhancer.enhance_ai_response(response, response_type)