# ai_reports/email_sender.py
"""
📧 Email Sender - Sistema AI Reports
Formata e envia relatórios de autonomia semanal
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import os
from jinja2 import Template

logger = logging.getLogger(__name__)

class AutonomyEmailSender:
   """Envia relatórios de autonomia formatados por email"""
   
   def __init__(self, smtp_config: Dict[str, str]):
       """
       Inicializa sender com configurações SMTP
       
       Args:
           smtp_config: {
               'server': 'smtp.gmail.com',
               'port': 587,
               'email': 'sender@company.com',
               'password': 'app_password',
               'sender_name': 'Sistema AI Reports'
           }
       """
       self.smtp_config = smtp_config
       self.sender_email = smtp_config.get('email')
       self.sender_name = smtp_config.get('sender_name', 'AI Reports')
       
   def test_connection(self) -> Dict[str, Any]:
       """Testa conexão SMTP"""
       try:
           server = smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'])
           server.starttls()
           server.login(self.smtp_config['email'], self.smtp_config['password'])
           server.quit()
           
           return {
               'success': True,
               'status': 'Conexão SMTP estabelecida com sucesso',
               'server': self.smtp_config['server']
           }
       except Exception as e:
           return {
               'success': False,
               'error': str(e),
               'status': 'Falha na conexão SMTP'
           }
   
   def send_weekly_report(
       self, 
       analysis_data: Dict[str, Any], 
       recipients: List[str],
       supervisor_name: Optional[str] = None,
       custom_subject: Optional[str] = None
   ) -> Dict[str, Any]:
       """
       Envia relatório semanal de autonomia
       
       Args:
           analysis_data: Dados da análise IA
           recipients: Lista de emails destinatários
           supervisor_name: Nome do supervisor (se relatório individual)
           custom_subject: Assunto personalizado
           
       Returns:
           Dict com resultado do envio
       """
       try:
           # Prepara dados para template
           template_data = self._prepare_template_data(analysis_data, supervisor_name)
           
           # Gera HTML e texto
           html_content = self._create_html_version(template_data)
           text_content = self._create_text_version(template_data)
           
           # Define assunto
           subject = custom_subject or self._generate_subject(template_data)
           
           # Envia email
           result = self._send_email(
               recipients=recipients,
               subject=subject,
               html_content=html_content,
               text_content=text_content
           )
           
           return result
           
       except Exception as e:
           logger.error(f"Erro ao enviar relatório: {e}")
           return {
               'success': False,
               'error': str(e),
               'status': 'Falha no envio do relatório'
           }
   
   def send_test_email(self, recipient: str) -> Dict[str, Any]:
       """Envia email de teste com DADOS REAIS do banco"""
       
       # REMOVIDO: Dados fake
       # ADICIONADO: Usar dados reais
       from .data_collector import collect_autonomy_data
       from .ai_analyzer import analyze_autonomy_data
       
       try:
           # Coletar dados reais do banco
           real_data = collect_autonomy_data()
           
           # Análise IA com dados reais
           real_analysis = analyze_autonomy_data(real_data)
           
           return self.send_weekly_report(
               analysis_data=real_analysis,
               recipients=[recipient],
               custom_subject="🧪 [TESTE] Relatório de Autonomia Semanal"
           )
           
       except Exception as e:
           logger.error(f"Erro ao gerar dados reais para teste: {e}")
           # Fallback para dados básicos se der erro
           return {
               'success': False,
               'error': f'Erro ao coletar dados reais: {str(e)}',
               'status': 'Falha na coleta de dados'
           }
   
   def _prepare_template_data(self, analysis_data: Dict[str, Any], supervisor_name: Optional[str]) -> Dict[str, Any]:
       """Prepara dados estruturados para o template"""
       
       # CORRIGIDO: Usar dados reais do data_collector
       raw_data = analysis_data.get('raw_data', {})
       periodo_atual = raw_data.get('periodo_atual', {})
       
       # Se não tiver dados do período, usar datas calculadas corretamente
       if periodo_atual:
           period_start_str = periodo_atual.get('inicio', '')
           period_end_str = periodo_atual.get('fim', '')
           
           # Converter para formato brasileiro
           if period_start_str:
               period_start = datetime.strptime(period_start_str, '%Y-%m-%d').strftime('%d/%m/%Y')
           else:
               period_start = 'N/A'
               
           if period_end_str:
               period_end = datetime.strptime(period_end_str, '%Y-%m-%d').strftime('%d/%m/%Y')
           else:
               period_end = 'N/A'
       else:
           # Fallback para cálculo manual
           now = datetime.now()
           yesterday = now - timedelta(days=1)
           week_start = yesterday - timedelta(days=6)
           
           period_start = week_start.strftime('%d/%m/%Y')
           period_end = yesterday.strftime('%d/%m/%Y')
       
       # Extrai dados dos 4 blocos
       radar = analysis_data.get('analysis', {}).get('block_1_radar', {})
       matrix = analysis_data.get('analysis', {}).get('block_2_training_matrix', {})
       productivity = analysis_data.get('analysis', {}).get('block_3_productivity', {})
       conclusions = analysis_data.get('analysis', {}).get('block_4_conclusions', {})
       
       return {
           # Cabeçalho - CORRIGIDO: Usar datas reais
           'report_title': f'Relatório de Autonomia Semanal{" - " + supervisor_name if supervisor_name else ""}',
           'period_start': period_start,
           'period_end': period_end,
           'generation_date': datetime.now().strftime('%d/%m/%Y às %H:%M'),
           'supervisor_name': supervisor_name,
           
           # Bloco 1: Radar de Autonomia
           'radar': {
               'total_requests': radar.get('total_requests', 0),
               'variation_requests': radar.get('variation_requests', 0),
               'general_autonomy': radar.get('general_autonomy', 0),
               'supervisor_ranking': radar.get('supervisor_ranking', 0),
               'critical_alerts': radar.get('critical_alerts', []),
               'positive_highlights': radar.get('positive_highlights', []),
               'executive_diagnosis': radar.get('executive_diagnosis', 'Operação normal')
           },
           
           # Bloco 2: Matriz de Capacitação
           'matrix': {
               'priority_agents': matrix.get('priority_agents', []),
               'time_distribution': matrix.get('time_distribution', []),
               'identified_gaps': matrix.get('identified_gaps', []),
               'training_recommendations': matrix.get('training_recommendations', [])
           },
           
           # Bloco 3: Dashboard de Produtividade
           'productivity': {
               'supervisors_evolution': productivity.get('supervisors_evolution', []),
               'period_summary': productivity.get('period_summary', {}),
               'visual_insights': productivity.get('visual_insights', [])
           },
           
           # Bloco 4: Conclusões IA
           'conclusions': {
               'ai_diagnosis': conclusions.get('ai_diagnosis', 'Análise em processamento'),
               'pattern_insights': conclusions.get('pattern_insights', []),
               'action_plan_7_days': conclusions.get('action_plan_7_days', []),
               'expected_results': conclusions.get('expected_results', []),
               'strategic_recommendations': conclusions.get('strategic_recommendations', []),
               'risk_assessment': conclusions.get('risk_assessment', 'Risco baixo')
           },
           
           # Metadados
           'ai_model_used': analysis_data.get('analysis', {}).get('ai_model_used', 'Ollama'),
           'data_quality': analysis_data.get('data_quality', {}),
           'analysis_timestamp': analysis_data.get('analysis', {}).get('analysis_timestamp', datetime.now().isoformat())
       }
   
   def _create_html_version(self, template_data: Dict[str, Any]) -> str:
       """Cria versão HTML do relatório usando template"""
       
       html_template = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
   <meta charset="UTF-8">
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   <title>{{ report_title }}</title>
   <style>
       body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background: #f8fafc; }
       .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; text-align: center; }
       .header h1 { margin: 0; font-size: 28px; font-weight: 700; }
       .header p { margin: 10px 0 0 0; opacity: 0.9; font-size: 16px; }
       
       .block { background: white; border-radius: 12px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 4px solid #667eea; }
       .block h2 { margin: 0 0 20px 0; color: #1e293b; font-size: 22px; display: flex; align-items: center; gap: 10px; }
       .block h3 { color: #475569; font-size: 18px; margin: 20px 0 10px 0; }
       
       .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
       .metric-card { background: #f1f5f9; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #e2e8f0; }
       .metric-value { font-size: 32px; font-weight: 700; color: #1e293b; margin-bottom: 5px; }
       .metric-label { color: #64748b; font-size: 14px; font-weight: 500; }
       .metric-variation { font-size: 14px; margin-top: 5px; font-weight: 600; }
       .positive { color: #059669; }
       .negative { color: #dc2626; }
       .neutral { color: #6b7280; }
       
       .alert-critical { background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px; margin: 10px 0; }
       .alert-positive { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 15px; margin: 10px 0; }
       .alert-title { font-weight: 600; margin-bottom: 5px; }
       .alert-critical .alert-title { color: #dc2626; }
       .alert-positive .alert-title { color: #059669; }
       
       .agent-list { list-style: none; padding: 0; }
       .agent-item { background: #f8fafc; padding: 15px; border-radius: 8px; margin: 8px 0; border-left: 4px solid #64748b; }
       .agent-item.critical { border-left-color: #dc2626; }
       .agent-item.attention { border-left-color: #f59e0b; }
       .agent-item.autonomous { border-left-color: #059669; }
       
       .action-plan { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 20px; margin: 15px 0; }
       .action-item { margin: 12px 0; padding: 12px; background: white; border-radius: 6px; border-left: 3px solid #3b82f6; }
       .action-priority { font-weight: 700; color: #1e293b; margin-bottom: 5px; }
       .action-priority.urgent { color: #dc2626; }
       .action-priority.important { color: #f59e0b; }
       .action-priority.monitor { color: #3b82f6; }
       .action-priority.goal { color: #059669; }
       
       .visual-bar { display: inline-block; background: #e2e8f0; height: 20px; width: 100px; border-radius: 10px; overflow: hidden; margin: 0 10px; }
       .visual-fill { height: 100%; background: linear-gradient(90deg, #3b82f6, #1d4ed8); transition: width 0.3s ease; }
       
       .footer { text-align: center; margin-top: 40px; padding: 20px; color: #64748b; font-size: 14px; background: white; border-radius: 8px; }
       
       @media (max-width: 600px) {
           body { padding: 10px; }
           .header { padding: 20px; }
           .block { padding: 20px; }
           .metrics-grid { grid-template-columns: 1fr; }
       }
   </style>
</head>
<body>
   <!-- Header -->
   <div class="header">
       <h1>📊 {{ report_title }}</h1>
       <p>Período: {{ period_start }} - {{ period_end }} | Gerado em: {{ generation_date }}</p>
   </div>

   <!-- Bloco 1: Radar de Autonomia -->
   <div class="block">
       <h2>📊 RADAR DE AUTONOMIA</h2>
       
       <div class="metrics-grid">
           <div class="metric-card">
               <div class="metric-value">{{ radar.total_requests }}</div>
               <div class="metric-label">Total Solicitações</div>
               <div class="metric-variation {{ 'positive' if radar.variation_requests < 0 else 'negative' if radar.variation_requests > 0 else 'neutral' }}">
                   {{ '{:+.1f}'.format(radar.variation_requests) }}%
               </div>
           </div>
           <div class="metric-card">
               <div class="metric-value">{{ radar.general_autonomy }}%</div>
               <div class="metric-label">Autonomia Geral</div>
           </div>
           <div class="metric-card">
               <div class="metric-value">#{{ radar.supervisor_ranking }}</div>
               <div class="metric-label">Ranking</div>
           </div>
       </div>

       <h3>🔍 Diagnóstico Executivo</h3>
       <p><strong>{{ radar.executive_diagnosis }}</strong></p>

       {% if radar.critical_alerts %}
       <h3>🔴 Alertas Críticos</h3>
       {% for alert in radar.critical_alerts %}
       <div class="alert-critical">
           <div class="alert-title">{{ alert.agent }} ({{ alert.supervisor }})</div>
           <div>{{ alert.requests }} casos ({{ '{:+.0f}'.format(alert.variation) }}%) → {{ alert.diagnosis }}</div>
       </div>
       {% endfor %}
       {% endif %}

       {% if radar.positive_highlights %}
       <h3>🟢 Destaques Positivos</h3>
       {% for highlight in radar.positive_highlights %}
       <div class="alert-positive">
           <div class="alert-title">{{ highlight.agent }} ({{ highlight.supervisor }})</div>
           <div>{{ highlight.requests }} casos ({{ '{:+.0f}'.format(highlight.variation) }}%) → {{ highlight.recognition }}</div>
       </div>
       {% endfor %}
       {% endif %}
   </div>

   <!-- Bloco 2: Matriz de Capacitação -->
   <div class="block">
       <h2>📋 MATRIZ DE CAPACITAÇÃO</h2>
       
       {% if matrix.priority_agents %}
       <h3>👥 Agentes Prioritários</h3>
       <ul class="agent-list">
       {% for agent in matrix.priority_agents[:5] %}
           <li class="agent-item {{ agent.risk_level }}">
               <strong>{{ agent.agent }}</strong> ({{ agent.supervisor }})
               <br>{{ agent.requests }} casos → Provável gap: {{ agent.gaps[0] if agent.gaps else 'A identificar' }}
               <br><em>Ação: {{ agent.action }}</em>
           </li>
       {% endfor %}
       </ul>
       {% endif %}

       {% if matrix.time_distribution %}
       <h3>⏱️ Distribuição do Tempo</h3>
       {% for supervisor in matrix.time_distribution %}
       <div style="margin: 15px 0; padding: 15px; background: #f8fafc; border-radius: 8px;">
           <strong>{{ supervisor.supervisor }}:</strong>
           <ul style="margin: 10px 0; list-style: none; padding-left: 0;">
           {% for agent in supervisor.agents_time %}
               <li style="margin: 5px 0;">
                   ├─ {{ agent.agent }}: {{ agent.time_percent }}% do tempo ({{ agent.status }})
               </li>
           {% endfor %}
               <li style="margin: 5px 0; font-weight: 600; color: #059669;">
                   └─ Disponível p/ estratégia: {{ supervisor.strategic_time }}%
               </li>
           </ul>
       </div>
       {% endfor %}
       {% endif %}
   </div>

   <!-- Bloco 3: Dashboard de Produtividade -->
   <div class="block">
       <h2>📈 DASHBOARD DE PRODUTIVIDADE</h2>
       
       {% if productivity.supervisors_evolution %}
       <h3>📊 Evolução por Supervisor (4 semanas)</h3>
       {% for supervisor in productivity.supervisors_evolution %}
       <div style="margin: 20px 0; padding: 15px; background: #f8fafc; border-radius: 8px;">
           <strong>{{ supervisor.supervisor_name }}</strong> - Tendência: {{ supervisor.trend }}
           <br>Atual: {{ supervisor.current_total }} | Anterior: {{ supervisor.previous_total }}
           
           {% if supervisor.agents %}
           <div style="margin-top: 10px;">
               <strong>Por Agente:</strong>
               {% for agent in supervisor.agents[:3] %}
               <div style="margin: 8px 0; display: flex; align-items: center; font-family: monospace;">
                   {{ agent.agent_name }}:   
                   <span style="margin: 0 10px; font-size: 14px;">{{ agent.visual_bar }}</span>
                   {{ agent.current_requests }} ({{ '{:+.0f}'.format(agent.variation) }}%) {{ agent.status }}
               </div>
               {% endfor %}
           </div>
           {% endif %}
       </div>
       {% endfor %}
       {% endif %}
   </div>

   <!-- Bloco 4: Conclusões IA & Plano de Ação -->
   <div class="block">
       <h2>🚀 CONCLUSÕES IA & PLANO DE AÇÃO</h2>
       
       <h3>🧠 Diagnóstico IA</h3>
       <p><strong>{{ conclusions.ai_diagnosis }}</strong></p>

       {% if conclusions.pattern_insights %}
       <h3>🔍 Padrões Identificados</h3>
       <ul>
       {% for pattern in conclusions.pattern_insights %}
           <li>{{ pattern }}</li>
       {% endfor %}
       </ul>
       {% endif %}

       {% if conclusions.action_plan_7_days %}
       <h3>📅 Plano 7 Dias</h3>
       <div class="action-plan">
       {% for action in conclusions.action_plan_7_days %}
           <div class="action-item">
               <div class="action-priority {{ action.priority.lower() }}">{{ action.priority }}:</div>
               <div><strong>{{ action.action }}</strong></div>
               {% if action.details %}
               <div style="font-size: 14px; color: #64748b; margin-top: 5px;">{{ action.details }}</div>
               {% endif %}
           </div>
       {% endfor %}
       </div>
       {% endif %}

       {% if conclusions.expected_results %}
       <h3>🎯 Resultados Esperados</h3>
       <ul>
       {% for result in conclusions.expected_results %}
           <li><strong>{{ result.description }}</strong></li>
       {% endfor %}
       </ul>
       {% endif %}
   </div>

   <!-- Footer -->
   <div class="footer">
       <p>📧 Relatório gerado automaticamente pelo Sistema AI Reports</p>
       <p>🤖 Análise IA: {{ ai_model_used }} | ⏰ {{ analysis_timestamp[:19] }}</p>
       <p>💡 Dúvidas? Entre em contato com o administrador do sistema</p>
   </div>
</body>
</html>
"""
       
       template = Template(html_template)
       return template.render(**template_data)
   
   def _create_text_version(self, template_data: Dict[str, Any]) -> str:
       """Cria versão texto do relatório"""
       
       text_content = f"""
📊 {template_data['report_title']}
Período: {template_data['period_start']} - {template_data['period_end']}
Gerado em: {template_data['generation_date']}

═══════════════════════════════════════════

📊 RADAR DE AUTONOMIA

- Total Solicitações: {template_data['radar']['total_requests']} casos
- Variação: {template_data['radar']['variation_requests']:+.1f}%
- Autonomia Geral: {template_data['radar']['general_autonomy']}%
- Ranking: #{template_data['radar']['supervisor_ranking']}

🔍 DIAGNÓSTICO: {template_data['radar']['executive_diagnosis']}

"""

       # Alertas críticos
       if template_data['radar']['critical_alerts']:
           text_content += "🔴 ALERTAS CRÍTICOS:\n"
           for alert in template_data['radar']['critical_alerts']:
               text_content += f"• {alert['agent']}: {alert['requests']} casos ({alert['variation']:+.0f}%) → {alert['diagnosis']}\n"
           text_content += "\n"

       # Destaques positivos
       if template_data['radar']['positive_highlights']:
           text_content += "🟢 DESTAQUES POSITIVOS:\n"
           for highlight in template_data['radar']['positive_highlights']:
               text_content += f"• {highlight['agent']}: {highlight['requests']} casos ({highlight['variation']:+.0f}%) → {highlight['recognition']}\n"
           text_content += "\n"

       text_content += """═══════════════════════════════════════════

📋 MATRIZ DE CAPACITAÇÃO

"""

       # Agentes prioritários
       if template_data['matrix']['priority_agents']:
           text_content += "AGENTES PRIORITÁRIOS:\n"
           for i, agent in enumerate(template_data['matrix']['priority_agents'][:5], 1):
               gaps_text = ', '.join(agent['gaps'][:2]) if agent['gaps'] else 'A identificar'
               text_content += f"{i}. 🔴 {agent['agent']}: {agent['requests']} casos → Provável gap: {gaps_text}\n"
           text_content += "\n"

       # Distribuição de tempo
       if template_data['matrix']['time_distribution']:
           text_content += "DISTRIBUIÇÃO DO SEU TEMPO:\n"
           for supervisor in template_data['matrix']['time_distribution']:
               text_content += f"├─ {supervisor['supervisor']}:\n"
               for agent in supervisor['agents_time']:
                   text_content += f"│  ├─ {agent['agent']}: {agent['time_percent']}% do tempo ({agent['status']})\n"
               text_content += f"│  └─ Disponível p/ estratégia: {supervisor['strategic_time']}%\n\n"

       text_content += """═══════════════════════════════════════════

📈 DASHBOARD DE PRODUTIVIDADE

"""

       # Evolução por supervisor
       if template_data['productivity']['supervisors_evolution']:
           text_content += "EVOLUÇÃO (4 semanas):\n\n"
           for supervisor in template_data['productivity']['supervisors_evolution']:
               text_content += f"{supervisor['supervisor_name']} - Tendência: {supervisor['trend']}\n"
               text_content += f"Atual: {supervisor['current_total']} | Anterior: {supervisor['previous_total']}\n\n"
               
               if supervisor['agents']:
                   text_content += "POR AGENTE:\n"
                   for agent in supervisor['agents'][:3]:
                       # Converte visual_bar para texto
                       bar_text = "█" * min(10, max(1, agent['current_requests'])) + "░" * (10 - min(10, max(1, agent['current_requests'])))
                       text_content += f"{agent['agent_name']}:   {bar_text} {agent['current_requests']} ({agent['variation']:+.0f}%) {agent['status']}\n"
               text_content += "\n"

       text_content += """═══════════════════════════════════════════

🚀 CONCLUSÕES IA & PLANO DE AÇÃO

"""

       text_content += f"🧠 DIAGNÓSTICO:\n{template_data['conclusions']['ai_diagnosis']}\n\n"

       # Padrões identificados
       if template_data['conclusions']['pattern_insights']:
           text_content += "🔍 PADRÕES IDENTIFICADOS:\n"
           for pattern in template_data['conclusions']['pattern_insights']:
               text_content += f"• {pattern}\n"
           text_content += "\n"

       # Plano de ação
       if template_data['conclusions']['action_plan_7_days']:
           text_content += "📅 PLANO 7 DIAS:\n"
           for action in template_data['conclusions']['action_plan_7_days']:
               text_content += f"{action['priority']}: {action['action']}\n"
               if action.get('details'):
                   text_content += f"   → {action['details']}\n"
           text_content += "\n"

       # Resultados esperados
       if template_data['conclusions']['expected_results']:
           text_content += "🎯 RESULTADOS ESPERADOS:\n"
           for result in template_data['conclusions']['expected_results']:
               text_content += f"• {result['description']}\n"
           text_content += "\n"

       text_content += f"""═══════════════════════════════════════════

📧 Relatório gerado automaticamente pelo Sistema AI Reports
🤖 Análise IA: {template_data['ai_model_used']} | ⏰ {template_data['analysis_timestamp'][:19]}
💡 Dúvidas? Entre em contato com o administrador do sistema
"""

       return text_content
   
   def _generate_subject(self, template_data: Dict[str, Any]) -> str:
       """Gera assunto do email baseado nos dados"""
       
       radar = template_data['radar']
       critical_count = len(radar['critical_alerts'])
       autonomy = radar['general_autonomy']
       
       # Define emoji e status baseado na situação
       if critical_count >= 3:
           emoji = "🔴"
           status = "CRÍTICO"
       elif critical_count >= 1:
           emoji = "🟡" 
           status = "ATENÇÃO"
       elif autonomy >= 80:
           emoji = "🟢"
           status = "EXCELENTE"
       else:
           emoji = "📊"
           status = "NORMAL"
       
       base_subject = f"{emoji} Relatório de Autonomia Semanal"
       
       if template_data.get('supervisor_name'):
           base_subject += f" - {template_data['supervisor_name']}"
       
       base_subject += f" | {status}"
       
       # Adiciona métrica principal
       if radar['total_requests'] > 0:
           base_subject += f" | {radar['total_requests']} casos"
           if radar['variation_requests'] != 0:
               base_subject += f" ({radar['variation_requests']:+.0f}%)"
       
       return base_subject
   
   def _send_email(self, recipients: List[str], subject: str, html_content: str, text_content: str) -> Dict[str, Any]:
       """Envia email usando SMTP"""
       
       try:
           # CORRIGIDO: Usar SMTP_FROM_EMAIL para remetente
           try:
               from config import Config
               from_email = Config.SMTP_FROM_EMAIL
           except:
               from_email = "atendepro@timeismoney.tec.br"  # fallback
           
           # Cria mensagem
           message = MIMEMultipart("alternative")
           message["Subject"] = subject
           message["From"] = f"{self.sender_name} <{from_email}>"  # CORRIGIDO: usar from_email
           message["To"] = ", ".join(recipients)
           
           # Adiciona versões texto e HTML
           text_part = MIMEText(text_content, "plain", "utf-8")
           html_part = MIMEText(html_content, "html", "utf-8")
           
           message.attach(text_part)
           message.attach(html_part)
           
           # Conecta e envia
           context = ssl.create_default_context()
           server = smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'])
           server.starttls(context=context)
           server.login(self.smtp_config['email'], self.smtp_config['password'])
           
           text = message.as_string()
           server.sendmail(from_email, recipients, text)  # CORRIGIDO: usar from_email para envio
           server.quit()
           
           return {
               'success': True,
               'status': 'Email enviado com sucesso',
               'recipients': recipients,
               'subject': subject,
               'from_email': from_email  # Para debug
           }
           
       except Exception as e:
           logger.error(f"Erro ao enviar email: {e}")
           return {
               'success': False,
               'error': str(e),
               'status': 'Falha no envio do email'
           }
   
   # REMOVIDO: _generate_test_data() - não precisa mais de dados fake

# Função auxiliar para facilitar uso
def send_autonomy_report(
   analysis_data: Dict[str, Any],
   smtp_config: Dict[str, str],
   recipients: List[str],
   supervisor_name: Optional[str] = None
) -> Dict[str, Any]:
   """
   Função helper para envio de relatórios
   
   Usage:
       from ai_reports.email_sender import send_autonomy_report
       
       result = send_autonomy_report(
           analysis_data=analysis,
           smtp_config=config,
           recipients=['supervisor@company.com']
       )
   """
   sender = AutonomyEmailSender(smtp_config)
   return sender.send_weekly_report(analysis_data, recipients, supervisor_name)

if __name__ == "__main__":
   # Teste rápido
   print("🧪 Testando Email Sender...")
   
   # Configuração de teste (usar variáveis de ambiente)
   test_config = {
       'server': 'smtp.gmail.com',
       'port': 587,
       'email': os.getenv('SMTP_EMAIL', 'test@example.com'),
       'password': os.getenv('SMTP_PASSWORD', 'test_password'),
       'sender_name': 'AI Reports Test'
   }
   
   sender = AutonomyEmailSender(test_config)
   
   # Testa conexão
   if test_config['email'] != 'test@example.com':
       connection = sender.test_connection()
       print(f"📧 Conexão SMTP: {connection['status']}")
   else:
       print("⚠️ Configure SMTP_EMAIL e SMTP_PASSWORD para testar conexão real")
   
   print("✅ Email Sender configurado com dados reais!")