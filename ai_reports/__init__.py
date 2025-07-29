# ai_reports/__init__.py
"""
🤖 AtendePro AI Reports Module

Módulo responsável por gerar relatórios automáticos com análise de IA
para supervisores e coordenação.

Componentes:
- data_collector: Extração de dados do banco
- ai_analyzer: Análise via Ollama/Qwen 2.5
- email_sender: Envio de relatórios por email  
- scheduler: Agendamento automático
"""

__version__ = "1.0.0"
__author__ = "AtendePro Team"

# Importações principais para facilitar uso
from .data_collector import DataCollector, collect_weekly_data, test_data_collection

__all__ = [
    'DataCollector',
    'collect_weekly_data', 
    'test_data_collection'
]