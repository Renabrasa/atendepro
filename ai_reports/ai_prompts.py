# ai_reports/ai_prompts.py
"""
🎯 AI Prompts - Sistema AI Reports
Prompts especializados para cada bloco de análise
"""

from typing import Dict, List, Any

def autonomy_radar_prompt(data: Dict[str, Any]) -> str:
    """Prompt para Bloco 1: Radar de Autonomia"""
    
    supervisors = data.get('supervisors', [])
    global_stats = data.get('global_stats', {})  # ← CORRIGIDO: era ] em vez de }
    
    # Identifica situações críticas
    critical_situations = []
    for supervisor in supervisors:
        for agent in supervisor.get('agents', []):
            if agent.get('risk_level') == 'critical':
                critical_situations.append(f"{agent.get('agent_name')}: {agent.get('current_requests')} casos")
    
    total_requests = global_stats.get('total_attendances_current', 0)
    variation = global_stats.get('variation_percent', 0)
    
    prompt = f"""
Você é um analista sênior de operações contábeis. Analise o RADAR DE AUTONOMIA semanal.

DADOS EXECUTIVOS:
- Total de solicitações: {total_requests}
- Variação semanal: {variation:+.1f}%
- Supervisores analisados: {len(supervisors)}
- Situações críticas: {', '.join(critical_situations) if critical_situations else 'Nenhuma'}

CONTEXTO OPERACIONAL:
- Cada solicitação = pedido de socorro técnico do agente para supervisor
- Meta: máximo 2 solicitações/agente/semana (autonomia operacional)
- >6 solicitações/agente = deficiência grave que impede trabalho autônomo

GERE DIAGNÓSTICO EXECUTIVO (máximo 2 frases):
[Foque no impacto operacional e urgência das ações necessárias]

IDENTIFIQUE ALERTAS CRÍTICOS (se houver):
[Liste agentes que precisam intervenção imediata]

DESTAQUE PONTOS POSITIVOS (se houver):
[Reconheça melhorias e autonomia alcançada]

Seja direto, específico e focado em ações.
"""
    
    return prompt

def training_matrix_prompt(data: Dict[str, Any]) -> str:
    """Prompt para Bloco 2: Matriz de Capacitação"""
    
    supervisors = data.get('supervisors', [])
    
    # Coleta gaps identificados
    all_gaps = []
    priority_agents = []
    
    for supervisor in supervisors:
        for agent in supervisor.get('agents', []):
            if agent.get('risk_level') in ['critical', 'attention']:
                priority_agents.append({
                    'name': agent.get('agent_name'),
                    'requests': agent.get('current_requests'),
                    'gaps': agent.get('probable_gaps', [])
                })
                all_gaps.extend(agent.get('probable_gaps', []))
    
    # Conta gaps mais frequentes
    gap_frequency = {}
    for gap in all_gaps:
        gap_frequency[gap] = gap_frequency.get(gap, 0) + 1
    
    most_common_gaps = sorted(gap_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
    
    prompt = f"""
Você é um especialista em desenvolvimento de equipes contábeis. Analise a MATRIZ DE CAPACITAÇÃO.

AGENTES PRIORITÁRIOS PARA TREINAMENTO:
{chr(10).join([f"- {agent['name']}: {agent['requests']} casos → {', '.join(agent['gaps'][:2])}" for agent in priority_agents[:5]])}

GAPS MAIS FREQUENTES IDENTIFICADOS:
{chr(10).join([f"- {gap}: {freq} ocorrências" for gap, freq in most_common_gaps])}

ÁREAS TÉCNICAS CONHECIDAS:
- eSocial vs Alterdata (diferenças entre sistemas)
- SPED (validação de arquivos magnéticos)
- Report Builder (dificuldades com relatórios)
- Rotinas específicas (processos internos)

ANALISE E FORNEÇA:

1. GAPS DE CONHECIMENTO PRINCIPAIS (3-4 áreas):
[Identifique as deficiências técnicas mais críticas]

2. PLANO DE CAPACITAÇÃO PRIORITÁRIO (ações específicas):
[Sugira treinamentos focados nas deficiências identificadas]

3. DISTRIBUIÇÃO RECOMENDADA DE ESFORÇOS:
[Como o supervisor deve alocar tempo entre agentes]

Foque em soluções práticas e implementáveis.
"""
    
    return prompt

def productivity_dashboard_prompt(data: Dict[str, Any]) -> str:
    """Prompt para Bloco 3: Dashboard de Produtividade"""
    
    supervisors = data.get('supervisors', [])
    global_stats = data.get('global_stats', {})
    
    # Analisa tendências
    improving_agents = []
    worsening_agents = []
    
    for supervisor in supervisors:
        for agent in supervisor.get('agents', []):
            variation = agent.get('variation_percent', 0)
            if variation < -25:  # Melhoria significativa
                improving_agents.append(f"{agent.get('agent_name')} ({variation:+.0f}%)")
            elif variation > 50:  # Piora significativa
                worsening_agents.append(f"{agent.get('agent_name')} (+{variation:.0f}%)")
    
    total_variation = global_stats.get('variation_percent', 0)
    
    prompt = f"""
Você é um analista de produtividade especializado em equipes técnicas. Analise o DASHBOARD DE PRODUTIVIDADE.

EVOLUÇÃO GERAL DO PERÍODO:
- Variação total de solicitações: {total_variation:+.1f}%
- Agentes melhorando: {', '.join(improving_agents) if improving_agents else 'Nenhum'}
- Agentes com piora: {', '.join(worsening_agents) if worsening_agents else 'Nenhum'}

SUPERVISORES ANALISADOS: {len(supervisors)}

CONTEXTO DE PRODUTIVIDADE:
- Redução de solicitações = ganho de autonomia = maior produtividade
- Aumento súbito = novo gap técnico ou mudança de sistema
- Estabilidade = operação madura

FORNEÇA ANÁLISE DE PRODUTIVIDADE:

1. TENDÊNCIA GERAL DA OPERAÇÃO:
[Avalie se a operação está melhorando, estável ou deteriorando]

2. INSIGHTS DE EVOLUÇÃO (3-4 pontos):
[Identifique padrões significativos na evolução dos agentes]

3. INDICADORES DE EFICIÊNCIA:
[Destaque métricas que mostram ganhos ou perdas de eficiência]

Seja analítico e baseado em dados.
"""
    
    return prompt

def strategic_conclusions_prompt(data: Dict[str, Any]) -> str:
    """Prompt para Bloco 4: Conclusões IA & Plano de Ação"""
    
    supervisors = data.get('supervisors', [])
    global_stats = data.get('global_stats', {})
    
    # Métricas estratégicas
    total_agents = sum(len(sup.get('agents', [])) for sup in supervisors)
    critical_agents = sum(1 for sup in supervisors for agent in sup.get('agents', []) 
                         if agent.get('risk_level') == 'critical')
    autonomous_agents = sum(1 for sup in supervisors for agent in sup.get('agents', []) 
                           if agent.get('risk_level') == 'autonomous')
    
    autonomy_rate = round((autonomous_agents / total_agents * 100), 1) if total_agents > 0 else 0
    critical_rate = round((critical_agents / total_agents * 100), 1) if total_agents > 0 else 0
    
    # Supervisor mais eficiente
    most_efficient = max(supervisors, key=lambda x: x.get('autonomy_rate', 0)) if supervisors else None
    
    prompt = f"""
Você é um consultor estratégico sênior em gestão operacional de contabilidade. Faça a ANÁLISE IA ESTRATÉGICA.

SITUAÇÃO OPERACIONAL ATUAL:
- Total de agentes: {total_agents}
- Taxa de autonomia: {autonomy_rate}%
- Agentes críticos: {critical_agents} ({critical_rate}%)
- Agentes autônomos: {autonomous_agents}
- Supervisor mais eficiente: {most_efficient.get('supervisor_name', 'N/A') if most_efficient else 'N/A'}

METAS OPERACIONAIS:
- Autonomia ideal: 85%+ dos agentes
- Máximo aceitável: 2 solicitações/agente/semana
- Tempo estratégico supervisor: 60%+

CONTEXTO ESTRATÉGICO:
- Supervisores devem atuar como mentores técnicos, não "bombeiros"
- Autonomia = produtividade = rentabilidade
- Investimento em treinamento = ROI através de redução de dependência

FORNEÇA ANÁLISE ESTRATÉGICA COMPLETA:

1. DIAGNÓSTICO ESTRATÉGICO (2-3 frases):
[Avalie a saúde operacional geral e principais desafios]

2. PADRÕES ESTRATÉGICOS IDENTIFICADOS (3-4 itens):
[Identifique tendências que impactam objetivos de negócio]

3. PLANO DE AÇÃO 7 DIAS (4 ações priorizadas):
URGENTE: [Ação que não pode esperar - intervenção imediata]
IMPORTANTE: [Ação estrutural para médio prazo]
MONITORAR: [Acompanhamento necessário]
META: [Objetivo mensurável para a semana]

4. RESULTADOS ESPERADOS (3 metas específicas):
[Defina metas numéricas alcançáveis em 7 dias]

5. RECOMENDAÇÕES ESTRATÉGICAS (2-3 ações):
[Ações que geram impacto sistêmico a médio prazo]

Seja estratégico, mensurável e focado em ROI.
"""
    
    return prompt

def gap_analysis_prompt(gaps_data: List[str], frequency_data: Dict[str, int]) -> str:
    """Prompt especializado para identificação de gaps técnicos"""
    
    # Organiza gaps por frequência
    sorted_gaps = sorted(frequency_data.items(), key=lambda x: x[1], reverse=True)
    
    prompt = f"""
Você é um especialista técnico em sistemas contábeis. Analise os GAPS DE CONHECIMENTO identificados.

GAPS REPORTADOS (por frequência):
{chr(10).join([f"- {gap}: {freq} ocorrências" for gap, freq in sorted_gaps[:5]])}

SISTEMAS/ÁREAS TÉCNICAS RELEVANTES:
- eSocial: Obrigações trabalhistas digitais
- Alterdata: Sistema ERP contábil
- SPED: Sistema Público de Escrituração Digital
- Report Builder: Ferramenta de relatórios
- Rotinas fiscais: Processos específicos da contabilidade

ANALISE E IDENTIFIQUE:

1. GAPS TÉCNICOS PRIORITÁRIOS (3 principais):
[Identifique as deficiências técnicas mais críticas baseadas na frequência]

2. CAUSA RAIZ PROVÁVEL:
[Identifique possíveis causas: novo sistema, mudança de processo, falta de treinamento]

3. PLANO DE CAPACITAÇÃO ESPECÍFICO:
[Sugira treinamentos focados e práticos para cada gap identificado]

4. IMPACTO OPERACIONAL:
[Avalie como esses gaps afetam a produtividade geral]

Seja técnico, específico e prático.
"""
    
    return prompt

def executive_summary_prompt(complete_analysis: Dict[str, Any]) -> str:
    """Prompt para resumo executivo integrado dos 4 blocos"""
    
    # Extrai dados dos 4 blocos
    radar_data = complete_analysis.get('block_1_radar', {})
    matrix_data = complete_analysis.get('block_2_training_matrix', {})
    productivity_data = complete_analysis.get('block_3_productivity', {})
    conclusions_data = complete_analysis.get('block_4_conclusions', {})
    
    total_requests = radar_data.get('total_requests', 0)
    critical_alerts = len(radar_data.get('critical_alerts', []))
    positive_highlights = len(radar_data.get('positive_highlights', []))
    
    prompt = f"""
Você é um CEO de empresa contábil. Crie um RESUMO EXECUTIVO integrando todos os blocos de análise.

DADOS CONSOLIDADOS DOS 4 BLOCOS:
- Total de solicitações: {total_requests}
- Alertas críticos: {critical_alerts}
- Destaques positivos: {positive_highlights}
- Gaps de capacitação identificados: SIM/NÃO
- Tendência de produtividade: ANALISAR
- Plano de ação definido: SIM/NÃO

PERSPECTIVA CEO:
- Foco em impacto no negócio
- ROI de investimentos em treinamento
- Eficiência operacional
- Competitividade no mercado

FORNEÇA RESUMO EXECUTIVO (4-5 frases):

1. SITUAÇÃO ATUAL:
[Status operacional em linguagem executiva]

2. PRINCIPAIS DESAFIOS:
[2-3 desafios que impactam resultados]

3. OPORTUNIDADES IDENTIFICADAS:
[Como converter desafios em vantagem competitiva]

4. PRÓXIMOS PASSOS ESTRATÉGICOS:
[Ações de maior impacto para os próximos 7 dias]

5. EXPECTATIVA DE RESULTADOS:
[ROI esperado das ações propostas]

Use linguagem executiva, objetiva e focada em resultados de negócio.
"""
    
    return prompt

def supervisor_performance_analysis_prompt(supervisor_data: Dict[str, Any]) -> str:
    """Prompt para análise individual de performance de supervisor"""
    
    supervisor_name = supervisor_data.get('supervisor_name', 'Supervisor')
    total_requests = supervisor_data.get('total_attendances_current', 0)
    autonomy_rate = supervisor_data.get('autonomy_rate', 0)
    strategic_time = supervisor_data.get('strategic_time_percent', 0)
    agents = supervisor_data.get('agents', [])
    
    critical_agents = [a for a in agents if a.get('risk_level') == 'critical']
    autonomous_agents = [a for a in agents if a.get('risk_level') == 'autonomous']
    
    prompt = f"""
Você é um consultor de gestão especializado em liderança operacional. Analise a performance do SUPERVISOR.

DADOS DO SUPERVISOR: {supervisor_name}
- Total de solicitações recebidas: {total_requests}
- Taxa de autonomia da equipe: {autonomy_rate}%
- Tempo disponível para estratégia: {strategic_time}%
- Total de agentes: {len(agents)}
- Agentes críticos: {len(critical_agents)}
- Agentes autônomos: {len(autonomous_agents)}

AGENTES CRÍTICOS (se houver):
{chr(10).join([f"- {a.get('agent_name')}: {a.get('current_requests')} solicitações" for a in critical_agents])}

BENCHMARKS DE EFICIÊNCIA:
- Supervisor eficiente: 75%+ autonomia, 60%+ tempo estratégico
- Supervisor sobrecarregado: <50% autonomia, <30% tempo estratégico
- Meta ideal: máximo 2 solicitações/agente/semana

ANALISE E FORNEÇA:

1. AVALIAÇÃO DE PERFORMANCE:
[Classifique: EXCELENTE/BOM/REGULAR/CRÍTICO e justifique]

2. PONTOS FORTES:
[Identifique o que o supervisor está fazendo bem]

3. ÁREAS DE MELHORIA:
[Identifique gargalos e oportunidades]

4. PLANO DE DESENVOLVIMENTO:
[Ações específicas para melhorar eficiência da liderança]

5. IMPACTO NO NEGÓCIO:
[Como a melhoria deste supervisor afeta resultados gerais]

Seja construtivo, específico e focado em desenvolvimento.
"""
    
    return prompt

def trend_analysis_prompt(historical_data: List[Dict[str, Any]]) -> str:
    """Prompt para análise de tendências históricas (4 semanas)"""
    
    if len(historical_data) < 2:
        return "Dados insuficientes para análise de tendência."
    
    # Calcula tendência
    weeks_data = []
    for i, week_data in enumerate(historical_data[-4:], 1):  # Últimas 4 semanas
        total = week_data.get('total_attendances', 0)
        weeks_data.append(f"Semana {i}: {total} solicitações")
    
    prompt = f"""
Você é um analista de dados especializado em tendências operacionais. Analise a EVOLUÇÃO HISTÓRICA.

DADOS DAS ÚLTIMAS 4 SEMANAS:
{chr(10).join(weeks_data)}

CONTEXTO ANALÍTICO:
- Redução consistente = melhoria da autonomia
- Aumento consistente = deterioração ou crescimento da operação
- Oscilação = instabilidade operacional
- Estabilidade = operação madura

FORNEÇA ANÁLISE DE TENDÊNCIA:

1. CLASSIFICAÇÃO DA TENDÊNCIA:
[MELHORANDO/ESTÁVEL/DETERIORANDO/INSTÁVEL]

2. PADRÕES IDENTIFICADOS:
[Identifique ciclos, sazonalidades ou eventos específicos]

3. PROJEÇÃO PARA PRÓXIMA SEMANA:
[Estime tendência baseada no histórico]

4. FATORES INFLUENCIADORES:
[Possíveis causas das variações observadas]

5. RECOMENDAÇÕES BASEADAS NA TENDÊNCIA:
[Ações específicas baseadas no padrão identificado]

Seja analítico, baseado em dados e preditivo.
"""
    
    return prompt

def risk_assessment_prompt(risk_data: Dict[str, Any]) -> str:
    """Prompt para avaliação de riscos operacionais"""
    
    critical_agents_count = risk_data.get('critical_agents_count', 0)
    deteriorating_agents = risk_data.get('deteriorating_agents', 0)
    supervisors_overloaded = risk_data.get('supervisors_overloaded', 0)
    total_variation = risk_data.get('total_variation', 0)
    
    prompt = f"""
Você é um especialista em gestão de riscos operacionais. Avalie os RISCOS IDENTIFICADOS.

INDICADORES DE RISCO:
- Agentes críticos (>6 solicitações): {critical_agents_count}
- Agentes em deterioração (>50% aumento): {deteriorating_agents}
- Supervisores sobrecarregados (<30% tempo estratégico): {supervisors_overloaded}
- Variação total do sistema: {total_variation:+.1f}%

MATRIZ DE RISCOS:
- ALTO: >3 agentes críticos OU >25% variação negativa
- MÉDIO: 1-3 agentes críticos OU 10-25% variação
- BAIXO: Operação estável com <10% variação

ANALISE E CLASSIFIQUE:

1. NÍVEL DE RISCO ATUAL:
[ALTO/MÉDIO/BAIXO e justificativa]

2. RISCOS IMEDIATOS (próximos 7 dias):
[Identifique riscos que podem se materializar rapidamente]

3. RISCOS SISTÊMICOS (30 dias):
[Identifique riscos que podem afetar toda a operação]

4. PLANO DE MITIGAÇÃO:
[Ações específicas para reduzir riscos identificados]

5. INDICADORES DE MONITORAMENTO:
[Métricas para acompanhar evolução dos riscos]

Seja conservador, específico e focado em prevenção.
"""
    
    return prompt

def performance_benchmark_prompt(comparative_data: Dict[str, Any]) -> str:
    """Prompt para análise comparativa de performance entre supervisores"""
    
    supervisors_data = comparative_data.get('supervisors', [])
    
    # Calcula benchmarks
    autonomy_rates = [s.get('autonomy_rate', 0) for s in supervisors_data]
    strategic_times = [s.get('strategic_time_percent', 0) for s in supervisors_data]
    
    best_autonomy = max(autonomy_rates) if autonomy_rates else 0
    worst_autonomy = min(autonomy_rates) if autonomy_rates else 0
    avg_autonomy = sum(autonomy_rates) / len(autonomy_rates) if autonomy_rates else 0
    
    prompt = f"""
Você é um consultor de benchmarking especializado em operações contábeis. Analise a PERFORMANCE COMPARATIVA.

DADOS COMPARATIVOS:
- Supervisores analisados: {len(supervisors_data)}
- Melhor taxa de autonomia: {best_autonomy:.1f}%
- Pior taxa de autonomia: {worst_autonomy:.1f}%
- Média de autonomia: {avg_autonomy:.1f}%

BENCHMARKS DA INDÚSTRIA:
- Excelente: >80% autonomia
- Bom: 60-80% autonomia
- Regular: 40-60% autonomia
- Crítico: <40% autonomia

SUPERVISORES POR PERFORMANCE:
{chr(10).join([f"- {s.get('supervisor_name')}: {s.get('autonomy_rate', 0):.1f}% autonomia" for s in sorted(supervisors_data, key=lambda x: x.get('autonomy_rate', 0), reverse=True)])}

FORNEÇA ANÁLISE COMPARATIVA:

1. CLASSIFICAÇÃO GERAL DA OPERAÇÃO:
[Como a operação se compara aos benchmarks da indústria]

2. GAPS DE PERFORMANCE:
[Diferenças significativas entre supervisores]

3. MELHORES PRÁTICAS IDENTIFICADAS:
[O que os supervisores eficientes fazem diferente]

4. PLANO DE NIVELAMENTO:
[Como elevar performance dos supervisores menos eficientes]

5. METAS DE CONVERGÊNCIA:
[Objetivos realistas para reduzir gaps de performance]

Seja comparativo, justo e focado em melhoria contínua.
"""
    
    return prompt

# Funções auxiliares para configuração de prompts

def get_base_context() -> str:
    """Contexto base comum a todos os prompts"""
    return """
CONTEXTO OPERACIONAL CONTÁBIL:
- Agentes = profissionais técnicos de contabilidade
- Supervisores = mentores técnicos e gestores
- Solicitações = pedidos de ajuda técnica (não são atendimentos a clientes)
- Autonomia = capacidade de trabalhar sem supervisão constante
- Meta operacional = máximo 2 solicitações/agente/semana

CLASSIFICAÇÃO DE AUTONOMIA:
🟢 AUTÔNOMO (0-2 solicitações/semana): Trabalha independente
🟡 ATENÇÃO (3-6 solicitações/semana): Gap específico de conhecimento  
🔴 CRÍTICO (>6 solicitações/semana): Não consegue trabalhar sozinho

ÁREAS TÉCNICAS COMUNS:
- eSocial: Sistema de obrigações trabalhistas
- SPED: Escrituração fiscal digital
- Report Builder: Geração de relatórios
- Alterdata: Sistema ERP contábil
- Rotinas fiscais: Processos específicos
"""

def format_prompt_with_context(prompt: str) -> str:
    """Adiciona contexto base a qualquer prompt"""
    base_context = get_base_context()
    return f"{base_context}\n\n{prompt}"

# Validação de prompts

def validate_prompt_data(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """Valida se os dados necessários estão presentes"""
    for field in required_fields:
        if field not in data:
            return False
    return True

def get_available_prompts() -> Dict[str, str]:
    """Retorna lista de prompts disponíveis"""
    return {
        'autonomy_radar': 'Análise do radar de autonomia (Bloco 1)',
        'training_matrix': 'Matriz de capacitação (Bloco 2)', 
        'productivity_dashboard': 'Dashboard de produtividade (Bloco 3)',
        'strategic_conclusions': 'Conclusões estratégicas (Bloco 4)',
        'gap_analysis': 'Análise de gaps técnicos',
        'executive_summary': 'Resumo executivo integrado',
        'supervisor_performance': 'Performance individual de supervisor',
        'trend_analysis': 'Análise de tendências históricas',
        'risk_assessment': 'Avaliação de riscos operacionais',
        'performance_benchmark': 'Benchmarking comparativo'
    }

if __name__ == "__main__":
    # Teste dos prompts
    print("🧪 Testando AI Prompts...")
    
    # Dados de teste
    test_data = {
        'supervisors': [
            {
                'supervisor_name': 'João Silva',
                'autonomy_rate': 75.5,
                'total_attendances_current': 15,
                'agents': [
                    {'agent_name': 'Ana', 'current_requests': 8, 'risk_level': 'critical'},
                    {'agent_name': 'Carlos', 'current_requests': 1, 'risk_level': 'autonomous'}
                ]
            }
        ],
        'global_stats': {
            'total_attendances_current': 25,
            'variation_percent': 15.5
        }
    }
    
    # Testa alguns prompts
    print("\n📊 Prompt Radar de Autonomia:")
    radar_prompt = autonomy_radar_prompt(test_data)
    print(f"Tamanho: {len(radar_prompt)} caracteres")
    
    print("\n📋 Prompt Matriz de Capacitação:")
    matrix_prompt = training_matrix_prompt(test_data)
    print(f"Tamanho: {len(matrix_prompt)} caracteres")
    
    print("\n✅ Prompts carregados com sucesso!")
    print(f"📝 Total de prompts disponíveis: {len(get_available_prompts())}")