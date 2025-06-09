import discord
import logging
import sys
import os
import asyncio
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import User, Agente, Atendimento
from config import Config

# Token do bot vindo da variável de ambiente
TOKEN = os.getenv('DISCORD_TOKEN', 'SEU_TOKEN_AQUI')

KEYWORD = '@@problema'

# Configuração do logger
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

# Configuração dos intents do Discord
intents = discord.Intents.default()
intents.message_content = True

# Configuração do banco de dados
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

class SupervisorSelectView(discord.ui.View):
    def __init__(self, supervisores, agente, conteudo_original, server_id):
        super().__init__(timeout=300)  # 5 minutos para responder
        self.supervisores = supervisores
        self.agente = agente
        self.conteudo_original = conteudo_original
        self.server_id = server_id
        
        # Adiciona botões para cada supervisor
        for i, supervisor in enumerate(supervisores):
            button = SupervisorButton(
                supervisor=supervisor,
                agente=agente,
                conteudo=conteudo_original,
                server_id=server_id,
                style=discord.ButtonStyle.primary,
                label=f"{supervisor.nome}",
                custom_id=f"supervisor_{supervisor.id}"
            )
            self.add_item(button)

    async def on_timeout(self):
        # Remove os botões quando expira
        for item in self.children:
            item.disabled = True

class SupervisorButton(discord.ui.Button):
    def __init__(self, supervisor, agente, conteudo, server_id, **kwargs):
        super().__init__(**kwargs)
        self.supervisor = supervisor
        self.agente = agente
        self.conteudo = conteudo
        self.server_id = server_id

    async def callback(self, interaction: discord.Interaction):
        session = Session()
        atendimento_criado = False
        atendimento_id = None
        
        try:
            # 1. PRIMEIRO: Criar o atendimento no banco
            atendimento = Atendimento(
                agente_id=self.agente.id,
                supervisor_id=self.supervisor.id,
                conteudo=self.conteudo,
                classificacao=None,
                status='pendente',
                data_hora=datetime.utcnow(),
                servidor_discord_id=self.server_id
            )
            session.add(atendimento)
            session.commit()
            atendimento_criado = True
            atendimento_id = atendimento.id
            
            logger.info(f'✅ Atendimento criado (ID: {atendimento.id}) para agente {self.agente.nome} com supervisor {self.supervisor.nome}')
            
            # 2. SEGUNDO: Responder IMEDIATAMENTE ao usuário
            await interaction.response.edit_message(
                content=f"✅ **Atendimento criado com sucesso!**\n\n"
                        f"**Agente:** {self.agente.nome}\n"
                        f"**Supervisor selecionado:** {self.supervisor.nome}\n"
                        f"**ID do atendimento:** #{atendimento.id}\n\n"
                        f"🔄 Tentando notificar o supervisor...",
                view=None  # Remove os botões
            )
            
            # 3. TERCEIRO: Tentar notificar supervisor (sem quebrar se falhar)
            notificacao_sucesso = await self.tentar_notificar_supervisor(
                self.supervisor, 
                self.agente.nome, 
                self.conteudo,
                interaction.guild.name if interaction.guild else "DM",
                interaction
            )
            
            # 4. QUARTO: Atualizar status da notificação
            await self.atualizar_status_notificacao(
                interaction, 
                atendimento.id, 
                notificacao_sucesso
            )
            
        except Exception as e:
            logger.error(f'❌ Erro ao processar seleção do supervisor: {e}', exc_info=True)
            
            if atendimento_criado and atendimento_id:
                # Se atendimento foi criado, informar sucesso mas com problema na notificação
                try:
                    await interaction.response.edit_message(
                        content=f"✅ **Atendimento criado com sucesso!**\n\n"
                                f"**Agente:** {self.agente.nome}\n"
                                f"**Supervisor selecionado:** {self.supervisor.nome}\n"
                                f"**ID do atendimento:** #{atendimento_id}\n\n"
                                f"⚠️ Houve um problema na notificação, mas seu atendimento está registrado.\n"
                                f"Entre em contato com o administrador informando o ID: #{atendimento_id}",
                        view=None
                    )
                except:
                    # Se não conseguir editar, tentar responder
                    try:
                        await interaction.followup.send(
                            content=f"✅ Atendimento #{atendimento_id} criado com sucesso!\n"
                                    f"⚠️ Houve problema na notificação. Contate o administrador.",
                            ephemeral=True
                        )
                    except:
                        logger.error("Não foi possível notificar o usuário sobre o problema")
            else:
                # Se atendimento não foi criado, enviar erro
                try:
                    await interaction.response.edit_message(
                        content="❌ **Erro ao criar atendimento.**\n\n"
                                "Tente novamente em alguns instantes ou entre em contato com o administrador.",
                        view=None
                    )
                except:
                    try:
                        await interaction.followup.send(
                            content="❌ Erro ao criar atendimento. Tente novamente.",
                            ephemeral=True
                        )
                    except:
                        logger.error("Não foi possível notificar o usuário sobre o erro")
        finally:
            session.close()

    async def tentar_notificar_supervisor(self, supervisor, nome_agente, conteudo, nome_servidor, interaction):
        """
        Tenta notificar supervisor via Discord DM
        Retorna True se sucesso, False se falha
        """
        try:
            # Verificar se supervisor tem discord_id
            if not supervisor.discord_id:
                logger.warning(f'⚠️ Supervisor {supervisor.nome} não possui discord_id configurado')
                return False

            # Tentar buscar usuário no Discord
            user_supervisor = await interaction.client.fetch_user(int(supervisor.discord_id))
            
            # Tentar enviar DM
            await user_supervisor.send(
                f"🚨 **Novo atendimento recebido**\n\n"
                f"**Servidor:** {nome_servidor}\n"
                f"**Agente:** {nome_agente}\n"
                f"**Conteúdo:** {conteudo}\n\n"
                "Por favor, entre em contato com o agente o mais breve possível."
            )
            
            logger.info(f'✅ Notificação enviada com sucesso ao supervisor {supervisor.nome}')
            return True
            
        except discord.NotFound:
            logger.error(f'❌ Usuário do supervisor {supervisor.nome} não encontrado no Discord (ID: {supervisor.discord_id})')
            return False
        except discord.Forbidden:
            logger.warning(f'⚠️ Supervisor {supervisor.nome} não permite receber DMs')
            return False
        except ValueError:
            logger.error(f'❌ Discord ID inválido para supervisor {supervisor.nome}: {supervisor.discord_id}')
            return False
        except Exception as e:
            logger.error(f'❌ Erro inesperado ao notificar supervisor {supervisor.nome}: {e}')
            return False

    async def atualizar_status_notificacao(self, interaction, atendimento_id, sucesso):
        """
        Atualiza a mensagem com o status final da notificação
        """
        try:
            if sucesso:
                mensagem_final = (
                    f"✅ **Atendimento criado com sucesso!**\n\n"
                    f"**Agente:** {self.agente.nome}\n"
                    f"**Supervisor selecionado:** {self.supervisor.nome}\n"
                    f"**ID do atendimento:** #{atendimento_id}\n\n"
                    f"🔔 **Supervisor notificado com sucesso!**\n"
                    f"O supervisor {self.supervisor.nome} entrará em contato em breve."
                )
            else:
                mensagem_final = (
                    f"✅ **Atendimento criado com sucesso!**\n\n"
                    f"**Agente:** {self.agente.nome}\n"
                    f"**Supervisor selecionado:** {self.supervisor.nome}\n"
                    f"**ID do atendimento:** #{atendimento_id}\n\n"
                    f"⚠️ **Supervisor será notificado por outros meios.**\n"
                    f"Seu atendimento está registrado e será processado normalmente."
                )
            
            await interaction.edit_original_response(content=mensagem_final)
            
        except Exception as e:
            logger.error(f'❌ Erro ao atualizar status da notificação: {e}')
            # Se não conseguir atualizar, pelo menos logar o resultado
            status = "com sucesso" if sucesso else "falhou"
            logger.info(f'📊 Notificação do supervisor {self.supervisor.nome} {status} para atendimento #{atendimento_id}')

class MeuBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        with open('bot_status.txt', 'w') as f:
            f.write(f"ONLINE:{datetime.now().isoformat()}")
        logger.info(f'🤖 Bot conectado como {self.user}')
        logger.info(f'📊 Bot está em {len(self.guilds)} servidores')
        logger.info(f'🌐 Servidores: {[f"{guild.name} (ID: {guild.id})" for guild in self.guilds]}')

        try:
            session = Session()
            agentes_count = session.query(Agente).count()
            supervisores_count = session.query(User).filter_by(tipo='supervisor').count()
            session.close()
            logger.info(f'🗄️ Conexão com BD AWS RDS OK. {agentes_count} agentes e {supervisores_count} supervisores cadastrados.')
        except Exception as e:
            logger.error(f'❌ Erro ao conectar com BD AWS RDS: {e}')

    async def on_message(self, message):
        try:
            channel_info = f"#{message.channel.name}" if hasattr(message.channel, 'name') else "DM"
            server_info = f" no servidor {message.guild.name} (ID: {message.guild.id})" if message.guild else " em DM"
            logger.info(f"💬 Mensagem de {message.author} ({message.author.id}){server_info} em {channel_info}: {message.content}")

            if message.author == self.user or message.author.bot:
                return

            if KEYWORD.lower() not in message.content.lower():
                logger.debug(f"🔍 Palavra-chave '{KEYWORD}' não encontrada na mensagem")
                return

            logger.info(f"🎯 Palavra-chave detectada! Processando mensagem de {message.author}")

            session = Session()
            try:
                discord_id = str(message.author.id)
                server_id = str(message.guild.id) if message.guild else None

                logger.info(f"🔍 Buscando agente com discord_id: {discord_id}")

                agente = session.query(Agente).filter_by(discord_id=discord_id).first()
                if not agente:
                    logger.warning(f'⚠️ Agente com discord_id {discord_id} não encontrado no banco.')
                    await self.enviar_erro_agente_nao_cadastrado(message.author)
                    return

                logger.info(f"👤 Agente encontrado: {agente.nome}")

                # Busca TODOS os supervisores ativos
                supervisores = session.query(User).filter(User.tipo.in_(['supervisor', 'coordenadora'])).all()
                
                if not supervisores:
                    logger.warning('⚠️ Nenhum supervisor encontrado no sistema.')
                    await self.enviar_erro_sem_supervisores(message.author)
                    return

                # Se há apenas um supervisor, cria automaticamente
                if len(supervisores) == 1:
                    supervisor = supervisores[0]
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
                    
                    logger.info(f'✅ Atendimento automático criado (ID: {atendimento.id}) para único supervisor')
                    
                    await self.enviar_confirmacao_agente(message.author, agente.nome, supervisor.nome, atendimento.id)
                    await self.enviar_notificacao_supervisor_segura(supervisor, agente.nome, message.content, message.guild.name if message.guild else "DM")
                    return

                # Se há múltiplos supervisores, oferece escolha
                embed = discord.Embed(
                    title="🎯 Selecione o Supervisor",
                    description=f"Olá **{agente.nome}**!\n\nPara qual supervisor você gostaria de direcionar seu atendimento?",
                    color=0x003366
                )
                
                # Adiciona informações dos supervisores no embed
                supervisor_info = ""
                for sup in supervisores:
                    equipes_count = len(sup.equipes) if hasattr(sup, 'equipes') else 0
                    supervisor_info += f"**{sup.nome}** - {equipes_count} equipe(s)\n"
                
                embed.add_field(name="Supervisores Disponíveis:", value=supervisor_info, inline=False)
                embed.add_field(name="Seu problema:", value=message.content[:100] + "..." if len(message.content) > 100 else message.content, inline=False)
                
                view = SupervisorSelectView(supervisores, agente, message.content, server_id)
                
                await message.author.send(embed=embed, view=view)
                
                # Confirma que recebeu a solicitação
                await message.add_reaction("✅")

            except Exception as e:
                logger.error(f'❌ Erro ao processar atendimento: {e}', exc_info=True)
                session.rollback()
                await self.enviar_erro_generico(message.author)
            finally:
                session.close()

        except Exception as e:
            logger.error(f'💥 Erro crítico no on_message: {e}', exc_info=True)

    async def enviar_confirmacao_agente(self, user, nome_agente, nome_supervisor, atendimento_id):
        try:
            await user.send(
                f"✅ **Atendimento criado com sucesso!**\n\n"
                f"**Agente:** {nome_agente}\n"
                f"**Supervisor responsável:** {nome_supervisor}\n"
                f"**ID do atendimento:** #{atendimento_id}\n\n"
                f"Em breve o supervisor entrará em contato com você por DM."
            )
            logger.info(f'✅ Confirmação enviada para {nome_agente}')
        except discord.Forbidden:
            logger.warning(f'⚠️ Usuário {nome_agente} não permite DMs')
        except Exception as e:
            logger.error(f'❌ Erro ao enviar DM para {nome_agente}: {e}')

    async def enviar_notificacao_supervisor_segura(self, supervisor, nome_agente, conteudo, nome_servidor):
        """
        Versão segura da notificação que não quebra o fluxo principal
        """
        try:
            if not supervisor.discord_id:
                logger.warning(f'⚠️ Supervisor {supervisor.nome} não possui discord_id')
                return False

            user_supervisor = await self.fetch_user(int(supervisor.discord_id))
            await user_supervisor.send(
                f"🚨 **Novo atendimento recebido**\n\n"
                f"**Servidor:** {nome_servidor}\n"
                f"**Agente:** {nome_agente}\n"
                f"**Conteúdo:** {conteudo}\n\n"
                "Por favor, entre em contato com o agente o mais breve possível."
            )
            logger.info(f'✅ Notificação enviada ao supervisor {supervisor.nome}')
            return True
        except discord.NotFound:
            logger.error(f'❌ Usuário do supervisor {supervisor.nome} não encontrado (ID: {supervisor.discord_id})')
            return False
        except discord.Forbidden:
            logger.warning(f'⚠️ Supervisor {supervisor.nome} não permite DMs')
            return False
        except Exception as e:
            logger.error(f'❌ Erro ao notificar supervisor {supervisor.nome}: {e}')
            return False

    async def enviar_erro_agente_nao_cadastrado(self, user):
        try:
            await user.send(
                "❌ **Erro:** Você não está cadastrado no sistema.\n"
                "Entre em contato com o administrador para realizar o cadastro."
            )
        except Exception:
            logger.error(f'❌ Não foi possível enviar mensagem de erro para {user}')

    async def enviar_erro_sem_supervisores(self, user):
        try:
            await user.send(
                "❌ **Erro:** Nenhum supervisor disponível no momento.\n"
                "Entre em contato com o administrador."
            )
        except Exception:
            logger.error(f'❌ Não foi possível enviar mensagem de erro para {user}')

    async def enviar_erro_generico(self, user):
        try:
            await user.send(
                "❌ **Erro interno:** Não foi possível processar sua solicitação.\n"
                "Tente novamente em alguns minutos ou entre em contato com o administrador."
            )
        except Exception:
            logger.error(f'❌ Não foi possível enviar mensagem de erro genérico para {user}')

    async def on_disconnect(self):
        if os.path.exists('bot_status.txt'):
            os.remove('bot_status.txt')
        logger.warning('🔌 Bot desconectado do Discord')

    async def on_resumed(self):
        logger.info('🔄 Conexão com Discord restaurada')

# Instancia o bot com intents configurados
client = MeuBot(intents=intents)

def main():
    try:
        logger.info('🚀 Iniciando bot standalone...')
        client.run(TOKEN)
    except discord.LoginFailure:
        logger.error('❌ Token inválido! Verifique o token do bot.')
    except Exception as e:
        logger.error(f'💥 Erro ao iniciar bot: {e}', exc_info=True)

if __name__ == '__main__':
    main()