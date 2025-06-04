import discord
import logging
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import User, Agente, Atendimento
from config import Config

# Token do bot vindo da variável de ambiente (recomendo configurar no .env)
TOKEN = os.getenv('DISCORD_TOKEN', 'SEU_TOKEN_AQUI')

KEYWORD = '@@problema'

# Configuração do logger para console e arquivo, com encoding UTF-8
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler('bot.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers = []
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Configuração dos intents do Discord para receber conteúdo das mensagens
intents = discord.Intents.default()
intents.message_content = True

# Configuração do banco de dados usando URI do config.py
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

class MeuBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        logger.info(f'Bot conectado como {self.user}')
        logger.info(f'Bot está em {len(self.guilds)} servidores')
        logger.info(f'Servidores: {[f"{guild.name} (ID: {guild.id})" for guild in self.guilds]}')

        try:
            session = Session()
            agentes_count = session.query(Agente).count()
            supervisores_count = session.query(User).filter_by(tipo='supervisor').count()
            session.close()
            logger.info(f'Conexão com BD AWS RDS OK. {agentes_count} agentes e {supervisores_count} supervisores cadastrados.')
        except Exception as e:
            logger.error(f'Erro ao conectar com BD AWS RDS: {e}')

    async def on_message(self, message):
        try:
            channel_info = f"#{message.channel.name}" if hasattr(message.channel, 'name') else "DM"
            server_info = f" no servidor {message.guild.name} (ID: {message.guild.id})" if message.guild else " em DM"
            logger.info(f"Mensagem de {message.author} ({message.author.id}){server_info} em {channel_info}: {message.content}")

            if message.author == self.user or message.author.bot:
                return

            if KEYWORD.lower() not in message.content.lower():
                logger.debug(f"Palavra-chave '{KEYWORD}' não encontrada na mensagem")
                return

            logger.info(f"Palavra-chave detectada! Processando mensagem de {message.author}")

            session = Session()
            try:
                discord_id = str(message.author.id)
                server_id = str(message.guild.id) if message.guild else None

                logger.info(f"Buscando agente com discord_id: {discord_id}")
                logger.info(f"Servidor da mensagem: {server_id}")

                agente = session.query(Agente).filter_by(discord_id=discord_id).first()
                if not agente:
                    logger.warning(f'Agente com discord_id {discord_id} não encontrado no banco.')
                    await self.enviar_erro_agente_nao_cadastrado(message.author)
                    return

                logger.info(f"Agente encontrado: {agente.nome}")

                supervisor = None
                if server_id:
                    supervisores = session.query(User).filter_by(tipo='supervisor').all()
                    for sup in supervisores:
                        if hasattr(sup, 'atende_servidor') and sup.atende_servidor(server_id):
                            supervisor = sup
                            logger.info(f"Supervisor encontrado pelo servidor: {supervisor.nome}")
                            break

                if not supervisor:
                    supervisor = agente.supervisor
                    logger.info(f"Usando supervisor principal do agente: {supervisor.nome if supervisor else 'Nenhum'}")

                if not supervisor:
                    logger.warning(f'Nenhum supervisor encontrado para agente {agente.nome} no servidor {server_id}.')
                    await self.enviar_erro_supervisor_nao_encontrado(message.author, agente.nome)
                    return

                atendimento = Atendimento(
                    agente_id=agente.id,
                    supervisor_id=supervisor.id,
                    conteudo=message.content,
                    classificacao=None,
                    status='pendente',
                    data_hora=datetime.utcnow(),
                    servidor_discord_id=server_id
                )
                session.add(atendimento)
                session.commit()
                logger.info(f'Atendimento criado (ID: {atendimento.id}) para agente {agente.nome} com supervisor {supervisor.nome}')

                await self.enviar_confirmacao_agente(message.author, agente.nome, supervisor.nome)
                await self.enviar_notificacao_supervisor(supervisor, agente.nome, message.content, message.guild.name if message.guild else "DM")

            except Exception as e:
                logger.error(f'Erro ao processar atendimento: {e}', exc_info=True)
                session.rollback()
                await self.enviar_erro_generico(message.author)
            finally:
                session.close()

        except Exception as e:
            logger.error(f'Erro crítico no on_message: {e}', exc_info=True)

    async def enviar_confirmacao_agente(self, user, nome_agente, nome_supervisor):
        try:
            await user.send(
                f"✅ Olá {nome_agente}! Seu atendimento foi recebido com sucesso.\n"
                f"Supervisor responsável: **{nome_supervisor}**\n"
                "Em breve o supervisor entrará em contato com você por DM."
            )
            logger.info(f'Confirmação enviada para {nome_agente}')
        except discord.Forbidden:
            logger.warning(f'Usuário {nome_agente} não permite DMs')
        except Exception as e:
            logger.error(f'Erro ao enviar DM para {nome_agente}: {e}')

    async def enviar_notificacao_supervisor(self, supervisor, nome_agente, conteudo, nome_servidor):
        try:
            if not supervisor.discord_id:
                logger.warning(f'Supervisor {supervisor.nome} não possui discord_id')
                return

            user_supervisor = await self.fetch_user(int(supervisor.discord_id))
            await user_supervisor.send(
                f"🚨 **Novo atendimento recebido**\n\n"
                f"**Servidor:** {nome_servidor}\n"
                f"**Agente:** {nome_agente}\n"
                f"**Conteúdo:** {conteudo}\n\n"
                "Por favor, entre em contato com o agente o mais breve possível."
            )
            logger.info(f'Notificação enviada ao supervisor {supervisor.nome}')
        except discord.NotFound:
            logger.error(f'Usuário do supervisor {supervisor.nome} não encontrado (ID: {supervisor.discord_id})')
        except discord.Forbidden:
            logger.warning(f'Supervisor {supervisor.nome} não permite DMs')
        except Exception as e:
            logger.error(f'Erro ao notificar supervisor {supervisor.nome}: {e}')

    async def enviar_erro_agente_nao_cadastrado(self, user):
        try:
            await user.send(
                "❌ **Erro:** Você não está cadastrado no sistema.\n"
                "Entre em contato com o administrador para realizar o cadastro."
            )
        except Exception:
            logger.error(f'Não foi possível enviar mensagem de erro para {user}')

    async def enviar_erro_supervisor_nao_encontrado(self, user, nome_agente):
        try:
            await user.send(
                f"❌ **Erro:** Nenhum supervisor disponível para atender {nome_agente} neste servidor.\n"
                "Entre em contato com o administrador."
            )
        except Exception:
            logger.error(f'Não foi possível enviar mensagem de erro para {user}')

    async def enviar_erro_generico(self, user):
        try:
            await user.send(
                "❌ **Erro interno:** Não foi possível processar sua solicitação.\n"
                "Tente novamente em alguns minutos ou entre em contato com o administrador."
            )
        except Exception:
            logger.error(f'Não foi possível enviar mensagem de erro genérico para {user}')

    async def on_disconnect(self):
        logger.warning('Bot desconectado do Discord')

    async def on_resumed(self):
        logger.info('Conexão com Discord restaurada')

# Instancia o bot com intents configurados
client = MeuBot(intents=intents)

def main():
    try:
        logger.info('Iniciando bot standalone...')
        client.run(TOKEN)
    except discord.LoginFailure:
        logger.error('Token inválido! Verifique o token do bot.')
    except Exception as e:
        logger.error(f'Erro ao iniciar bot: {e}', exc_info=True)

if __name__ == '__main__':
    main()
