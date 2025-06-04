from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models.models import db, User, Equipe, Agente, Atendimento, agente_equipe
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict
import pytz
from datetime import datetime, timedelta
from collections import defaultdict


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

br_tz = pytz.timezone('America/Sao_Paulo')

from flask import redirect, url_for, flash
from flask_login import LoginManager


@login_manager.unauthorized_handler
def unauthorized_callback():
    flash('Por favor, faça login para acessar esta página.', 'danger')
    return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='admin@admin.com').first():
        admin = User(
            email='admin@admin.com',
            nome='Admin',
            senha=generate_password_hash('admin123'),
            tipo='admin'
        )
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.senha, senha):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login inválido. Verifique email e senha.', 'danger')
    return render_template('login.html')





@app.route('/dashboard')
@login_required
def dashboard():
    data_inicio_str = request.args.get('data_inicio', '')
    data_fim_str = request.args.get('data_fim', '')

    data_inicio = None
    data_fim = None

    try:
        if data_inicio_str:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
        if data_fim_str:
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        flash('Formato de data inválido.', 'danger')
        return redirect(url_for('dashboard'))

    if current_user.tipo == 'admin':
        supervisores = User.query.filter_by(tipo='supervisor').all()
    else:
        supervisores = [current_user]

    data = []
    total_atendimentos = 0
    total_agentes = 0
    todos_agentes = []

    for sup in supervisores:
        query = Atendimento.query.filter_by(supervisor_id=sup.id)
        if data_inicio:
            query = query.filter(Atendimento.data_hora >= data_inicio)
        if data_fim:
            query = query.filter(Atendimento.data_hora <= data_fim)

        atendimentos = query.order_by(Atendimento.data_hora.desc()).all()

        # Ajusta timezone para cada atendimento
        for atendimento in atendimentos:
            if atendimento.data_hora.tzinfo is None:
                atendimento.data_hora = atendimento.data_hora.replace(tzinfo=pytz.utc)
            atendimento.data_hora = atendimento.data_hora.astimezone(br_tz)

        total_chamados = len(atendimentos)
        total_atendimentos += total_chamados

        contador_agentes = defaultdict(list)
        for a in atendimentos:
            contador_agentes[a.agente_rel.nome].append(a)

        num_agentes_supervisor = len(contador_agentes)
        total_agentes += num_agentes_supervisor

        if contador_agentes:
            agente_top, chamados_top = max(contador_agentes.items(), key=lambda x: len(x[1]))
            qtd_top = len(chamados_top)
        else:
            agente_top, chamados_top, qtd_top = None, [], 0

        agentes_data = []
        for agente_nome, chamados in contador_agentes.items():
            qtd_chamados = len(chamados)
            agentes_data.append({
                'nome': agente_nome,
                'qtd_chamados': qtd_chamados,
                'chamados': chamados
            })
            todos_agentes.append({
                'nome': agente_nome,
                'qtd_chamados': qtd_chamados,
                'supervisor_nome': sup.nome
            })

        agentes_data.sort(key=lambda x: x['qtd_chamados'], reverse=True)

        data.append({
            'supervisor': sup,
            'total_chamados': total_chamados,
            'agente_top': agente_top,
            'qtd_top': qtd_top,
            'agentes': agentes_data,
            'num_agentes': num_agentes_supervisor
        })

    data.sort(key=lambda x: x['total_chamados'], reverse=True)
    todos_agentes.sort(key=lambda x: x['qtd_chamados'], reverse=True)
    top_5_agentes = todos_agentes[:5]

    total_supervisores = len(supervisores)
    media_por_agente = round(total_atendimentos / total_agentes, 1) if total_agentes > 0 else 0

    return render_template('dashboard.html',
                           data=data,
                           total_supervisores=total_supervisores,
                           total_agentes=total_agentes,
                           total_atendimentos=total_atendimentos,
                           media_por_agente=media_por_agente,
                           top_5_agentes=top_5_agentes,
                           data_inicio=data_inicio_str,
                           data_fim=data_fim_str)





@app.route('/atendimentos')
@login_required
def atendimentos():
    if current_user.tipo == 'admin':
        atendimentos = Atendimento.query.order_by(Atendimento.data_hora.desc()).all()
    else:
        atendimentos = Atendimento.query.filter_by(supervisor_id=current_user.id).order_by(Atendimento.data_hora.desc()).all()

    # Ajusta timezone para cada atendimento
    for atendimento in atendimentos:
        if atendimento.data_hora.tzinfo is None:
            atendimento.data_hora = atendimento.data_hora.replace(tzinfo=pytz.utc)
        atendimento.data_hora = atendimento.data_hora.astimezone(br_tz)

    return render_template('atendimento_list.html', atendimentos=atendimentos)


from datetime import date

@app.route('/atendimentos/novo', methods=['GET', 'POST'])
@login_required
def novo_atendimento():
    # CORREÇÃO: Busca agentes corretamente usando consulta SQL direta
    if current_user.tipo == 'admin':
        agentes = Agente.query.filter_by(ativo=True).all()
    else:
        # Busca agentes que estão em equipes do supervisor atual
        agentes = db.session.query(Agente).join(
            agente_equipe, Agente.id == agente_equipe.c.agente_id
        ).join(
            Equipe, agente_equipe.c.equipe_id == Equipe.id
        ).filter(
            Equipe.supervisor_id == current_user.id,
            Agente.ativo == True
        ).distinct().all()

    if request.method == 'POST':
        agente_id = request.form['agente_id']
        conteudo = request.form['conteudo']
        classificacao = request.form.get('classificacao')

        agente = Agente.query.get(int(agente_id))
        if not agente:
            flash('Agente inválido.', 'danger')
            return redirect(url_for('novo_atendimento'))

        # Validação para agente desligado
        hoje = date.today()
        if not agente.ativo or (agente.data_desligamento and agente.data_desligamento <= hoje):
            flash('Não é possível criar atendimento para agente desligado.', 'danger')
            return redirect(url_for('novo_atendimento'))

        # O supervisor_id do atendimento é quem está criando
        atendimento = Atendimento(
            agente_id=agente.id,
            supervisor_id=current_user.id,  # Quem está criando o atendimento
            conteudo=conteudo,
            classificacao=classificacao,
            status='pendente',
            data_hora=datetime.utcnow()
        )
        db.session.add(atendimento)
        db.session.commit()
        flash('Atendimento criado com sucesso!', 'success')
        return redirect(url_for('atendimentos'))

    return render_template('atendimento_form.html', agentes=agentes)




@app.route('/atendimento/editar/<int:atendimento_id>', methods=['GET', 'POST'])
@login_required
def editar_atendimento(atendimento_id):
    atendimento = Atendimento.query.get_or_404(atendimento_id)

    if current_user.tipo != 'admin' and atendimento.supervisor_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('atendimentos'))

    if request.method == 'POST':
        agente_id = request.form['agente_id']
        conteudo = request.form['conteudo']
        classificacao = request.form['classificacao']

        agente_obj = Agente.query.get(int(agente_id))
        if not agente_obj:
            flash('Agente inválido.', 'danger')
            return redirect(url_for('editar_atendimento', atendimento_id=atendimento_id))

        atendimento.agente_id = agente_id
        atendimento.conteudo = conteudo
        atendimento.classificacao = classificacao
        atendimento.status = 'classificado' if classificacao else 'pendente'

        db.session.commit()
        flash('Atendimento atualizado com sucesso!', 'success')
        return redirect(url_for('atendimentos'))

    # CORREÇÃO: Lista agentes disponíveis para edição usando consulta SQL direta
    if current_user.tipo == 'admin':
        agentes = Agente.query.all()
    else:
        # Busca agentes que estão em equipes do supervisor atual
        agentes = db.session.query(Agente).join(
            agente_equipe, Agente.id == agente_equipe.c.agente_id
        ).join(
            Equipe, agente_equipe.c.equipe_id == Equipe.id
        ).filter(
            Equipe.supervisor_id == current_user.id
        ).distinct().all()

    return render_template('atendimento_edit.html', atendimento=atendimento, agentes=agentes)

@app.route('/atendimento/excluir/<int:atendimento_id>', methods=['GET'])
@login_required
def excluir_atendimento(atendimento_id):
    atendimento = Atendimento.query.get_or_404(atendimento_id)

    if current_user.tipo != 'admin' and atendimento.supervisor_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('atendimentos'))

    db.session.delete(atendimento)
    db.session.commit()
    flash('Atendimento excluído com sucesso.', 'success')
    return redirect(url_for('atendimentos'))


@app.route('/cadastros/supervisores', methods=['GET', 'POST'])
@login_required
def supervisores():
    if current_user.tipo != 'admin':
        flash('Acesso negado', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        discord_id = request.form.get('discord_id')
        servidor_discord_id = request.form.get('servidor_discord_id')
        senha = request.form['senha']
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'danger')
        else:
            # Processa servidor_discord_id - pode ser único ou lista separada por vírgula
            if servidor_discord_id:
                # Remove espaços e divide por vírgula se houver múltiplos
                servidores = [s.strip() for s in servidor_discord_id.split(',') if s.strip()]
                if len(servidores) > 1:
                    # Se múltiplos servidores, salva como JSON array
                    import json
                    servidor_discord_id = json.dumps(servidores)
                else:
                    # Se apenas um servidor, salva como string simples
                    servidor_discord_id = servidores[0] if servidores else None
            
            novo = User(
                nome=nome,
                email=email,
                discord_id=discord_id,
                servidor_discord_id=servidor_discord_id,
                senha=generate_password_hash(senha),
                tipo='supervisor'
            )
            db.session.add(novo)
            db.session.commit()
            flash('Supervisor criado com sucesso!', 'success')
            return redirect(url_for('supervisores'))

    supervisores = User.query.filter_by(tipo='supervisor').all()
    return render_template('supervisores.html', supervisores=supervisores)

@app.route('/cadastros/supervisor/editar/<int:supervisor_id>', methods=['GET', 'POST'])
@login_required
def editar_supervisor(supervisor_id):
    if current_user.tipo != 'admin':
        flash('Acesso negado', 'danger')
        return redirect(url_for('dashboard'))
    
    supervisor = User.query.filter_by(id=supervisor_id, tipo='supervisor').first_or_404()

    if request.method == 'POST':
        supervisor.nome = request.form['nome']
        supervisor.email = request.form['email']
        discord_id = request.form.get('discord_id')
        supervisor.discord_id = discord_id if discord_id else None
        
        # Processa servidor_discord_id
        servidor_discord_id = request.form.get('servidor_discord_id')
        if servidor_discord_id:
            # Remove espaços e divide por vírgula se houver múltiplos
            servidores = [s.strip() for s in servidor_discord_id.split(',') if s.strip()]
            if len(servidores) > 1:
                # Se múltiplos servidores, salva como JSON array
                import json
                supervisor.servidor_discord_id = json.dumps(servidores)
            else:
                # Se apenas um servidor, salva como string simples
                supervisor.servidor_discord_id = servidores[0] if servidores else None
        else:
            supervisor.servidor_discord_id = None

        senha = request.form.get('senha')
        if senha:
            supervisor.senha = generate_password_hash(senha)

        db.session.commit()
        flash('Supervisor atualizado com sucesso!', 'success')
        return redirect(url_for('supervisores'))

    return render_template('supervisor_edit.html', supervisor=supervisor)


from flask import request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user



@app.route('/cadastros/agentes', methods=['GET', 'POST'])
@login_required
def agentes():
    supervisores = User.query.filter_by(tipo='supervisor').all()
    
    # CORREÇÃO 1: Admin vê todas as equipes, supervisor vê todas também (para poder associar agentes)
    if current_user.tipo == 'admin':
        equipes = Equipe.query.all()
    else:
        # Supervisor vê todas as equipes para poder associar agentes
        equipes = Equipe.query.all()

    if request.method == 'POST':
        nome = request.form['nome']
        discord_id = request.form.get('discord_id')
        equipes_ids = request.form.getlist('equipes')

        # CORREÇÃO 2: Verifica se já existe agente com mesmo nome (não discord_id)
        existente_nome = Agente.query.filter_by(nome=nome).first()
        if existente_nome:
            flash(f'Já existe um agente com o nome "{nome}".', 'danger')
            return redirect(url_for('agentes'))

        # Verifica discord_id se fornecido
        if discord_id:
            existente_discord = Agente.query.filter_by(discord_id=discord_id).first()
            if existente_discord:
                flash('Este Discord ID já está cadastrado para outro agente.', 'danger')
                return redirect(url_for('agentes'))

        if not equipes_ids:
            flash('Selecione pelo menos uma equipe.', 'danger')
            return redirect(url_for('agentes'))

        # CORREÇÃO 3: Define supervisor_id baseado na primeira equipe OU usuário atual
        primeira_equipe = Equipe.query.filter(Equipe.id.in_(equipes_ids)).first()
        
        # Se o usuário atual é supervisor de uma das equipes selecionadas, ele vira o supervisor principal
        equipes_do_usuario = [eq for eq in Equipe.query.filter(Equipe.id.in_(equipes_ids)).all() 
                             if eq.supervisor_id == current_user.id]
        
        if equipes_do_usuario:
            supervisor_principal = current_user.id
        elif primeira_equipe:
            supervisor_principal = primeira_equipe.supervisor_id
        else:
            supervisor_principal = current_user.id

        novo_agente = Agente(
            nome=nome,
            discord_id=discord_id if discord_id else None,
            ativo=True,
            supervisor_id=supervisor_principal
        )

        # Associa às equipes selecionadas
        selecionadas = Equipe.query.filter(Equipe.id.in_(equipes_ids)).all()
        novo_agente.equipes = selecionadas

        db.session.add(novo_agente)
        db.session.commit()
        flash('Agente criado com sucesso!', 'success')
        return redirect(url_for('agentes'))

    # CORREÇÃO PRINCIPAL: Listagem correta de agentes usando consulta SQL direta
    if current_user.tipo == 'admin':
        agentes = Agente.query.all()
    else:
        # Busca agentes que estão em equipes do supervisor atual
        # Usando uma consulta que une as tabelas diretamente
        agentes = db.session.query(Agente).join(
            agente_equipe, Agente.id == agente_equipe.c.agente_id
        ).join(
            Equipe, agente_equipe.c.equipe_id == Equipe.id
        ).filter(
            Equipe.supervisor_id == current_user.id
        ).distinct().all()

    return render_template('agentes.html', agentes=agentes, supervisores=supervisores, equipes=equipes)





from datetime import datetime

@app.route('/cadastros/agente/editar/<int:agente_id>', methods=['GET', 'POST'])
@login_required
def editar_agente(agente_id):
    agente = Agente.query.get_or_404(agente_id)
    supervisores = User.query.filter_by(tipo='supervisor').all()
    
    # CORREÇÃO 5: Todos podem ver todas as equipes para edição
    equipes = Equipe.query.all()

    if request.method == 'POST':
        # Verifica se mudou o nome e se já existe outro com mesmo nome
        novo_nome = request.form['nome']
        if novo_nome != agente.nome:
            existente = Agente.query.filter_by(nome=novo_nome).first()
            if existente:
                flash(f'Já existe um agente com o nome "{novo_nome}".', 'danger')
                return redirect(url_for('editar_agente', agente_id=agente_id))

        agente.nome = novo_nome
        
        novo_discord = request.form.get('discord_id')
        if novo_discord != agente.discord_id:
            if novo_discord:
                existente_discord = Agente.query.filter_by(discord_id=novo_discord).first()
                if existente_discord:
                    flash('Este Discord ID já está cadastrado para outro agente.', 'danger')
                    return redirect(url_for('editar_agente', agente_id=agente_id))
        
        agente.discord_id = novo_discord if novo_discord else None

        equipes_ids = request.form.getlist('equipes')
        if equipes_ids:
            agente.equipes = Equipe.query.filter(Equipe.id.in_(equipes_ids)).all()
        else:
            agente.equipes = []

        db.session.commit()
        flash('Agente atualizado com sucesso!', 'success')
        return redirect(url_for('agentes'))

    return render_template('agente_edit.html', agente=agente, supervisores=supervisores, equipes=equipes)

@app.route('/cadastros/equipes', methods=['GET', 'POST'])
@login_required
def equipes():
    if current_user.tipo != 'admin' and current_user.tipo != 'supervisor':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))

    # Lista de supervisores para o admin escolher
    supervisores = User.query.filter_by(tipo='supervisor').all() if current_user.tipo == 'admin' else None

    if request.method == 'POST':
        nome = request.form['nome']
        
        # CORREÇÃO: Admin pode escolher o supervisor, supervisor cria para si
        if current_user.tipo == 'admin':
            supervisor_id = request.form.get('supervisor_id')
            if not supervisor_id:
                flash('Selecione um supervisor para a equipe.', 'danger')
                return redirect(url_for('equipes'))
            
            # Valida se o supervisor existe
            supervisor = User.query.filter_by(id=supervisor_id, tipo='supervisor').first()
            if not supervisor:
                flash('Supervisor inválido.', 'danger')
                return redirect(url_for('equipes'))
        else:
            # Supervisor cria equipe para si mesmo
            supervisor_id = current_user.id

        # Verifica se já existe equipe com o mesmo nome
        equipe_existente = Equipe.query.filter_by(nome=nome).first()
        if equipe_existente:
            flash(f'Já existe uma equipe com o nome "{nome}".', 'danger')
            return redirect(url_for('equipes'))

        nova_equipe = Equipe(nome=nome, supervisor_id=supervisor_id)
        db.session.add(nova_equipe)
        db.session.commit()
        
        supervisor_nome = User.query.get(supervisor_id).nome
        flash(f'Equipe "{nome}" criada com sucesso para o supervisor {supervisor_nome}!', 'success')
        return redirect(url_for('equipes'))

    if current_user.tipo == 'admin':
        equipes = Equipe.query.all()
    else:
        equipes = Equipe.query.filter_by(supervisor_id=current_user.id).all()

    return render_template('equipes.html', equipes=equipes, supervisores=supervisores)

@app.route('/cadastros/equipe/editar/<int:equipe_id>', methods=['GET', 'POST'])
@login_required
def editar_equipe(equipe_id):
    if current_user.tipo != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))
    
    equipe = Equipe.query.get_or_404(equipe_id)
    supervisores = User.query.filter_by(tipo='supervisor').all()

    if request.method == 'POST':
        nome = request.form['nome']
        supervisor_id = request.form['supervisor_id']
        
        # Verifica se já existe outra equipe com o mesmo nome
        equipe_existente = Equipe.query.filter(
            Equipe.nome == nome, 
            Equipe.id != equipe_id
        ).first()
        
        if equipe_existente:
            flash(f'Já existe uma equipe com o nome "{nome}".', 'danger')
            return redirect(url_for('editar_equipe', equipe_id=equipe_id))

        # Valida se o supervisor existe
        supervisor = User.query.filter_by(id=supervisor_id, tipo='supervisor').first()
        if not supervisor:
            flash('Supervisor inválido.', 'danger')
            return redirect(url_for('editar_equipe', equipe_id=equipe_id))

        # Atualiza os dados
        equipe.nome = nome
        equipe.supervisor_id = supervisor_id
        
        db.session.commit()
        flash(f'Equipe "{nome}" atualizada com sucesso!', 'success')
        return redirect(url_for('equipes'))

    return render_template('equipe_edit.html', equipe=equipe, supervisores=supervisores)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'success')
    return redirect(url_for('login'))


import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[logging.FileHandler("app_debug.log"),
                              logging.StreamHandler()])

logger = logging.getLogger(__name__)

logger.debug("Aplicação Flask iniciada.")



if __name__ == '__main__':
    app.run(debug=True)

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.debug = True
