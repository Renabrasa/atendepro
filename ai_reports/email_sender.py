# ai_reports/email_sender.py
"""
📧 Email Sender - Envio de relatórios AI por email
Processa templates e envia relatórios semanais para supervisores
"""

import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import os

from jinja2 import Environment, FileSystemLoader
from config import Config

# Configurar logging
logger = logging.getLogger(__name__)


class EmailSender:
    """
    📧 Gerenciador de envio de emails para relatórios AI
    
    Responsável por processar templates, formatar dados e 
    enviar relatórios semanais por email
    """
    
    def __init__(self):
        """Inicializa o sender de email"""
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.smtp_username = Config.SMTP_USERNAME
        self.smtp_password = Config.SMTP_PASSWORD
        self.smtp_use_tls = Config.SMTP_USE_TLS
        self.smtp_use_ssl = Config.SMTP_USE_SSL
        self.from_email = Config.SMTP_FROM_EMAIL
        self.from_name = Config.SMTP_FROM_NAME
        self.debug = Config.AI_REPORTS_DEBUG
        
        # Configurar Jinja2 para templates
        template_dir = Path(__file__).parent / 'templates'
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )
        
        if self.debug:
            logger.info(f"📧 EmailSender inicializado - {self.smtp_server}:{self.smtp_port}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        🔌 Testa conexão SMTP
        
        Returns:
            Dict com resultado do teste
        """
        try:
            if self.debug:
                logger.info("🔌 Testando conexão SMTP...")
            
            # Criar conexão SSL/TLS conforme configuração
            if self.smtp_use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.smtp_use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            # Testar autenticação
            server.login(self.smtp_username, self.smtp_password)
            server.quit()
            
            result = {
                'success': True,
                'status': 'Connected',
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port,
                'auth_method': 'SSL' if self.smtp_use_ssl else 'TLS' if self.smtp_use_tls else 'None',
                'from_email': self.from_email,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info("✅ Conexão SMTP bem-sucedida")
            return result
            
        except Exception as e:
            error_msg = f"Erro na conexão SMTP: {e}"
            logger.error(f"❌ {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port,
                'timestamp': datetime.now().isoformat()
            }
    
    def send_weekly_report(self, supervisor_data: Dict[str, Any], 
                          ai_analysis: Dict[str, Any],
                          weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        📊 Envia relatório semanal para um supervisor
        
        Args:
            supervisor_data: Dados do supervisor específico
            ai_analysis: Análise IA completa
            weekly_data: Dados da semana coletados
            
        Returns:
            Dict com resultado do envio
        """
        try:
            if self.debug:
                supervisor_name = supervisor_data['supervisor']['name']
                logger.info(f"📧 Preparando email para {supervisor_name}...")
            
            # Preparar dados para template
            template_data = self._prepare_template_data(supervisor_data, ai_analysis, weekly_data)
            
            # Renderizar template HTML
            html_content = self._render_template('weekly_report.html', template_data)
            
            # Preparar email
            recipient_email = supervisor_data['supervisor']['email']
            subject = self._generate_subject(template_data)
            
            # Enviar email
            result = self._send_email(
                to_email=recipient_email,
                subject=subject,
                html_content=html_content,
                template_data=template_data
            )
            
            # Log resultado
            if result['success']:
                logger.info(f"✅ Email enviado para {supervisor_name} ({recipient_email})")
            else:
                logger.error(f"❌ Falha no envio para {supervisor_name}: {result['error']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Erro no envio do relatório: {e}"
            logger.error(f"❌ {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }
    
    def send_reports_to_all_supervisors(self, weekly_data: Dict[str, Any], 
                                       ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        📧 Envia relatórios para todos os supervisores
        
        Args:
            weekly_data: Dados da semana coletados
            ai_analysis: Análise IA completa
            
        Returns:
            Dict com resumo dos envios
        """
        results = {
            'total_supervisors': len(ai_analysis['supervisors_analysis']),
            'successful_sends': 0,
            'failed_sends': 0,
            'send_results': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if self.debug:
                logger.info(f"📧 Enviando relatórios para {results['total_supervisors']} supervisores...")
            
            for supervisor_analysis in ai_analysis['supervisors_analysis']:
                # Encontrar dados do supervisor nos dados originais
                supervisor_data = None
                for sup_data in weekly_data['supervisors_data']:
                    if sup_data['supervisor']['id'] == supervisor_analysis['supervisor_id']:
                        supervisor_data = sup_data
                        break
                
                if not supervisor_data:
                    logger.warning(f"⚠️ Dados do supervisor ID {supervisor_analysis['supervisor_id']} não encontrados")
                    continue
                
                # Combinar dados para o template
                combined_supervisor_data = {
                    **supervisor_data,
                    'ai_analysis': supervisor_analysis
                }
                
                # Enviar email
                send_result = self.send_weekly_report(
                    combined_supervisor_data, 
                    ai_analysis, 
                    weekly_data
                )
                
                # Registrar resultado
                results['send_results'].append({
                    'supervisor_name': supervisor_data['supervisor']['name'],
                    'supervisor_email': supervisor_data['supervisor']['email'],
                    'success': send_result['success'],
                    'error': send_result.get('error'),
                    'timestamp': send_result['timestamp']
                })
                
                if send_result['success']:
                    results['successful_sends'] += 1
                else:
                    results['failed_sends'] += 1
            
            logger.info(f"📧 Envios concluídos: {results['successful_sends']} sucessos, {results['failed_sends']} falhas")
            
        except Exception as e:
            logger.error(f"❌ Erro no envio em lote: {e}")
            results['batch_error'] = str(e)
        
        return results
    
    def _prepare_template_data(self, supervisor_data: Dict[str, Any], 
                          ai_analysis: Dict[str, Any],
                          weekly_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        📋 Prepara dados para renderização do template
        """
        # Dados básicos do período
        current_week = weekly_data['metadata']['current_week']
        supervisor_name = supervisor_data['supervisor']['name']
        
        # Métricas do supervisor
        current_tickets = supervisor_data['current_week']['total_tickets']
        change = supervisor_data['comparison']['absolute_change']
        change_percent = supervisor_data['comparison']['percent_change']
        
        # Classificar mudança
        if change > 0:
            trend_class = 'positive'
            change_text = f"+{change} ({change_percent:+.1f}%)"
        elif change < 0:
            trend_class = 'negative' 
            change_text = f"{change} ({change_percent:.1f}%)"
        else:
            trend_class = 'neutral'
            change_text = "Sem mudança"
        
        # Encontrar análise específica do supervisor
        supervisor_ai_analysis = None
        for analysis in ai_analysis['supervisors_analysis']:
            if analysis['supervisor_id'] == supervisor_data['supervisor']['id']:
                supervisor_ai_analysis = analysis
                break
        
        # Agentes com dados enriquecidos
        agents_performance = []
        if supervisor_ai_analysis:
            for agent_insight in supervisor_ai_analysis['agents_insights']:
                agents_performance.append({
                    'agent_name': agent_insight['agent_name'],
                    'current_tickets': agent_insight['current_tickets'],
                    'change': agent_insight['change'],
                    'change_percent': agent_insight['change_percent'],
                    'performance_level': agent_insight['performance_level'],
                    'status': agent_insight['status'],
                    'needs_attention': agent_insight['needs_attention']
                })
        
        # Posição no ranking
        all_supervisors = ai_analysis['supervisors_analysis']
        ranking_position = None
        for i, analysis in enumerate(sorted(all_supervisors, key=lambda x: x['key_metrics']['current_tickets'], reverse=True), 1):
            if analysis['supervisor_id'] == supervisor_data['supervisor']['id']:
                ranking_position = i
                break
        
        ranking_text = f"#{ranking_position} no ranking" if ranking_position else "Ranking indisponível"
        
        # Próximo relatório
        next_monday = self._get_next_monday()
        
        template_data = {
            # Informações básicas
            'supervisor_name': supervisor_name,
            'period_label': current_week['period_label'],
            'generated_at': datetime.now().strftime('%d/%m/%Y às %H:%M'),
            'next_report_date': next_monday.strftime('%d/%m/%Y'),
            
            # Métricas principais
            'total_tickets': current_tickets,
            'change_text': change_text,
            'trend_class': trend_class,
            'agents_count': len(supervisor_data['current_week']['agents_performance']),
            'ranking_text': ranking_text,
            
            # CORRIGIDO: Usar novos campos ao invés de global_analysis
            'executive_dashboard': ai_analysis.get('executive_dashboard', {}),
            'intelligent_insights': ai_analysis.get('intelligent_insights', {}),
            'supervisor_analysis': supervisor_ai_analysis['performance_analysis'] if supervisor_ai_analysis else 'Análise indisponível',
            'recommendations': supervisor_ai_analysis['recommendations'] if supervisor_ai_analysis else ['Revisar dados manualmente'],
            
            # Lista de agentes
            'agents_performance': agents_performance,
            
            # Informações técnicas
            'data_source_info': f"{len(weekly_data['supervisors_data'])} supervisores, {ai_analysis['summary']['total_tickets']} atendimentos totais",
            'ai_model': ai_analysis['metadata']['ai_model']
        }
        
        return template_data
    
    def _render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        🎨 Renderiza template HTML com dados
        """
        try:
            template = self.jinja_env.get_template(template_name)
            html_content = template.render(**data)
            
            if self.debug:
                logger.info(f"✅ Template {template_name} renderizado - {len(html_content)} caracteres")
            
            return html_content
            
        except Exception as e:
            logger.error(f"❌ Erro na renderização do template: {e}")
            raise
    
    def _generate_subject(self, template_data: Dict[str, Any]) -> str:
        """
        📝 Gera assunto do email
        """
        supervisor_name = template_data['supervisor_name']
        period = template_data['period_label']
        total_tickets = template_data['total_tickets']
        trend = template_data['trend_class']
        
        # Emoji baseado na tendência
        trend_emoji = {
            'positive': '📈',
            'negative': '📉', 
            'neutral': '📊'
        }.get(trend, '📊')
        
        subject = f"{trend_emoji} AtendePro AI - Relatório Semanal | {supervisor_name} | {period} | {total_tickets} atendimentos"
        
        return subject
    
    def _send_email(self, to_email: str, subject: str, html_content: str, 
                   template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        📧 Envia email via SMTP
        """
        try:
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Adicionar cabeçalhos extras
            msg['X-Mailer'] = 'AtendePro AI Reports v1.0'
            msg['X-Priority'] = '3'  # Normal priority
            
            # Criar versão texto simples (fallback)
            text_content = self._create_text_version(template_data)
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            
            # Adicionar versão HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            # Anexar ambas as versões
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Estabelecer conexão e enviar
            if self.smtp_use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.smtp_use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
            
            # Autenticar e enviar
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            result = {
                'success': True,
                'to_email': to_email,
                'subject': subject,
                'timestamp': datetime.now().isoformat(),
                'html_size': len(html_content),
                'text_size': len(text_content)
            }
            
            if self.debug:
                logger.info(f"✅ Email enviado - {len(html_content)} bytes HTML")
            
            return result
            
        except Exception as e:
            error_msg = f"Erro no envio SMTP: {e}"
            logger.error(f"❌ {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'to_email': to_email,
                'timestamp': datetime.now().isoformat()
            }
    
    def _create_text_version(self, template_data: Dict[str, Any]) -> str:
        """
        📝 Cria versão texto simples do email
        """
        supervisor_name = template_data['supervisor_name']
        period = template_data['period_label']
        total_tickets = template_data['total_tickets']
        change_text = template_data['change_text']
        
        # Usar executive_dashboard ao invés de global_analysis
        executive_dashboard = template_data.get('executive_dashboard', {})
        dashboard_summary = f"Dashboard: {executive_dashboard.get('total_tickets', 0)} atendimentos totais"
        
        text_content = f"""
    AtendePro AI - Relatório Semanal

    Olá, {supervisor_name}!

    PERÍODO: {period}

    RESUMO:
    • Total de atendimentos: {total_tickets}
    • Variação: {change_text}
    • Agentes ativos: {template_data['agents_count']}
    • Posição: {template_data['ranking_text']}

    DASHBOARD EXECUTIVO:
    {dashboard_summary}
    """
        
        # Adicionar ranking se disponível
        ranking = executive_dashboard.get('ranking', [])
        if ranking:
            text_content += "\nTOP SUPERVISORES:\n"
            for rank in ranking[:3]:
                text_content += f"• {rank}\n"
        
        # Adicionar alertas se disponíveis
        alerts = executive_dashboard.get('alerts', [])
        if alerts:
            text_content += "\nALERTAS:\n"
            for alert in alerts[:3]:
                text_content += f"⚠️ {alert}\n"
        
        text_content += f"""

    ANÁLISE ESPECÍFICA:
    {template_data['supervisor_analysis']}

    RECOMENDAÇÕES:
    """
        
        for i, rec in enumerate(template_data['recommendations'], 1):
            text_content += f"{i}. {rec}\n"
        
        text_content += f"""

    AGENTES DA EQUIPE:
    """
        
        for agent in template_data['agents_performance']:
            status_text = "⚠️" if agent['needs_attention'] else "✅"
            text_content += f"{status_text} {agent['agent_name']}: {agent['current_tickets']} atendimentos ({agent['change']:+d})\n"
        
        text_content += f"""

    Este relatório foi gerado automaticamente em {template_data['generated_at']}.
    Próximo relatório: {template_data['next_report_date']}

    AtendePro AI Reports - Gestão Inteligente de Atendimentos
    """
        
        return text_content.strip()
    
    def _get_next_monday(self) -> datetime:
        """
        📅 Calcula próxima segunda-feira
        """
        today = datetime.now()
        days_ahead = 7 - today.weekday()  # 0 = Monday, 6 = Sunday
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)
        return next_monday
    
    def send_test_email(self, test_email: str) -> Dict[str, Any]:
        """
        🧪 Envia email de teste
        """
        try:
            # Dados fictícios para teste
            test_data = {
                'supervisor_name': 'Supervisor Teste',
                'period_label': '09/06 a 15/06',  # Primeira quinzena de junho
                'generated_at': datetime.now().strftime('%d/%m/%Y às %H:%M'),
                'next_report_date': self._get_next_monday().strftime('%d/%m/%Y'),
                'total_tickets': 25,
                'change_text': '+5 (+25.0%)',
                'trend_class': 'positive',
                'agents_count': 3,
                'ranking_text': '#2 no ranking',
                
                # CORRIGIDO: Usar executive_dashboard ao invés de global_analysis
                'executive_dashboard': {
                    'total_tickets': 75,
                    'variation': 15,
                    'variation_percent': 25.0,
                    'supervisor_count': 3,
                    'ranking': [
                        '1º Supervisor A: 30 (+8)',
                        '2º Supervisor Teste: 25 (+5)',
                        '3º Supervisor C: 20 (+2)'
                    ],
                    'alerts': [
                        'Supervisor A: +36.4% - requer atenção'
                    ],
                    'patterns': [
                        'Supervisor A: Agente X concentra 40% dos casos'
                    ]
                },
                'intelligent_insights': {
                    'performance_alerts': ['Supervisor A: +36.4% - requer atenção'],
                    'concentration_patterns': ['Supervisor A: Agente X concentra 40% dos casos'],
                    'ranking_summary': [
                        '1º Supervisor A: 30 (+8)',
                        '2º Supervisor Teste: 25 (+5)',
                        '3º Supervisor C: 20 (+2)'
                    ]
                },
                
                'supervisor_analysis': 'Supervisor Teste, sua equipe processou 25 casos esta semana. Agente A se destaca com 12 atendimentos, demonstrando boa capacidade técnica. Recomendo manter atual distribuição para otimizar performance.',
                'recommendations': [
                    'Manter atual distribuição de carga entre agentes',
                    'Reconhecer performance do Agente A',
                    'Monitorar capacidade para próxima semana'
                ],
                'agents_performance': [
                    {
                        'agent_name': 'Agente A',
                        'current_tickets': 12,
                        'change': 3,
                        'performance_level': 'Crescimento estável',
                        'status': 'success',
                        'needs_attention': False
                    },
                    {
                        'agent_name': 'Agente B', 
                        'current_tickets': 8,
                        'change': 1,
                        'performance_level': 'Estável',
                        'status': 'neutral',
                        'needs_attention': False
                    },
                    {
                        'agent_name': 'Agente C',
                        'current_tickets': 5,
                        'change': 1,
                        'performance_level': 'Crescimento estável',
                        'status': 'success',
                        'needs_attention': False
                    }
                ],
                'data_source_info': '3 supervisores, 75 atendimentos totais',
                'ai_model': 'qwen2.5:3b'
            }
            
            # Renderizar template
            html_content = self._render_template('weekly_report.html', test_data)
            
            # Enviar email de teste
            subject = f"🧪 TESTE - AtendePro AI - Relatório Semanal | {test_data['period_label']}"
            
            result = self._send_email(test_email, subject, html_content, test_data)
            
            if result['success']:
                logger.info(f"✅ Email de teste enviado para {test_email}")
            else:
                logger.error(f"❌ Falha no email de teste: {result['error']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Erro no email de teste: {e}"
            logger.error(f"❌ {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }


# Funções de conveniência para uso externo
def send_weekly_reports(weekly_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    🔧 Função utilitária para enviar relatórios semanais
    
    Args:
        weekly_data: Dados coletados pelo DataCollector
        ai_analysis: Análise gerada pelo AIAnalyzer
        
    Returns:
        Resultado dos envios
    """
    sender = EmailSender()
    return sender.send_reports_to_all_supervisors(weekly_data, ai_analysis)


def test_email_connection() -> Dict[str, Any]:
    """
    🧪 Função utilitária para testar conexão de email
    
    Returns:
        Resultado do teste de conexão
    """
    sender = EmailSender()
    return sender.test_connection()


def send_test_email(test_email: str) -> Dict[str, Any]:
    """
    🧪 Função utilitária para enviar email de teste
    
    Args:
        test_email: Email de destino para teste
        
    Returns:
        Resultado do envio de teste
    """
    sender = EmailSender()
    return sender.send_test_email(test_email)