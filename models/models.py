from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

# Tabela de associação para o relacionamento many-to-many entre Agente e Equipe
agente_equipe = db.Table('agente_equipe',
    db.Column('agente_id', db.Integer, db.ForeignKey('agentes.id'), primary_key=True),
    db.Column('equipe_id', db.Integer, db.ForeignKey('equipes.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'admin' ou 'supervisor'
    discord_id = db.Column(db.String(50), unique=True, nullable=True)
    servidor_discord_id = db.Column(db.Text, nullable=True)  # Novo campo para IDs dos servidores
    
    def atende_servidor(self, servidor_id):
        """Verifica se este supervisor atende o servidor especificado"""
        if not self.servidor_discord_id:
            return False
        
        servidor_id_str = str(servidor_id)
        
        # Se é um JSON array (múltiplos servidores)
        if self.servidor_discord_id.startswith('['):
            try:
                servidores = json.loads(self.servidor_discord_id)
                return servidor_id_str in servidores
            except json.JSONDecodeError:
                return False
        
        # Se é um ID único
        return self.servidor_discord_id == servidor_id_str

class Equipe(db.Model):
    __tablename__ = 'equipes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    supervisor = db.relationship('User', backref='equipes')
    # Relacionamento many-to-many com Agente
    agentes = db.relationship('Agente', secondary=agente_equipe, back_populates='equipes')


class Agente(db.Model):
    __tablename__ = 'agentes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Supervisor principal
    discord_id = db.Column(db.String(50), unique=True, nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_desligamento = db.Column(db.Date, nullable=True)
    
    supervisor = db.relationship('User', backref='agentes')
    # Relacionamento many-to-many com Equipe
    equipes = db.relationship('Equipe', secondary=agente_equipe, back_populates='agentes')
    atendimentos = db.relationship('Atendimento', back_populates='agente_rel')


class Atendimento(db.Model):
    __tablename__ = 'atendimentos'
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    agente_id = db.Column(db.Integer, db.ForeignKey('agentes.id'), nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Supervisor que atendeu
    conteudo = db.Column(db.Text, nullable=False)
    classificacao = db.Column(db.String(20), nullable=True)  # básico, médio, complexo ou None
    status = db.Column(db.String(20), default='pendente')  # pendente, classificado
    servidor_discord_id = db.Column(db.String(50), nullable=True)  # Servidor onde foi criado o atendimento

    agente_rel = db.relationship('Agente', back_populates='atendimentos')
    supervisor = db.relationship('User')