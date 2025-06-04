import threading
import asyncio
import logging
import time
import signal
import sys
from app import app
from bot import client, TOKEN

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('application.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Variáveis globais para controle
flask_thread = None
bot_task = None
loop = None
shutdown_event = threading.Event()

def run_flask():
    """Executa o servidor Flask"""
    try:
        logger.info("Iniciando servidor Flask...")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Erro no servidor Flask: {e}")
        shutdown_event.set()

async def run_bot_async():
    """Executa o bot Discord de forma assíncrona"""
    try:
        logger.info("Iniciando bot Discord...")
        await client.start(TOKEN)
    except Exception as e:
        logger.error(f"Erro no bot Discord: {e}")
        shutdown_event.set()

def signal_handler(signum, frame):
    """Handler para sinais de interrupção"""
    logger.info(f"Recebido sinal {signum}. Iniciando shutdown...")
    shutdown_event.set()

async def main():
    """Função principal que coordena Flask e Discord bot"""
    global flask_thread, bot_task, loop
    
    # Configurar handlers de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Iniciar Flask em thread separada
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info("Thread do Flask iniciada")
        
        # Aguardar um pouco para Flask inicializar
        await asyncio.sleep(2)
        
        # Iniciar bot Discord
        bot_task = asyncio.create_task(run_bot_async())
        logger.info("Task do bot Discord criada")
        
        # Loop principal - monitora shutdown
        while not shutdown_event.is_set():
            await asyncio.sleep(1)
            
            # Verificar se Flask thread ainda está viva
            if not flask_thread.is_alive():
                logger.error("Thread do Flask morreu!")
                shutdown_event.set()
                break
                
            # Verificar se bot task terminou
            if bot_task.done():
                logger.error("Task do bot Discord terminou!")
                shutdown_event.set()
                break
        
        logger.info("Iniciando processo de shutdown...")
        
    except Exception as e:
        logger.error(f"Erro crítico na aplicação: {e}")
    finally:
        await cleanup()

async def cleanup():
    """Limpa recursos antes de encerrar"""
    global bot_task, flask_thread
    
    logger.info("Executando cleanup...")
    
    # Cancelar bot task
    if bot_task and not bot_task.done():
        logger.info("Cancelando task do bot...")
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            logger.info("Task do bot cancelada")
        except Exception as e:
            logger.error(f"Erro ao cancelar bot task: {e}")
    
    # Fechar conexão do bot
    if not client.is_closed():
        logger.info("Fechando conexão do bot Discord...")
        await client.close()
    
    logger.info("Cleanup concluído")

def run_application():
    """Ponto de entrada principal"""
    try:
        logger.info("=== INICIANDO APLICAÇÃO COMPLETA ===")
        logger.info("Flask + Discord Bot")
        logger.info("Pressione Ctrl+C para parar")
        logger.info("=" * 40)
        
        # Verificar se o token existe
        if not TOKEN or TOKEN == 'SEU_TOKEN_AQUI':
            logger.error("Token do Discord não configurado!")
            logger.error("Configure a variável de ambiente DISCORD_TOKEN ou edite o arquivo bot.py")
            return
        
        # Executar aplicação
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("Interrupção pelo usuário (Ctrl+C)")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
    finally:
        logger.info("Aplicação encerrada")

if __name__ == '__main__':
    run_application()