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
            
            # Gerar análise global
            global_analysis = self._analyze_global_trends(weekly_data)
            
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
                'global_analysis': global_analysis,
                'supervisors_analysis': supervisors_analysis,
                'strategic_recommendations': strategic_recommendations,
                'summary': self._generate_executive_summary(weekly_data, global_analysis, supervisors_analysis)
            }
            
            if self.debug:
                logger.info(f"✅ Análise IA concluída - {len(supervisors_analysis)} supervisores analisados")
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"❌ Erro na análise IA: {e}")
            raise
    
    def _analyze_global_trends(self, weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        🌍 Analisa tendências globais do sistema
        """
        global_stats = weekly_data['global_stats']
        
        # Preparar dados para IA
        analysis_prompt = self._build_global_analysis_prompt(global_stats, weekly_data)
        
        # Solicitar análise da IA
        ai_response = self._query_ollama(analysis_prompt, "global_trends")
        
        return {
            'trend_analysis': ai_response,
            'key_metrics': {
                'total_tickets': global_stats['current_week']['total_tickets'],
                'change_percent': global_stats['comparison']['percent_change'],
                'trend_direction': global_stats['comparison']['trend'],
                'active_supervisors': global_stats['current_week']['active_supervisors']
            },
            'insights': self._extract_insights_from_ai_response(ai_response)
        }
    
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
        👥 Analisa performance dos agentes
        """
        agents_insights = []
        
        for agent in agents_data:
            agent_name = agent['agent']['name']
            current_tickets = agent['current_tickets']
            change = agent['change']
            
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
            
            # Detectar padrões atípicos
            change_percent = ((change / agent['previous_tickets']) * 100) if agent['previous_tickets'] > 0 else 0
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
                                   global_analysis: Dict[str, Any],
                                   supervisors_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        📋 Gera resumo executivo para coordenação usando prompt especializado
        """
        try:
            from .ai_prompts import PromptBuilder
            
            # Gerar prompt para resumo executivo
            executive_prompt = PromptBuilder.executive_summary(weekly_data, global_analysis, supervisors_analysis)
            
            # Solicitar análise da IA
            ai_summary = self._query_ollama(executive_prompt, "executive_summary")
        except ImportError:
            # Fallback se ai_prompts não estiver disponível
            ai_summary = "Resumo executivo indisponível"
        
        total_tickets = weekly_data['global_stats']['current_week']['total_tickets']
        total_change = weekly_data['global_stats']['comparison']['absolute_change']
        
        # Top performer
        top_supervisor = max(supervisors_analysis, key=lambda x: x['key_metrics']['current_tickets']) if supervisors_analysis else None
        
        # Supervisores que precisam de atenção
        attention_needed = [
            s for s in supervisors_analysis 
            if abs(s['key_metrics']['change_percent']) >= 30 or any(agent.get('needs_attention', False) for agent in s.get('agents_insights', []))
        ]
        
        return {
            'total_tickets': total_tickets,
            'weekly_change': total_change,
            'change_percent': weekly_data['global_stats']['comparison']['percent_change'],
            'top_supervisor': {
                'name': top_supervisor['supervisor_name'] if top_supervisor else 'N/A',
                'tickets': top_supervisor['key_metrics']['current_tickets'] if top_supervisor else 0
            },
            'supervisors_needing_attention': len(attention_needed),
            'overall_trend': weekly_data['global_stats']['comparison']['trend'],
            'ai_generated_summary': ai_summary,
            'key_insights': global_analysis.get('insights', [])[:3],  # Top 3 insights
            'priority_actions': len([s for s in supervisors_analysis if s['key_metrics']['change_percent'] >= 50])
        }
    
    def _build_global_analysis_prompt(self, global_stats: Dict[str, Any], weekly_data: Dict[str, Any]) -> str:
        """
        🔤 Constrói prompt para análise global usando prompts especializados
        """
        try:
            from .ai_prompts import PromptBuilder
            from .ai_refinements import PromptOptimizer
            
            # Gerar prompt base
            base_prompt = PromptBuilder.global_trend_analysis(global_stats, weekly_data)
            
            # Aplicar otimizações
            context = {
                'change_percent': global_stats['comparison']['percent_change'],
                'total_tickets': global_stats['current_week']['total_tickets']
            }
            
            optimized_prompt = PromptOptimizer.enhance_global_prompt(base_prompt, context)
            return optimized_prompt
        except ImportError:
            # Fallback básico se módulos não estiverem disponíveis
            current_tickets = global_stats['current_week']['total_tickets']
            previous_tickets = global_stats['previous_week']['total_tickets']
            change = global_stats['comparison']['absolute_change']
            change_percent = global_stats['comparison']['percent_change']
            
            period = weekly_data['metadata']['current_week']['period_label']
            
            prompt = f"""
Analise os dados semanais de atendimento e forneça insights profissionais:

PERÍODO: {period}
ATENDIMENTOS ATUAIS: {current_tickets}
ATENDIMENTOS ANTERIORES: {previous_tickets}
VARIAÇÃO: {change:+d} ({change_percent:+.1f}%)

Forneça uma análise concisa focando em:
1. Interpretação da tendência geral
2. Possíveis causas da variação
3. Impacto operacional
4. Ações recomendadas

Seja objetivo e professional. Máximo 200 palavras.
"""
            return prompt.strip()
    
    def _build_supervisor_analysis_prompt(self, supervisor_data: Dict[str, Any], weekly_data: Dict[str, Any]) -> str:
        """
        🔤 Constrói prompt para análise de supervisor usando prompts especializados
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
            previous = supervisor_data['previous_week']['total_tickets']
            change = supervisor_data['comparison']['absolute_change']
            change_percent = supervisor_data['comparison']['percent_change']
            
            agents = supervisor_data['current_week']['agents_performance']
            agents_summary = []
            for agent in agents[:3]:  # Top 3 agentes
                agents_summary.append(f"{agent['agent']['name']}: {agent['current_tickets']} atendimentos ({agent['change']:+d})")
            
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
        🔤 Constrói prompt para recomendações estratégicas usando prompts especializados
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
                change = sup['comparison']['absolute_change']
                supervisors_summary.append(f"{name}: {tickets} atendimentos ({change:+d})")
            
            prompt = f"""
Com base nos dados semanais, forneça 3-5 recomendações estratégicas para a gestão:

CENÁRIO GERAL:
- Total: {global_stats['current_week']['total_tickets']} atendimentos
- Variação: {global_stats['comparison']['absolute_change']:+d} ({global_stats['comparison']['percent_change']:+.1f}%)

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
                "system": "Você é um analista de contabilidade. NUNCA mencione férias escolares, sazonalidade ou educação. Foque APENAS em empresa de contabilidade interna. Use APENAS os dados fornecidos.",
                "stream": False,
                "options": {
                    "temperature": 0.05,  # Ainda mais baixo
                    "top_p": 0.7,
                    "max_tokens": 150,    # Ainda menor
                    "repeat_penalty": 1.3
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