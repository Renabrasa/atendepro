# ai_reports/ai_analyzer.py
"""
🤖 AI Analyzer - Sistema AI Reports
Análise inteligente de dados de autonomia usando Ollama
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class AutonomyAIAnalyzer:
    """Analisa dados de autonomia usando IA local (Ollama)"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "llama3.2:3b"  # Modelo padrão (pode ser configurado)
        
    def test_connection(self) -> Dict[str, Any]:
        """Testa conexão com Ollama"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return {
                    'success': True,
                    'available_models': [m['name'] for m in models],
                    'status': 'Ollama conectado com sucesso'
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'status': 'Erro na conexão'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status': 'Ollama indisponível'
            }
    
    def analyze_weekly_data(self, autonomy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Análise completa dos dados semanais de autonomia
        Gera os 4 blocos integrados do relatório
        """
        try:
            # Verifica se há dados para analisar
            if not autonomy_data.get('supervisors'):
                return self._generate_empty_analysis()
            
            # Gera análise dos 4 blocos
            analysis_result = {
                'block_1_radar': self._analyze_autonomy_radar(autonomy_data),
                'block_2_training_matrix': self._analyze_training_matrix(autonomy_data),
                'block_3_productivity': self._analyze_productivity_evolution(autonomy_data),
                'block_4_conclusions': self._analyze_strategic_conclusions(autonomy_data),
                'executive_summary': self._generate_executive_summary(autonomy_data),
                'analysis_timestamp': datetime.now().isoformat(),
                'ai_model_used': self.model
            }
            
            return {
                'success': True,
                'analysis': analysis_result,
                'data_quality': self._assess_data_quality(autonomy_data)
            }
            
        except Exception as e:
            logger.error(f"Erro na análise IA: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis': self._generate_fallback_analysis(autonomy_data)
            }
    
    def _analyze_autonomy_radar(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Bloco 1: Radar de Autonomia - Dashboard Executivo"""
        
        # Prepara dados para análise
        supervisors = data.get('supervisors', [])
        global_stats = data.get('global_stats', {})
        
        # Identifica alertas críticos e destaques
        critical_agents = []
        positive_highlights = []
        
        for supervisor in supervisors:
            for agent in supervisor.get('agents', []):
                if agent.get('risk_level') == 'critical':
                    critical_agents.append({
                        'supervisor': supervisor.get('supervisor_name'),
                        'agent': agent.get('agent_name'),
                        'requests': agent.get('current_requests'),
                        'variation': agent.get('variation_percent'),
                        'diagnosis': self._generate_diagnosis(agent)
                    })
                elif agent.get('is_improving') and agent.get('current_requests') <= 2:
                    positive_highlights.append({
                        'supervisor': supervisor.get('supervisor_name'),
                        'agent': agent.get('agent_name'),
                        'requests': agent.get('current_requests'),
                        'variation': agent.get('variation_percent'),
                        'recognition': "Evoluiu para autonomia"
                    })
        
        # Ranking de supervisores por eficiência
        supervisors_ranking = sorted(
            supervisors,
            key=lambda x: (x.get('autonomy_rate', 0), -x.get('total_attendances_current', 999)),
            reverse=True
        )
        
        return {
            'total_requests': global_stats.get('total_attendances_current', 0),
            'variation_requests': global_stats.get('variation_percent', 0),
            'general_autonomy': self._calculate_general_autonomy(supervisors),
            'supervisor_ranking': len(supervisors_ranking),
            'critical_alerts': critical_agents[:3],  # Top 3 críticos
            'positive_highlights': positive_highlights[:2],  # Top 2 positivos
            'executive_diagnosis': self._generate_executive_diagnosis(global_stats, critical_agents)
        }
    
    def _analyze_training_matrix(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Bloco 2: Matriz de Capacitação - Gaps Identificados"""
        
        supervisors = data.get('supervisors', [])
        
        # Identifica agentes prioritários para treinamento
        priority_agents = []
        
        for supervisor in supervisors:
            for agent in supervisor.get('agents', []):
                if agent.get('risk_level') in ['critical', 'attention']:
                    priority_agents.append({
                        'supervisor': supervisor.get('supervisor_name'),
                        'agent': agent.get('agent_name'),
                        'requests': agent.get('current_requests'),
                        'gaps': agent.get('probable_gaps', []),
                        'risk_level': agent.get('risk_level'),
                        'action': agent.get('recommended_action')
                    })
        
        # Ordena por prioridade (críticos primeiro, depois por volume)
        priority_agents.sort(key=lambda x: (
            0 if x['risk_level'] == 'critical' else 1,
            -x['requests']
        ))
        
        # Calcula distribuição de tempo por supervisor
        time_distribution = []
        for supervisor in supervisors:
            agents_time = []
            total_requests = supervisor.get('total_attendances_current', 0)
            
            for agent in supervisor.get('agents', []):
                agent_requests = agent.get('current_requests', 0)
                time_percent = round((agent_requests / total_requests * 100), 1) if total_requests > 0 else 0
                
                agents_time.append({
                    'agent': agent.get('agent_name'),
                    'time_percent': time_percent,
                    'status': agent.get('autonomy_status', 'Normal')
                })
            
            time_distribution.append({
                'supervisor': supervisor.get('supervisor_name'),
                'strategic_time': supervisor.get('strategic_time_percent', 0),
                'agents_time': sorted(agents_time, key=lambda x: x['time_percent'], reverse=True)[:3]
            })
        
        return {
            'priority_agents': priority_agents[:5],  # Top 5 prioritários
            'time_distribution': time_distribution,
            'identified_gaps': self._aggregate_identified_gaps(priority_agents),
            'training_recommendations': self._generate_training_recommendations(priority_agents)
        }
    
    def _analyze_productivity_evolution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Bloco 3: Dashboard de Produtividade - Evolução Visual"""
        
        supervisors = data.get('supervisors', [])
        
        evolution_analysis = []
        
        for supervisor in supervisors:
            # Análise de tendência do supervisor
            trend = supervisor.get('evolution_trend', '📊 ESTÁVEL')
            current_total = supervisor.get('total_attendances_current', 0)
            previous_total = supervisor.get('total_attendances_previous', 0)
            
            # Análise por agente com barras visuais
            agents_evolution = []
            for agent in supervisor.get('agents', []):
                current_req = agent.get('current_requests', 0)
                previous_req = agent.get('previous_requests', 0)
                variation = agent.get('variation_percent', 0)
                
                # Gera barra visual baseada no volume
                visual_bar = self._generate_visual_bar(current_req)
                
                # Status baseado em risco e variação
                if agent.get('risk_level') == 'critical':
                    status = '🔴 CRÍTICO'
                elif agent.get('risk_level') == 'attention':
                    status = '🟡 ATENÇÃO'
                else:
                    status = '🟢 AUTÔNOMO'
                
                agents_evolution.append({
                    'agent_name': agent.get('agent_name'),
                    'current_requests': current_req,
                    'variation': variation,
                    'visual_bar': visual_bar,
                    'status': status,
                    'status_description': self._get_status_description(agent)
                })
            
            evolution_analysis.append({
                'supervisor_name': supervisor.get('supervisor_name'),
                'trend': trend,
                'current_total': current_total,
                'previous_total': previous_total,
                'agents': sorted(agents_evolution, key=lambda x: x['current_requests'], reverse=True)
            })
        
        return {
            'supervisors_evolution': evolution_analysis,
            'period_summary': self._generate_period_summary(data),
            'visual_insights': self._generate_visual_insights(evolution_analysis)
        }
    
    def _analyze_strategic_conclusions(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Bloco 4: Conclusões IA & Plano de Ação"""
        
        # Gera prompt estruturado para análise IA
        analysis_prompt = self._build_strategic_analysis_prompt(data)
        
        # Chama IA para análise estratégica
        ai_analysis = self._query_ollama_for_strategic_insights(analysis_prompt)
        
        # Gera plano de ação de 7 dias
        action_plan = self._generate_7_day_action_plan(data)
        
        # Calcula resultados esperados
        expected_results = self._calculate_expected_results(data)
        
        return {
            'ai_diagnosis': ai_analysis.get('diagnosis', 'Análise em processamento'),
            'pattern_insights': ai_analysis.get('patterns', []),
            'action_plan_7_days': action_plan,
            'expected_results': expected_results,
            'strategic_recommendations': ai_analysis.get('recommendations', []),
            'risk_assessment': self._assess_overall_risk(data)
        }
    
    def _query_ollama_for_strategic_insights(self, prompt: str) -> Dict[str, Any]:
        """Consulta Ollama para insights estratégicos"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Mais determinístico
                    "top_k": 20,
                    "top_p": 0.8
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get('response', '')
                
                # Tenta extrair estrutura da resposta
                return self._parse_ai_response(analysis_text)
            else:
                logger.warning(f"Ollama retornou status {response.status_code}")
                return self._generate_fallback_insights()
                
        except Exception as e:
            logger.error(f"Erro ao consultar Ollama: {e}")
            return self._generate_fallback_insights()
    
    def _build_strategic_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Constrói prompt estruturado para análise estratégica"""
        
        supervisors = data.get('supervisors', [])
        global_stats = data.get('global_stats', {})
        
        # Identifica padrões principais
        critical_count = sum(1 for sup in supervisors for agent in sup.get('agents', []) 
                           if agent.get('risk_level') == 'critical')
        
        improving_count = sum(1 for sup in supervisors for agent in sup.get('agents', []) 
                            if agent.get('is_improving', False))
        
        total_requests = global_stats.get('total_attendances_current', 0)
        variation = global_stats.get('variation_percent', 0)
        
        prompt = f"""
Você é um especialista em gestão de equipes de contabilidade. Analise os dados abaixo e forneça insights estratégicos.

DADOS OPERACIONAIS:
- Total de solicitações: {total_requests}
- Variação semanal: {variation:+.1f}%
- Agentes críticos (>6 solicitações): {critical_count}
- Agentes melhorando: {improving_count}
- Total de supervisores: {len(supervisors)}

CONTEXTO DO NEGÓCIO:
- Cada solicitação = deficiência de conhecimento técnico
- Meta: máximo 2 solicitações/agente/semana (autonomia)
- Áreas técnicas problemáticas: eSocial, SPED, Report Builder, Alterdata

ANALISE E RESPONDA:

1. DIAGNÓSTICO (2-3 frases):
[Análise dos padrões identificados considerando o contexto contábil]

2. PADRÕES IDENTIFICADOS (3-4 itens):
- [Padrão 1]
- [Padrão 2]
- [Padrão 3]

3. RECOMENDAÇÕES ESTRATÉGICAS (3-4 ações):
- [Recomendação 1]
- [Recomendação 2]
- [Recomendação 3]

Seja específico, prático e focado em resultados mensuráveis.
"""
        
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Extrai estrutura da resposta da IA"""
        try:
            # Parsing simples baseado em padrões
            lines = response_text.strip().split('\n')
            
            diagnosis = ""
            patterns = []
            recommendations = []
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if "DIAGNÓSTICO" in line.upper():
                    current_section = "diagnosis"
                elif "PADRÕES" in line.upper() or "PADROES" in line.upper():
                    current_section = "patterns"
                elif "RECOMENDAÇÕES" in line.upper() or "RECOMENDACOES" in line.upper():
                    current_section = "recommendations"
                elif line.startswith('-') or line.startswith('•'):
                    if current_section == "patterns":
                        patterns.append(line[1:].strip())
                    elif current_section == "recommendations":
                        recommendations.append(line[1:].strip())
                elif current_section == "diagnosis" and not line.startswith(('1.', '2.', '3.')):
                    diagnosis += line + " "
            
            return {
                'diagnosis': diagnosis.strip() or "Operação dentro da normalidade esperada.",
                'patterns': patterns or ["Padrão de atendimentos estável", "Distribuição equilibrada entre supervisores"],
                'recommendations': recommendations or ["Manter acompanhamento atual", "Monitorar agentes críticos semanalmente"]
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar resposta IA: {e}")
            return self._generate_fallback_insights()
    
    def _generate_fallback_insights(self) -> Dict[str, Any]:
        """Gera insights básicos quando IA não está disponível"""
        return {
            'diagnosis': "Sistema operando normalmente. Análise IA indisponível.",
            'patterns': [
                "Distribuição de atendimentos dentro da normalidade",
                "Variações semanais compatíveis com operação normal"
            ],
            'recommendations': [
                "Monitorar agentes com mais de 6 solicitações semanais",
                "Implementar treinamentos para gaps identificados",
                "Manter acompanhamento semanal de autonomia"
            ]
        }
    
    def _generate_7_day_action_plan(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Gera plano de ação específico para 7 dias"""
        
        actions = []
        supervisors = data.get('supervisors', [])
        
        # Identifica ações urgentes
        critical_agents = []
        for supervisor in supervisors:
            for agent in supervisor.get('agents', []):
                if agent.get('risk_level') == 'critical':
                    critical_agents.append({
                        'supervisor': supervisor.get('supervisor_name'),
                        'agent': agent.get('agent_name'),
                        'requests': agent.get('current_requests')
                    })
        
        if critical_agents:
            actions.append({
                'priority': 'URGENTE',
                'action': f"Treinamento intensivo para {len(critical_agents)} agente(s) crítico(s)",
                'details': f"Focar em: {critical_agents[0]['agent']} ({critical_agents[0]['requests']} casos)"
            })
        
        # Ações importantes
        attention_agents = sum(1 for sup in supervisors for agent in sup.get('agents', []) 
                             if agent.get('risk_level') == 'attention')
        
        if attention_agents > 0:
            actions.append({
                'priority': 'IMPORTANTE',
                'action': f"Identificar gaps específicos em {attention_agents} agente(s)",
                'details': "Analisar padrões de dúvidas e implementar treinamento pontual"
            })
        
        # Monitoramento
        total_agents = sum(len(sup.get('agents', [])) for sup in supervisors)
        
        actions.append({
            'priority': 'MONITORAR',
            'action': f"Acompanhar evolução de {total_agents} agentes ativos",
            'details': "Verificar se medidas implementadas estão surtindo efeito"
        })
        
        # Meta semanal
        avg_autonomy = self._calculate_general_autonomy(supervisors)
        target_autonomy = min(85, avg_autonomy + 5)
        
        actions.append({
            'priority': 'META',
            'action': f"Aumentar autonomia geral para {target_autonomy}%",
            'details': f"Atual: {avg_autonomy}% → Meta: {target_autonomy}%"
        })
        
        return actions
    
    def _calculate_expected_results(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Calcula resultados esperados baseado em ações"""
        
        results = []
        supervisors = data.get('supervisors', [])
        
        # Para agentes críticos
        critical_agents = [agent for sup in supervisors for agent in sup.get('agents', []) 
                          if agent.get('risk_level') == 'critical']
        
        if critical_agents:
            current_max = max(agent.get('current_requests', 0) for agent in critical_agents)
            target_max = max(6, current_max - 3)  # Redução de 3 casos
            
            results.append({
                'type': 'agent_improvement',
                'description': f"Agente crítico: De {current_max} para {target_max} casos (máximo)"
            })
        
        # Para tempo estratégico
        supervisors_with_low_strategic_time = [sup for sup in supervisors 
                                             if sup.get('strategic_time_percent', 0) < 50]
        
        if supervisors_with_low_strategic_time:
            current_avg = sum(sup.get('strategic_time_percent', 0) for sup in supervisors_with_low_strategic_time) / len(supervisors_with_low_strategic_time)
            target_avg = min(70, current_avg + 10)
            
            results.append({
                'type': 'strategic_time',
                'description': f"Tempo estratégico: De {current_avg:.0f}% para {target_avg:.0f}%"
            })
        
        # Para autonomia geral
        current_autonomy = self._calculate_general_autonomy(supervisors)
        target_autonomy = min(85, current_autonomy + 5)
        
        results.append({
            'type': 'general_autonomy',
            'description': f"Autonomia geral: De {current_autonomy}% para {target_autonomy}%"
        })
        
        return results
    
    # Métodos auxiliares
    
    def _generate_visual_bar(self, value: int, max_width: int = 10) -> str:
        """Gera barra visual ASCII baseada no valor"""
        if value == 0:
            return "░" * max_width
        
        # Escala: 1-2 = baixo, 3-6 = médio, 7+ = alto
        if value <= 2:
            fill_char = "▓"
            fill_percent = 0.3
        elif value <= 6:
            fill_char = "█"
            fill_percent = 0.6
        else:
            fill_char = "█"
            fill_percent = 1.0
        
        filled = int(max_width * fill_percent)
        empty = max_width - filled
        
        return fill_char * filled + "░" * empty
    
    def _calculate_general_autonomy(self, supervisors: List[Dict]) -> float:
        """Calcula autonomia geral do sistema"""
        total_agents = 0
        autonomous_agents = 0
        
        for supervisor in supervisors:
            for agent in supervisor.get('agents', []):
                total_agents += 1
                if agent.get('risk_level') == 'autonomous':
                    autonomous_agents += 1
        
        return round((autonomous_agents / total_agents * 100), 1) if total_agents > 0 else 0
    
    def _generate_diagnosis(self, agent: Dict) -> str:
        """Gera diagnóstico específico para um agente"""
        requests = agent.get('current_requests', 0)
        variation = agent.get('variation_percent', 0)
        
        if requests > 8:
            return "Deficiência técnica grave"
        elif requests > 6:
            return "Gap em área específica"
        elif variation > 100:
            return "Nova dificuldade emergente"
        else:
            return "Necessita acompanhamento"
    
    def _generate_executive_diagnosis(self, global_stats: Dict, critical_agents: List) -> str:
        """Gera diagnóstico executivo geral"""
        total = global_stats.get('total_attendances_current', 0)
        variation = global_stats.get('variation_percent', 0)
        critical_count = len(critical_agents)
        
        if critical_count >= 3:
            return "Situação crítica: múltiplos agentes em dificuldade"
        elif variation > 25:
            return "Deterioração operacional: aumento significativo de demandas"
        elif total < 20:
            return "Operação eficiente: baixo volume de solicitações"
        else:
            return "Operação normal: dentro dos parâmetros esperados"
    
    def _assess_data_quality(self, data: Dict) -> Dict[str, Any]:
        """Avalia qualidade dos dados coletados"""
        supervisors = data.get('supervisors', [])
        total_supervisors = len(supervisors)
        total_agents = sum(len(sup.get('agents', [])) for sup in supervisors)
        
        return {
            'supervisors_analyzed': total_supervisors,
            'agents_analyzed': total_agents,
            'data_completeness': 'high' if total_agents > 5 else 'medium' if total_agents > 0 else 'low',
            'analysis_confidence': 'high' if total_supervisors >= 2 and total_agents >= 5 else 'medium'
        }
    
    def _generate_empty_analysis(self) -> Dict[str, Any]:
        """Gera análise vazia quando não há dados"""
        return {
            'success': True,
            'analysis': {
                'block_1_radar': {'message': 'Nenhum dado de atendimento encontrado no período'},
                'block_2_training_matrix': {'message': 'Sem dados para análise de capacitação'},
                'block_3_productivity': {'message': 'Sem dados de produtividade disponíveis'},
                'block_4_conclusions': {'message': 'Análise não possível sem dados'},
                'executive_summary': 'Período sem atendimentos registrados'
            }
        }
    
    def _generate_fallback_analysis(self, data: Dict) -> Dict[str, Any]:
        """Gera análise básica quando IA falha"""
        supervisors = data.get('supervisors', [])
        
        return {
            'block_1_radar': {
                'total_requests': sum(sup.get('total_attendances_current', 0) for sup in supervisors),
                'critical_alerts': [],
                'positive_highlights': [],
                'message': 'Análise IA indisponível - dados básicos apresentados'
            },
            'block_2_training_matrix': {
                'priority_agents': [],
                'message': 'Identificação de gaps indisponível'
            },
            'block_3_productivity': {
                'supervisors_evolution': [],
                'message': 'Análise de evolução básica'
            },
            'block_4_conclusions': {
                'ai_diagnosis': 'Sistema IA temporariamente indisponível',
                'action_plan_7_days': [
                    {'priority': 'MONITORAR', 'action': 'Verificar agentes com alta demanda'}
                ]
            }
        }

    def _aggregate_identified_gaps(self, priority_agents):
        """Agrega gaps identificados dos agentes prioritários"""
        gap_frequency = {}
        all_gaps = []
        
        for agent in priority_agents:
            agent_gaps = agent.get('gaps', [])
            all_gaps.extend(agent_gaps)
            
            for gap in agent_gaps:
                gap_frequency[gap] = gap_frequency.get(gap, 0) + 1
        
        # Retorna os gaps mais frequentes
        sorted_gaps = sorted(gap_frequency.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'most_common_gaps': sorted_gaps[:5],  # Top 5 gaps
            'total_gaps_identified': len(all_gaps),
            'unique_gaps': len(gap_frequency),
            'gap_distribution': gap_frequency
        }

    def _generate_training_recommendations(self, priority_agents):
        """Gera recomendações de treinamento baseado nos agentes prioritários"""
        if not priority_agents:
            return ["Nenhuma recomendação específica - equipe operando normalmente"]
        
        recommendations = []
        
        # Contar gaps por tipo
        gap_counts = {}
        for agent in priority_agents:
            for gap in agent.get('gaps', []):
                gap_counts[gap] = gap_counts.get(gap, 0) + 1
        
        # Gerar recomendações baseadas nos gaps mais comuns
        for gap, count in sorted(gap_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            if count > 1:
                recommendations.append(f"Treinamento em {gap} para {count} agentes")
            else:
                recommendations.append(f"Capacitação pontual em {gap}")
        
        # Recomendação geral se há muitos agentes críticos
        critical_count = len([a for a in priority_agents if a.get('risk_level') == 'critical'])
        if critical_count >= 3:
            recommendations.append("Programa intensivo de capacitação técnica")
        
        return recommendations[:4]  # Máximo 4 recomendações
        
        
    def _get_status_description(self, agent: Dict) -> str:
        """Gera descrição detalhada do status do agente"""
        risk_level = agent.get('risk_level', 'autonomous')
        current_requests = agent.get('current_requests', 0)
        variation = agent.get('variation_percent', 0)
        
        if risk_level == 'critical':
            return f"Crítico: {current_requests} casos ({variation:+.0f}%)"
        elif risk_level == 'attention':
            return f"Atenção: {current_requests} casos ({variation:+.0f}%)"
        elif agent.get('is_improving'):
            return f"Melhorando: {current_requests} casos ({variation:+.0f}%)"
        else:
            return f"Autônomo: {current_requests} casos ({variation:+.0f}%)"

    def _generate_period_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Gera resumo consolidado do período"""
        supervisors = data.get('supervisors', [])
        global_stats = data.get('global_stats', {})
        
        total_agents = sum(len(sup.get('agents', [])) for sup in supervisors)
        critical_agents = sum(1 for sup in supervisors for agent in sup.get('agents', []) 
                            if agent.get('risk_level') == 'critical')
        autonomous_agents = sum(1 for sup in supervisors for agent in sup.get('agents', []) 
                            if agent.get('risk_level') == 'autonomous')
        
        return {
            'total_supervisors': len(supervisors),
            'total_agents': total_agents,
            'critical_agents': critical_agents,
            'autonomous_agents': autonomous_agents,
            'autonomy_rate': round((autonomous_agents / total_agents * 100), 1) if total_agents > 0 else 0,
            'total_requests': global_stats.get('total_attendances_current', 0),
            'variation_percent': global_stats.get('variation_percent', 0)
        }

    def _generate_visual_insights(self, evolution_analysis: List[Dict]) -> List[str]:
        """Gera insights visuais baseados na análise de evolução"""
        insights = []
        
        # Analisa tendências
        improving_supervisors = len([sup for sup in evolution_analysis if '📉' in sup.get('trend', '')])
        deteriorating_supervisors = len([sup for sup in evolution_analysis if '📈' in sup.get('trend', '')])
        
        if improving_supervisors > 0:
            insights.append(f"{improving_supervisors} supervisor(es) com tendência de melhoria")
        
        if deteriorating_supervisors > 0:
            insights.append(f"{deteriorating_supervisors} supervisor(es) com tendência de deterioração")
        
        # Analisa distribuição de agentes
        total_critical = sum(len([agent for agent in sup.get('agents', []) if '🔴' in agent.get('status', '')]) 
                            for sup in evolution_analysis)
        
        if total_critical > 0:
            insights.append(f"{total_critical} agente(s) em situação crítica")
        
        # Insight geral
        if not insights:
            insights.append("Situação operacional estável")
        
        return insights

    def _assess_overall_risk(self, data: Dict[str, Any]) -> str:
        """Avalia risco geral do sistema"""
        supervisors = data.get('supervisors', [])
        
        critical_count = sum(1 for sup in supervisors for agent in sup.get('agents', []) 
                            if agent.get('risk_level') == 'critical')
        
        total_agents = sum(len(sup.get('agents', [])) for sup in supervisors)
        
        if total_agents == 0:
            return "Sem dados para avaliação"
        
        critical_percentage = (critical_count / total_agents) * 100
        
        if critical_percentage >= 30:
            return "Risco alto: mais de 30% dos agentes em situação crítica"
        elif critical_percentage >= 15:
            return "Risco médio: percentual significativo de agentes críticos"
        elif critical_percentage > 0:
            return "Risco baixo: poucos agentes em situação crítica"
        else:
            return "Risco mínimo: nenhum agente em situação crítica"

    def _generate_executive_summary(self, data: Dict[str, Any]) -> str:
        """Gera resumo executivo da análise"""
        supervisors = data.get('supervisors', [])
        global_stats = data.get('global_stats', {})
        
        total_requests = global_stats.get('total_attendances_current', 0)
        variation = global_stats.get('variation_percent', 0)
        autonomy_rate = self._calculate_general_autonomy(supervisors)
        
        if total_requests == 0:
            return "Período sem atendimentos registrados - equipe operando de forma autônoma"
        
        summary = f"Período com {total_requests} solicitações "
        
        if variation > 15:
            summary += f"(aumento de {variation:+.1f}%). "
        elif variation < -15:
            summary += f"(redução de {variation:+.1f}%). "
        else:
            summary += f"(variação de {variation:+.1f}%). "
        
        summary += f"Taxa de autonomia atual: {autonomy_rate}%. "
        
        critical_count = sum(1 for sup in supervisors for agent in sup.get('agents', []) 
                            if agent.get('risk_level') == 'critical')
        
        if critical_count > 0:
            summary += f"Atenção: {critical_count} agente(s) em situação crítica."
        else:
            summary += "Equipe operando dentro da normalidade."
        
        return summary   
        
        
               
        
        
        
 ######################## FIM DA CLASSE AutonomyAIAnalyzer ########################       
        
    # Função helper para facilitar uso
def analyze_autonomy_data(autonomy_data: Dict[str, Any], ollama_url: str = "http://localhost:11434") -> Dict[str, Any]:
      """
      Função helper para análise de dados de autonomia
        
      Usage:
          from ai_reports.ai_analyzer import analyze_autonomy_data
          analysis = analyze_autonomy_data(data)
      """
      analyzer = AutonomyAIAnalyzer(ollama_url)
      return analyzer.analyze_weekly_data(autonomy_data)        


if __name__ == "__main__":
    # Teste rápido
    print("🧪 Testando AI Analyzer...")
    analyzer = AutonomyAIAnalyzer()
    
    # Testa conexão
    connection = analyzer.test_connection()
    print(f"🔌 Conexão Ollama: {connection['status']}")
    
    if connection['success']:
        print(f"🤖 Modelos disponíveis: {connection['available_models']}")
    else:
        print(f"❌ Erro: {connection['error']}")