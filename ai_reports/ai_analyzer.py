# ai_reports/ai_analyzer.py
"""
🤖 AI Analyzer - Integração com Ollama/Qwen 2.5
Processa dados coletados e gera insights inteligentes para relatórios
"""

import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from config import Config

# Configurar logging
logger = logging.getLogger(__name__)


class AIAnalyzer:
    """
    🤖 Analisador IA para dados de atendimento
    
    Conecta com Ollama (Qwen 2.5:3b) para gerar insights automáticos
    sobre performance de supervisores e agentes
    """
    
    def __init__(self):
        """Inicializa o analisador IA"""
        self.ollama_url = Config.OLLAMA_BASE_URL
        self.model = Config.OLLAMA_MODEL
        self.timeout = Config.OLLAMA_TIMEOUT
        self.debug = Config.AI_REPORTS_DEBUG
        
        if self.debug:
            logger.info(f"🤖 AIAnalyzer inicializado - {self.model} @ {self.ollama_url}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        🔌 Testa conexão com Ollama
        
        Returns:
            Dict com resultado do teste
        """
        try:
            # Testar endpoint de health check
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model['name'] for model in models_data.get('models', [])]
                
                model_available = any(self.model in model for model in available_models)
                
                result = {
                    'success': True,
                    'status': 'Connected',
                    'ollama_url': self.ollama_url,
                    'available_models': available_models,
                    'target_model': self.model,
                    'model_available': model_available,
                    'timestamp': datetime.now().isoformat()
                }
                
                if model_available:
                    logger.info(f"✅ Ollama conectado - Modelo {self.model} disponível")
                else:
                    logger.warning(f"⚠️ Ollama conectado - Modelo {self.model} NÃO disponível")
                
                return result
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            error_msg = f"Erro na conexão com Ollama: {e}"
            logger.error(f"❌ {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'ollama_url': self.ollama_url,
                'timestamp': datetime.now().isoformat()
            }
    
    def analyze_weekly_data(self, weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        📊 Analisa dados semanais completos com IA
        
        Args:
            weekly_data: Dados coletados pelo DataCollector
            
        Returns:
            Dict com análise completa da IA
        """
        try:
            if self.debug:
                logger.info("🧠 Iniciando análise IA dos dados semanais...")
            
            # REMOVIDO: Análise global problemática
            # global_analysis = self._analyze_global_trends(weekly_data)
            
            # Gerar análise por supervisor
            supervisors_analysis = []
            for supervisor_data in weekly_data['supervisors_data']:
                analysis = self._analyze_supervisor_performance(supervisor_data, weekly_data)
                supervisors_analysis.append(analysis)
            
            # Gerar recomendações estratégicas
            strategic_recommendations = self._generate_strategic_recommendations(weekly_data)
            
            # Compilar análise final
            ai_analysis = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'ai_model': self.model,
                    'analysis_period': weekly_data['metadata']['current_week']['period_label']
                },
                # NOVO: Dashboard executivo substitui análise global problemática
                'executive_dashboard': weekly_data.get('executive_dashboard', {}),
                'intelligent_insights': weekly_data.get('intelligent_insights', {}),
                'supervisors_analysis': supervisors_analysis,
                'strategic_recommendations': strategic_recommendations,
                'summary': self._generate_executive_summary(weekly_data, supervisors_analysis)
            }
            
            if self.debug:
                logger.info(f"✅ Análise IA concluída - {len(supervisors_analysis)} supervisores analisados")
                logger.info(f"📊 Dashboard: {len(weekly_data.get('executive_dashboard', {}).get('ranking', []))} supervisores no ranking")
                logger.info(f"🧠 Insights: {len(weekly_data.get('intelligent_insights', {}).get('performance_alerts', []))} alertas gerados")
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise IA: {e}")
            raise
    
    def _analyze_supervisor_performance(self, supervisor_data: Dict[str, Any], 
                                       weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        👤 Analisa performance individual de um supervisor
        """
        supervisor_name = supervisor_data['supervisor']['name']
        
        # Preparar dados para IA
        analysis_prompt = self._build_supervisor_analysis_prompt(supervisor_data, weekly_data)
        
        # Solicitar análise da IA
        ai_response = self._query_ollama(analysis_prompt, f"supervisor_{supervisor_name}")
        
        return {
            'supervisor_id': supervisor_data['supervisor']['id'],
            'supervisor_name': supervisor_name,
            'performance_analysis': ai_response,
            'key_metrics': {
                'current_tickets': supervisor_data['current_week']['total_tickets'],
                'change_percent': supervisor_data['comparison']['percent_change'],
                'agents_count': len(supervisor_data['current_week']['agents_performance']),
                'trend': supervisor_data['comparison']['trend']
            },
            'agents_insights': self._analyze_agents_performance(supervisor_data['current_week']['agents_performance']),
            'recommendations': self._extract_recommendations_from_ai_response(ai_response)
        }
    
    def _analyze_agents_performance(self, agents_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        👥 Analisa performance dos agentes - VERSÃO CORRIGIDA
        """
        agents_insights = []
        
        for agent in agents_data:
            agent_name = agent['agent']['name']
            current_tickets = agent.get('current_tickets', 0)
            change = agent.get('change', 0)
            
            # CORREÇÃO: Acessar previous_tickets de forma segura
            previous_tickets = 0
            if 'previous_tickets' in agent:
                previous_tickets = agent['previous_tickets']
            elif hasattr(agent, 'previous_tickets'):
                previous_tickets = agent.previous_tickets
            else:
                # Tentar calcular baseado no change
                previous_tickets = current_tickets - change if change != 0 else 0
            
            # Classificar performance
            if change > 0:
                if change >= 10:
                    performance_level = "Alta demanda"
                    status = "warning"
                else:
                    performance_level = "Crescimento estável"
                    status = "success"
            elif change < 0:
                performance_level = "Redução"
                status = "info"
            else:
                performance_level = "Estável"
                status = "neutral"
            
            # CORREÇÃO: Calcular change_percent de forma segura
            try:
                if previous_tickets > 0:
                    change_percent = (change / previous_tickets) * 100
                else:
                    change_percent = 100 if current_tickets > 0 else 0
            except (ZeroDivisionError, TypeError):
                change_percent = 0
            
            # Detectar padrões atípicos
            is_atypical = abs(change_percent) >= 50
            
            agents_insights.append({
                'agent_name': agent_name,
                'current_tickets': current_tickets,
                'change': change,
                'change_percent': round(change_percent, 1),
                'performance_level': performance_level,
                'status': status,
                'is_atypical': is_atypical,
                'needs_attention': is_atypical or current_tickets >= 50  # Mais de 50 tickets pode indicar sobrecarga
            })
        
        return agents_insights
    
    def _generate_strategic_recommendations(self, weekly_data: Dict[str, Any]) -> List[str]:
        """
        🎯 Gera recomendações estratégicas baseadas nos dados
        """
        # Preparar dados para IA
        strategy_prompt = self._build_strategy_prompt(weekly_data)
        
        # Solicitar recomendações da IA
        ai_response = self._query_ollama(strategy_prompt, "strategic_recommendations")
        
        # Extrair recomendações específicas
        recommendations = self._extract_recommendations_from_ai_response(ai_response)
        
        return recommendations
    
    def _generate_executive_summary(self, weekly_data: Dict[str, Any], 
                                    supervisors_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        📋 Gera resumo executivo para coordenação usando dados inteligentes
        
        Args:
            weekly_data: Dados coletados pelo DataCollector
            supervisors_analysis: Análises dos supervisores pela IA
            
        Returns:
            Dict com resumo executivo completo
        """
        try:
            # Usar intelligent_insights ao invés de global_analysis
            intelligent_insights = weekly_data.get('intelligent_insights', {})
            executive_dashboard = weekly_data.get('executive_dashboard', {})
            
            # Gerar resumo IA apenas se necessário
            ai_summary = "Resumo executivo baseado em dados automáticos"
            try:
                from .ai_prompts import PromptBuilder
                
                # Usar apenas dados dos supervisores para prompt (sem análise global problemática)
                if supervisors_analysis:
                    executive_prompt = PromptBuilder.executive_summary_simple(weekly_data, supervisors_analysis)
                    ai_summary = self._query_ollama(executive_prompt, "executive_summary")
            except (ImportError, Exception) as e:
                if self.debug:
                    logger.warning(f"⚠️ Prompt Builder indisponível, usando resumo automático: {e}")
            
            # Dados básicos do dashboard executivo
            total_tickets = executive_dashboard.get('total_tickets', 0)
            total_change = executive_dashboard.get('variation', 0)
            change_percent = executive_dashboard.get('variation_percent', 0)
            
            # Top performer baseado no ranking automático
            ranking = executive_dashboard.get('ranking', [])
            top_supervisor_info = {'name': 'N/A', 'tickets': 0}
            if ranking:
                # Parse do primeiro item do ranking: "1º Nome: 58 (-10)"
                top_entry = ranking[0]
                try:
                    parts = top_entry.split(': ')
                    if len(parts) >= 2:
                        name_part = parts[0].split(' ', 1)[1]  # Remove "1º "
                        tickets_part = parts[1].split(' ')[0]  # Pega só o número
                        top_supervisor_info = {
                            'name': name_part,
                            'tickets': int(tickets_part)
                        }
                except (ValueError, IndexError):
                    pass
            
            # Supervisores que precisam de atenção baseado em insights automáticos
            alerts = intelligent_insights.get('performance_alerts', [])
            attention_needed_count = len(alerts)
            
            # Determinar tendência
            if change_percent > 5:
                trend = 'crescimento'
            elif change_percent < -5:
                trend = 'queda'
            else:
                trend = 'estável'
            
            # Ações prioritárias baseadas em alertas
            priority_actions = len([alert for alert in alerts if 'requer atenção' in alert])
            
            return {
                'total_tickets': total_tickets,
                'weekly_change': total_change,
                'change_percent': change_percent,
                'top_supervisor': top_supervisor_info,
                'supervisors_needing_attention': attention_needed_count,
                'overall_trend': trend,
                'ai_generated_summary': ai_summary,
                'key_insights': intelligent_insights.get('concentration_patterns', [])[:3],  # Top 3 padrões
                'priority_actions': priority_actions,
                'ranking_summary': ranking[:3],  # Top 3 do ranking
                'alerts_summary': alerts[:3]  # Top 3 alertas
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar resumo executivo: {e}")
            
            # Fallback com dados mínimos
            return {
                'total_tickets': weekly_data.get('global_stats', {}).get('current_week', {}).get('total_tickets', 0),
                'weekly_change': 0,
                'change_percent': 0,
                'top_supervisor': {'name': 'N/A', 'tickets': 0},
                'supervisors_needing_attention': 0,
                'overall_trend': 'indisponível',
                'ai_generated_summary': 'Resumo executivo indisponível devido a erro técnico',
                'key_insights': [],
                'priority_actions': 0,
                'ranking_summary': [],
                'alerts_summary': []
            }
    
    def _build_supervisor_analysis_prompt(self, supervisor_data: Dict[str, Any], weekly_data: Dict[str, Any]) -> str:
        """
        🔤 Constrói prompt para análise de supervisor usando prompts especializados - VERSÃO CORRIGIDA
        """
        try:
            from .ai_prompts import PromptBuilder
            from .ai_refinements import PromptOptimizer
            
            # Calcular ranking do supervisor
            all_supervisors = weekly_data.get('supervisors_data', [])
            ranking = None
            
            if all_supervisors:
                sorted_supervisors = sorted(all_supervisors, key=lambda x: x['current_week']['total_tickets'], reverse=True)
                for i, sup in enumerate(sorted_supervisors, 1):
                    if sup['supervisor']['id'] == supervisor_data['supervisor']['id']:
                        ranking = i
                        break
            
            # Gerar prompt base
            base_prompt = PromptBuilder.supervisor_performance_analysis(supervisor_data, weekly_data, ranking)
            
            # Aplicar otimizações
            optimized_prompt = PromptOptimizer.enhance_supervisor_prompt(base_prompt, supervisor_data)
            return optimized_prompt
        except ImportError:
            # Fallback básico se módulos não estiverem disponíveis
            supervisor_name = supervisor_data['supervisor']['name']
            current = supervisor_data['current_week']['total_tickets']
            
            # CORREÇÃO: Acessar dados do período anterior de forma segura
            previous = supervisor_data.get('previous_week', {}).get('total_tickets', 0)
            change = supervisor_data.get('comparison', {}).get('absolute_change', 0)
            change_percent = supervisor_data.get('comparison', {}).get('percent_change', 0)
            
            agents = supervisor_data['current_week']['agents_performance']
            agents_summary = []
            for agent in agents[:3]:  # Top 3 agentes
                agent_change = agent.get('change', 0)
                agents_summary.append(f"{agent['agent']['name']}: {agent['current_tickets']} atendimentos ({agent_change:+d})")
            
            period = weekly_data['metadata']['current_week']['period_label']
            
            prompt = f"""
Analise a performance do supervisor {supervisor_name} no período {period}:

SUPERVISOR: {supervisor_name}
ATENDIMENTOS: {current} (anterior: {previous})
VARIAÇÃO: {change:+d} ({change_percent:+.1f}%)

PRINCIPAIS AGENTES:
{chr(10).join(agents_summary)}

Forneça análise focada em:
1. Avaliação da performance
2. Análise da distribuição entre agentes
3. Identificação de padrões
4. Recomendações específicas

Seja conciso e actionable. Máximo 150 palavras.
"""
            return prompt.strip()
    
    def _build_strategy_prompt(self, weekly_data: Dict[str, Any]) -> str:
        """
        🔤 Constrói prompt para recomendações estratégicas usando prompts especializados - VERSÃO CORRIGIDA
        """
        try:
            from .ai_prompts import PromptBuilder
            from .ai_refinements import PromptOptimizer
            
            # Gerar prompt base
            base_prompt = PromptBuilder.strategic_recommendations(weekly_data)
            
            # Aplicar otimizações
            strategic_context = {
                'supervisors_data': weekly_data['supervisors_data'],
                'global_stats': weekly_data['global_stats']
            }
            
            optimized_prompt = PromptOptimizer.enhance_strategic_prompt(base_prompt, strategic_context)
            return optimized_prompt
        except ImportError:
            # Fallback básico se módulos não estiverem disponíveis
            supervisors = weekly_data['supervisors_data']
            global_stats = weekly_data['global_stats']
            
            # Resumo dos supervisores
            supervisors_summary = []
            for sup in supervisors[:5]:  # Top 5
                name = sup['supervisor']['name']
                tickets = sup['current_week']['total_tickets']
                change = sup.get('comparison', {}).get('absolute_change', 0)
                supervisors_summary.append(f"{name}: {tickets} atendimentos ({change:+d})")
            
            # CORREÇÃO: Acessar dados globais de forma segura
            current_total = global_stats.get('current_week', {}).get('total_tickets', 0)
            change_abs = global_stats.get('comparison', {}).get('absolute_change', 0)
            change_pct = global_stats.get('comparison', {}).get('percent_change', 0)
            
            prompt = f"""
Com base nos dados semanais, forneça 3-5 recomendações estratégicas para a gestão:

CENÁRIO GERAL:
- Total: {current_total} atendimentos
- Variação: {change_abs:+d} ({change_pct:+.1f}%)

SUPERVISORES:
{chr(10).join(supervisors_summary)}

Foque em:
1. Redistribuição de carga
2. Apoio a supervisores
3. Otimização de processos
4. Prevenção de problemas

Seja específico e prático. Uma recomendação por linha.
"""
            return prompt.strip()
    
    def _query_ollama(self, prompt: str, context: str = "") -> str:
        """
        🤖 Faz consulta ao Ollama com melhorias na resposta
        
        Args:
            prompt: Prompt para a IA
            context: Contexto da consulta (para logs)
            
        Returns:
            Resposta da IA melhorada
        """
        try:
            if self.debug:
                logger.info(f"🤖 Consultando Ollama - {context}")
            
            # Adicionar system prompt restritivo
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": "Você é supervisor de contabil. NUNCA mencione férias escolares, sazonalidade ou educação. Foque APENAS em empresa de contabilidade interna. Use APENAS dados fornecidos.",
                "stream": False,
                "options": {
                    "temperature": 0.05,      # Reduzido de 0.3 para 0.05
                    "top_p": 0.7,            # Reduzido de 0.9 para 0.7  
                    "max_tokens": 150,       # Reduzido de 400 para 150
                    "repeat_penalty": 1.3,   # Aumentado de 1.1 para 1.3
                    "stop": ["ANÁLISE:", "CONTEXTO:", "DADOS:", "INSTRUÇÕES:"]
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                raw_response = result.get('response', '').strip()
                
                # Aplicar melhorias na resposta
                try:
                    from .ai_refinements import ResponseEnhancer
                    enhanced = ResponseEnhancer.enhance_ai_response(raw_response, context)
                    
                    # Log qualidade da resposta se em debug
                    if self.debug:
                        quality = enhanced['quality_score']
                        confidence = enhanced['confidence_metrics']
                        logger.info(f"✅ IA resposta - Qualidade: {quality['level']} ({quality['score']}/4), Confiança: {confidence['confidence_level']}")
                    
                    # Retornar resposta limpa
                    final_response = enhanced['cleaned_response']
                    
                    # Se resposta for muito curta, usar resposta original
                    if len(final_response) < 50 and len(raw_response) > len(final_response):
                        final_response = raw_response
                    
                    return final_response
                except ImportError:
                    # Fallback se módulo de refinements não estiver disponível
                    return raw_response
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            error_msg = f"Erro na consulta Ollama ({context}): {e}"
            logger.error(f"❌ {error_msg}")
            
            # Fallback melhorado
            try:
                from .ai_refinements import ResponseEnhancer
                fallback = ResponseEnhancer._create_fallback_response(context)
                return fallback['cleaned_response']
            except ImportError:
                return f"[Erro na análise IA: {e}]"
    
    def _extract_insights_from_ai_response(self, ai_response: str) -> List[str]:
        """
        📝 Extrai insights principais da resposta da IA
        """
        if not ai_response or ai_response.startswith("[Erro"):
            return ["Análise indisponível"]
        
        # Dividir em sentenças e filtrar insights relevantes
        sentences = [s.strip() for s in ai_response.split('.') if s.strip()]
        insights = []
        
        for sentence in sentences[:4]:  # Máximo 4 insights
            if len(sentence) > 20 and not sentence.startswith("["):
                insights.append(sentence + ".")
        
        return insights if insights else ["Nenhum insight específico identificado"]
    
    def _extract_recommendations_from_ai_response(self, ai_response: str) -> List[str]:
        """
        📋 Extrai recomendações da resposta da IA
        """
        if not ai_response or ai_response.startswith("[Erro"):
            return ["Análise indisponível"]
        
        # Procurar por listas numeradas ou com bullets
        lines = ai_response.split('\n')
        recommendations = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Limpar numeração/bullets
                clean_line = line.lstrip('0123456789.-• ').strip()
                if len(clean_line) > 10:
                    recommendations.append(clean_line)
        
        # Se não encontrou listas, usar sentenças
        if not recommendations:
            sentences = [s.strip() for s in ai_response.split('.') if s.strip()]
            recommendations = [s + "." for s in sentences[:3] if len(s) > 20]
        
        return recommendations if recommendations else ["Nenhuma recomendação específica"]


# Função de conveniência para uso externo
def analyze_weekly_data(weekly_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    🔧 Função utilitária para análise de dados semanais
    
    Args:
        weekly_data: Dados coletados pelo DataCollector
        
    Returns:
        Análise completa da IA
    """
    analyzer = AIAnalyzer()
    return analyzer.analyze_weekly_data(weekly_data)


def test_ai_connection() -> Dict[str, Any]:
    """
    🧪 Função utilitária para testar conexão com IA
    
    Returns:
        Resultado do teste de conexão
    """
    analyzer = AIAnalyzer()
    return analyzer.test_connection()