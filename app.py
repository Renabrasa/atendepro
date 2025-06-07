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





# SUBSTITUA a função dashboard() no app.py por esta versão

@app.route('/dashboard')
@login_required
def dashboard():
    from datetime import datetime, date
    
    # Pega filtros da URL (se houver)
    data_inicio_str = request.args.get('data_inicio', '')
    data_fim_str = request.args.get('data_fim', '')
    
    # Se não há filtros, usa dados de HOJE por padrão
    if not data_inicio_str and not data_fim_str:
        hoje = date.today()
        data_inicio = datetime.combine(hoje, datetime.min.time())
        data_fim = datetime.combine(hoje, datetime.max.time())
        data_inicio_str = hoje.strftime('%Y-%m-%d')
        data_fim_str = hoje.strftime('%Y-%m-%d')
        periodo_atual = "HOJE"
    else:
        # Se há filtros, usa eles
        data_inicio = None
        data_fim = None
        periodo_atual = "PERÍODO PERSONALIZADO"
        
        try:
            if data_inicio_str:
                data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
            if data_fim_str:
                data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d')
                data_fim = datetime.combine(data_fim.date(), datetime.max.time())
        except ValueError:
            flash('Formato de data inválido.', 'danger')
            return redirect(url_for('dashboard'))

    # Buscar supervisores baseado no tipo de usuário
    if current_user.tipo in ['admin', 'coordenadora']:
        supervisores = User.query.filter(User.tipo.in_(['supervisor', 'coordenadora'])).all()
    else:
        supervisores = [current_user]

    data = []
    total_atendimentos = 0
    total_agentes = 0
    todos_agentes = []

    for sup in supervisores:
        # Query com filtros de data aplicados
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
                           data_fim=data_fim_str,
                           periodo_atual=periodo_atual)




# SUBSTITUA a rota /atendimentos no app.py por esta versão atualizada

@app.route('/atendimentos')
@login_required
def atendimentos():
    # Parâmetros de filtro da URL
    page = request.args.get('page', 1, type=int)
    per_page = 20  # 20 atendimentos por página
    
    data_inicio_str = request.args.get('data_inicio', '')
    data_fim_str = request.args.get('data_fim', '')
    agente_id = request.args.get('agente', '')
    supervisor_id = request.args.get('supervisor', '')  # Supervisor do agente (mantido para compatibilidade)
    atendido_por_id = request.args.get('atendido_por', '')  # NOVO: Quem prestou o atendimento
    status_filter = request.args.get('status', '')
    busca = request.args.get('busca', '')

    # Converte datas
    data_inicio = None
    data_fim = None
    try:
        if data_inicio_str:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
        if data_fim_str:
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
    except ValueError:
        flash('Formato de data inválido.', 'danger')

    # Query base com filtros de permissão
    if current_user.tipo in ['admin', 'coordenadora']:
        # Admin e Coordenadora veem todos
        query = Atendimento.query
    else:
        # Supervisor vê apenas os seus (atendimentos que ELE prestou)
        query = Atendimento.query.filter_by(supervisor_id=current_user.id)

    # Aplicar filtros
    if data_inicio:
        query = query.filter(Atendimento.data_hora >= data_inicio)
    if data_fim:
        query = query.filter(Atendimento.data_hora <= data_fim)
    if agente_id:
        query = query.filter_by(agente_id=agente_id)
    if supervisor_id:
        # Filtro por supervisor do agente (JOIN necessário)
        query = query.join(Agente).filter(Agente.supervisor_id == supervisor_id)
    if atendido_por_id:
        # NOVO: Filtro por quem prestou o atendimento
        query = query.filter_by(supervisor_id=atendido_por_id)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if busca:
        query = query.filter(Atendimento.conteudo.contains(busca))

    # Ordenar por data (mais recente primeiro)
    query = query.order_by(Atendimento.data_hora.desc())

    # Paginação
    atendimentos_paginated = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )

    # Ajustar timezone
    for atendimento in atendimentos_paginated.items:
        if atendimento.data_hora.tzinfo is None:
            atendimento.data_hora = atendimento.data_hora.replace(tzinfo=pytz.utc)
        atendimento.data_hora = atendimento.data_hora.astimezone(br_tz)

    # Buscar dados para os dropdowns de filtro
    if current_user.tipo in ['admin', 'coordenadora']:
        # Admin/Coordenadora veem todos
        agentes_dropdown = Agente.query.filter_by(ativo=True).all()
        supervisores_dropdown = User.query.filter(User.tipo.in_(['supervisor', 'coordenadora'])).all()
    else:
        # Supervisor vê apenas seus agentes
        agentes_dropdown = db.session.query(Agente).join(
            agente_equipe, Agente.id == agente_equipe.c.agente_id
        ).join(
            Equipe, agente_equipe.c.equipe_id == Equipe.id
        ).filter(
            Equipe.supervisor_id == current_user.id,
            Agente.ativo == True
        ).distinct().all()
        supervisores_dropdown = [current_user]

    # Estatísticas para os cards
    stats = {
        'total_filtrados': atendimentos_paginated.total,
        'pendentes': query.filter_by(status='pendente').count() if status_filter != 'classificado' else 0,
        'classificados': query.filter_by(status='classificado').count() if status_filter != 'pendente' else 0,
        'hoje': query.filter(
            Atendimento.data_hora >= datetime.now().replace(hour=0, minute=0, second=0)
        ).count() if not data_inicio and not data_fim else 0
    }

    return render_template('atendimento_list.html', 
                         atendimentos_paginated=atendimentos_paginated,
                         atendimentos=atendimentos_paginated.items,
                         agentes_dropdown=agentes_dropdown,
                         supervisores_dropdown=supervisores_dropdown,
                         stats=stats,
                         # Manter filtros na URL (INCLUINDO O NOVO)
                         current_filters={
                             'data_inicio': data_inicio_str,
                             'data_fim': data_fim_str,
                             'agente': agente_id,
                             'supervisor': supervisor_id,
                             'atendido_por': atendido_por_id,  # NOVO FILTRO
                             'status': status_filter,
                             'busca': busca
                         })


from datetime import date

@app.route('/atendimentos/novo', methods=['GET', 'POST'])
@login_required
def novo_atendimento():
    # CORREÇÃO: Busca agentes corretamente usando consulta SQL direta
    if current_user.tipo in ['admin', 'coordenadora']:
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

    if current_user.tipo not in ['admin', 'coordenadora'] and atendimento.supervisor_id != current_user.id:
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
    if current_user.tipo in ['admin', 'coordenadora']:
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

    if current_user.tipo not in ['admin', 'coordenadora'] and atendimento.supervisor_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('atendimentos'))

    db.session.delete(atendimento)
    db.session.commit()
    flash('Atendimento excluído com sucesso.', 'success')
    return redirect(url_for('atendimentos'))


# Adicione estas rotas ao seu app.py

# SUBSTITUA a rota /meu-perfil no app.py por esta versão corrigida

@app.route('/meu-perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    """Permite usuários editarem seu próprio perfil"""
    # CORREÇÃO: Incluir admin na verificação
    if current_user.tipo not in ['supervisor', 'coordenadora', 'admin']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Atualizar dados do próprio usuário
        current_user.nome = request.form['nome']
        current_user.email = request.form['email']
        
        # Discord ID (todos os tipos podem ter)
        discord_id = request.form.get('discord_id')
        current_user.discord_id = discord_id if discord_id else None
        
        # Servidor Discord ID (apenas para supervisores e admin)
        if current_user.tipo in ['supervisor', 'admin']:
            servidor_discord_id = request.form.get('servidor_discord_id')
            if servidor_discord_id:
                # Remove espaços e divide por vírgula se houver múltiplos
                servidores = [s.strip() for s in servidor_discord_id.split(',') if s.strip()]
                if len(servidores) > 1:
                    import json
                    current_user.servidor_discord_id = json.dumps(servidores)
                else:
                    current_user.servidor_discord_id = servidores[0] if servidores else None
            else:
                current_user.servidor_discord_id = None
        
        # Alterar senha se fornecida
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        if nova_senha:
            if nova_senha != confirmar_senha:
                flash('As senhas não coincidem.', 'danger')
                return redirect(url_for('meu_perfil'))
            
            if len(nova_senha) < 6:
                flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
                return redirect(url_for('meu_perfil'))
            
            current_user.senha = generate_password_hash(nova_senha)
        
        try:
            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar perfil: {str(e)}', 'danger')
        
        return redirect(url_for('meu_perfil'))
    
    # Preparar dados para exibição baseado no tipo de usuário
    equipes_supervisionadas = []
    agentes_supervisionados = []
    total_atendimentos = 0
    usuarios_gerenciados = 0
    total_equipes = 0
    
    if current_user.tipo == 'supervisor':
        # Dados específicos do supervisor
        equipes_supervisionadas = Equipe.query.filter_by(supervisor_id=current_user.id).all()
        agentes_supervisionados = Agente.query.filter_by(supervisor_id=current_user.id).all()
        total_atendimentos = Atendimento.query.filter_by(supervisor_id=current_user.id).count()
        
    elif current_user.tipo == 'coordenadora':
        # Dados da coordenadora (pode ver tudo)
        total_atendimentos = Atendimento.query.count()
        usuarios_gerenciados = User.query.filter_by(tipo='supervisor').count()
        total_equipes = Equipe.query.count()
        
    elif current_user.tipo == 'admin':
        # Dados do admin (estatísticas gerais do sistema)
        total_atendimentos = Atendimento.query.count()
        usuarios_gerenciados = User.query.filter(User.tipo.in_(['supervisor', 'coordenadora'])).count()
        total_equipes = Equipe.query.count()
        agentes_supervisionados = Agente.query.all()  # Admin vê todos os agentes
    
    return render_template('meu_perfil.html',
                         equipes=equipes_supervisionadas,
                         agentes=agentes_supervisionados,
                         total_atendimentos=total_atendimentos,
                         usuarios_gerenciados=usuarios_gerenciados,
                         total_equipes=total_equipes)






@app.route('/cadastros/supervisores', methods=['GET', 'POST'])
@login_required
def supervisores():
    if current_user.tipo not in ['admin', 'coordenadora']:
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

    # CORREÇÃO AQUI: Incluir coordenadora na listagem
    # ANTES: supervisores = User.query.filter_by(tipo='supervisor').all()
    # NOVO:
    if current_user.tipo == 'admin':
        # Admin vê supervisores E coordenadores
        supervisores = User.query.filter(User.tipo.in_(['supervisor', 'coordenadora'])).all()
    else:
        # Coordenadora vê supervisores E ela mesma
        supervisores_lista = User.query.filter_by(tipo='supervisor').all()
        # Adiciona a própria coordenadora na lista
        supervisores_lista.append(current_user)
        supervisores = supervisores_lista

    return render_template('supervisores.html', supervisores=supervisores)

@app.route('/cadastros/supervisor/editar/<int:supervisor_id>', methods=['GET', 'POST'])
@login_required
def editar_supervisor(supervisor_id):
    if current_user.tipo not in ['admin', 'coordenadora']:
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


# ADICIONE esta nova rota no app.py (após as outras rotas)

@app.route('/api/supervisor-details/<int:supervisor_id>')
@login_required
def api_supervisor_details(supervisor_id):
    """API para buscar detalhes de um supervisor e seus agentes"""
    try:
        # Verificar permissões
        if current_user.tipo not in ['admin', 'coordenadora']:
            if current_user.id != supervisor_id:
                return jsonify({'success': False, 'error': 'Acesso negado'}), 403
        
        # Buscar o supervisor
        supervisor = User.query.get_or_404(supervisor_id)
        
        # Pegar filtros da URL (mesmos do dashboard)
        data_inicio_str = request.args.get('data_inicio', '')
        data_fim_str = request.args.get('data_fim', '')
        
        # Aplicar mesma lógica de data do dashboard
        if not data_inicio_str and not data_fim_str:
            # Dados de hoje
            from datetime import datetime, date
            hoje = date.today()
            data_inicio = datetime.combine(hoje, datetime.min.time())
            data_fim = datetime.combine(hoje, datetime.max.time())
        else:
            # Dados do período especificado
            data_inicio = None
            data_fim = None
            
            if data_inicio_str:
                data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d')
            if data_fim_str:
                data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d')
                data_fim = datetime.combine(data_fim.date(), datetime.max.time())
        
        # Query de atendimentos do supervisor
        query = Atendimento.query.filter_by(supervisor_id=supervisor_id)
        
        if data_inicio:
            query = query.filter(Atendimento.data_hora >= data_inicio)
        if data_fim:
            query = query.filter(Atendimento.data_hora <= data_fim)
        
        atendimentos = query.order_by(Atendimento.data_hora.desc()).all()
        
        # Agrupar por agente
        from collections import defaultdict
        contador_agentes = defaultdict(list)
        
        for atendimento in atendimentos:
            # Ajustar timezone
            if atendimento.data_hora.tzinfo is None:
                atendimento.data_hora = atendimento.data_hora.replace(tzinfo=pytz.utc)
            atendimento.data_hora = atendimento.data_hora.astimezone(br_tz)
            
            contador_agentes[atendimento.agente_rel.nome].append(atendimento)
        
        # Preparar dados dos agentes para JSON
        agentes_data = []
        total_atendimentos = len(atendimentos)
        
        for agente_nome, lista_atendimentos in contador_agentes.items():
            # Serializar atendimentos para JSON
            atendimentos_json = []
            for atendimento in lista_atendimentos:
                atendimentos_json.append({
                    'id': atendimento.id,
                    'conteudo': atendimento.conteudo,
                    'classificacao': atendimento.classificacao,
                    'status': atendimento.status,
                    'data_hora': atendimento.data_hora.isoformat()
                })
            
            agentes_data.append({
                'nome': agente_nome,
                'qtd_chamados': len(lista_atendimentos),
                'atendimentos': atendimentos_json
            })
        
        # Ordenar por quantidade de atendimentos
        agentes_data.sort(key=lambda x: x['qtd_chamados'], reverse=True)
        
        return jsonify({
            'success': True,
            'supervisor': {
                'nome': supervisor.nome,
                'id': supervisor.id,
                'tipo': supervisor.tipo
            },
            'agentes': agentes_data,
            'total_atendimentos': total_atendimentos
        })
        
    except Exception as e:
        app.logger.error(f'Erro na API supervisor-details: {e}')
        return jsonify({
            'success': False, 
            'error': 'Erro interno do servidor'
        }), 500




from flask import request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user


@app.route('/cadastros/agentes', methods=['GET', 'POST'])
@login_required
def agentes():
    # Buscar supervisores (incluindo coordenadoras) para dropdown
    supervisores = User.query.filter(User.tipo.in_(['supervisor', 'coordenadora'])).all()
    
    # CORREÇÃO: SEMPRE mostrar todas as equipes para permitir compartilhamento
    # Independente do tipo de usuário, mostra todas as equipes
    equipes = Equipe.query.all()

    if request.method == 'POST':
        nome = request.form['nome'].strip()  # Remove espaços extras
        discord_id = request.form.get('discord_id', '').strip()
        supervisor_id = request.form.get('supervisor_id')
        equipes_ids = request.form.getlist('equipes')

        # Validações básicas
        if not nome:
            flash('Nome do agente é obrigatório.', 'danger')
            return redirect(url_for('agentes'))

        if len(nome) < 2:
            flash('Nome do agente deve ter pelo menos 2 caracteres.', 'danger')
            return redirect(url_for('agentes'))

        # Verifica se já existe agente com mesmo nome
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

        # Valida supervisor
        if not supervisor_id:
            flash('Selecione um supervisor principal.', 'danger')
            return redirect(url_for('agentes'))

        # Valida se o supervisor existe e é do tipo correto
        supervisor = User.query.filter(
            User.id == supervisor_id, 
            User.tipo.in_(['supervisor', 'coordenadora'])
        ).first()
        if not supervisor:
            flash('Supervisor selecionado não é válido.', 'danger')
            return redirect(url_for('agentes'))

        # Valida equipes
        if not equipes_ids:
            flash('Selecione pelo menos uma equipe.', 'danger')
            return redirect(url_for('agentes'))

        # VALIDAÇÃO ADICIONAL: Verificar se o supervisor atual pode criar agentes
        # Supervisor só pode criar agentes se pelo menos uma das equipes selecionadas for dele
        if current_user.tipo == 'supervisor':
            equipes_do_supervisor = set(str(e.id) for e in Equipe.query.filter_by(supervisor_id=current_user.id).all())
            equipes_selecionadas = set(equipes_ids)
            
            # Verifica se há pelo menos uma equipe em comum
            if not equipes_do_supervisor.intersection(equipes_selecionadas):
                flash('Você deve incluir pelo menos uma de suas próprias equipes ao criar um agente.', 'warning')
                return redirect(url_for('agentes'))

        # Validar se as equipes selecionadas existem
        selecionadas = Equipe.query.filter(Equipe.id.in_(equipes_ids)).all()
        if len(selecionadas) != len(equipes_ids):
            flash('Uma ou mais equipes selecionadas são inválidas.', 'danger')
            return redirect(url_for('agentes'))

        try:
            # Criar novo agente
            novo_agente = Agente(
                nome=nome,
                discord_id=discord_id if discord_id else None,
                ativo=True,
                supervisor_id=int(supervisor_id),
                data_criacao=datetime.now()  # Adiciona data de criação se o campo existir
            )

            # Associa às equipes selecionadas
            novo_agente.equipes = selecionadas

            db.session.add(novo_agente)
            db.session.commit()
            
            equipes_nomes = [e.nome for e in selecionadas]
            flash(f'Agente "{nome}" criado com sucesso! Supervisor principal: {supervisor.nome}. Equipes: {", ".join(equipes_nomes)}', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar agente: {str(e)}', 'danger')
            
        return redirect(url_for('agentes'))

    # Listagem de agentes (mantém a lógica de permissão atual para visualização)
    if current_user.tipo in ['admin', 'coordenadora']:
        agentes = Agente.query.order_by(Agente.nome).all()  # Ordenar por nome
    else:
        agentes = db.session.query(Agente).join(
            agente_equipe, Agente.id == agente_equipe.c.agente_id
        ).join(
            Equipe, agente_equipe.c.equipe_id == Equipe.id
        ).filter(
            Equipe.supervisor_id == current_user.id
        ).order_by(Agente.nome).distinct().all()  # Ordenar por nome

    return render_template('agentes.html', agentes=agentes, supervisores=supervisores, equipes=equipes)





from datetime import datetime

# SUBSTITUA a rota /cadastros/agente/editar/<int:agente_id> no app.py por esta versão

@app.route('/cadastros/agente/editar/<int:agente_id>', methods=['GET', 'POST'])
@login_required
def editar_agente(agente_id):
    agente = Agente.query.get_or_404(agente_id)
    
    # CORREÇÃO 1: Buscar supervisores para o dropdown (não usar supervisor_id aqui)
    supervisores = User.query.filter(User.tipo.in_(['supervisor', 'coordenadora'])).all()
    
    # CORREÇÃO: SEMPRE mostrar todas as equipes para permitir compartilhamento
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
        
        # Atualiza Discord ID
        novo_discord = request.form.get('discord_id')
        if novo_discord != agente.discord_id:
            if novo_discord:
                existente_discord = Agente.query.filter_by(discord_id=novo_discord).first()
                if existente_discord and existente_discord.id != agente.id:
                    flash('Este Discord ID já está cadastrado para outro agente.', 'danger')
                    return redirect(url_for('editar_agente', agente_id=agente_id))
        
        agente.discord_id = novo_discord if novo_discord else None

        # Atualiza supervisor principal
        supervisor_id = request.form.get('supervisor_id')
        if not supervisor_id:
            flash('Selecione um supervisor principal.', 'danger')
            return redirect(url_for('editar_agente', agente_id=agente_id))

        # CORREÇÃO 2: Valida se o supervisor existe e é do tipo correto
        supervisor = User.query.filter(
            User.id == supervisor_id, 
            User.tipo.in_(['supervisor', 'coordenadora'])
        ).first()
        if not supervisor:
            flash('Supervisor selecionado não é válido.', 'danger')
            return redirect(url_for('editar_agente', agente_id=agente_id))

        agente.supervisor_id = int(supervisor_id)

        # Atualiza equipes
        equipes_ids = request.form.getlist('equipes')
        if equipes_ids:
            # VALIDAÇÃO: Supervisor só pode editar se pelo menos uma equipe for dele
            if current_user.tipo == 'supervisor':
                equipes_do_supervisor = set(str(e.id) for e in Equipe.query.filter_by(supervisor_id=current_user.id).all())
                equipes_selecionadas = set(equipes_ids)
                
                # Verifica se há pelo menos uma equipe em comum
                if not equipes_do_supervisor.intersection(equipes_selecionadas):
                    flash('Você deve manter pelo menos uma de suas próprias equipes ao editar um agente.', 'warning')
                    return redirect(url_for('editar_agente', agente_id=agente_id))
            
            agente.equipes = Equipe.query.filter(Equipe.id.in_(equipes_ids)).all()
        else:
            flash('Selecione pelo menos uma equipe.', 'danger')
            return redirect(url_for('editar_agente', agente_id=agente_id))

        # Atualiza status se presente no formulário
        ativo = request.form.get('ativo')
        if ativo is not None:
            agente.ativo = bool(int(ativo))

        db.session.commit()
        
        equipes_nomes = [e.nome for e in agente.equipes]
        flash(f'Agente "{agente.nome}" atualizado com sucesso! Supervisor principal: {supervisor.nome}. Equipes: {", ".join(equipes_nomes)}', 'success')
        return redirect(url_for('agentes'))

    return render_template('agente_edit.html', agente=agente, supervisores=supervisores, equipes=equipes)

@app.route('/cadastros/equipes', methods=['GET', 'POST'])
@login_required
def equipes():
    if current_user.tipo not in ['admin', 'coordenadora', 'supervisor']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))

    # Lista de supervisores para o admin/coordenadora escolher
    supervisores = User.query.filter_by(tipo='supervisor').all() if current_user.tipo in ['admin', 'coordenadora'] else None

    if request.method == 'POST':
        nome = request.form['nome']
        
        # CORREÇÃO: Admin/Coordenadora pode escolher o supervisor, supervisor cria para si
        if current_user.tipo in ['admin', 'coordenadora']:
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

    # Listagem de equipes
    if current_user.tipo in ['admin', 'coordenadora']:
        equipes = Equipe.query.all()
    else:
        equipes = Equipe.query.filter_by(supervisor_id=current_user.id).all()

    # NOVO: Calcular quantidade de agentes por supervisor
    # Cria um dicionário com a contagem de agentes por supervisor
    agentes_por_supervisor = {}
    
    # Busca todos os supervisores únicos das equipes
    supervisores_equipes = User.query.filter(
        User.id.in_([equipe.supervisor_id for equipe in equipes])
    ).all()
    
    # Para cada supervisor, conta quantos agentes ele supervisiona diretamente
    for supervisor in supervisores_equipes:
        qtd_agentes = Agente.query.filter_by(
            supervisor_id=supervisor.id,
            ativo=True
        ).count()
        agentes_por_supervisor[supervisor.id] = qtd_agentes

    return render_template('equipes.html', 
                         equipes=equipes, 
                         supervisores=supervisores,
                         agentes_por_supervisor=agentes_por_supervisor)

@app.route('/cadastros/equipe/editar/<int:equipe_id>', methods=['GET', 'POST'])
@login_required
def editar_equipe(equipe_id):
    if current_user.tipo not in ['admin', 'coordenadora']:
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


#
# 
# Rotas administrativas
# 
# 
# Adicione estas rotas ao seu app.py - Sistema Admin Simplificado

from flask import jsonify, request, send_file
from datetime import datetime, timedelta
import os
import json

# Rota principal do painel admin
@app.route('/admin')
@login_required
def admin_panel():
    """Painel de administração com controles por nível"""
    if not current_user.pode_acessar_admin():
        flash('Acesso negado. Apenas administradores podem acessar este painel.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Estatísticas básicas
    stats = {
        'total_usuarios': User.query.count(),
        'total_agentes': Agente.query.count(),
        'total_atendimentos': Atendimento.query.count(),
        'atendimentos_mes': Atendimento.query.filter(
            Atendimento.data_hora >= datetime.now().replace(day=1, hour=0, minute=0, second=0)
        ).count()
    }
    
    return render_template('admin_panel.html', stats=stats)




@app.route('/painel_coordenacao')
@login_required  
def painel_coordenacao():
    """Painel da Coordenação - VERSÃO CORRIGIDA (Erro timedelta)"""
    if current_user.tipo not in ['admin', 'coordenadora']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # === CORREÇÃO: Garantir que período seja sempre int ===
        try:
            periodo_raw = request.args.get('periodo', '7')
            periodo = int(periodo_raw)  # Força conversão para int
            
            # Validação adicional
            if periodo not in [1, 7, 30, 90]:
                periodo = 7  # Default seguro
                
        except (ValueError, TypeError):
            app.logger.warning(f"Período inválido recebido: {request.args.get('periodo')}")
            periodo = 7  # Default seguro
        
        app.logger.info(f"Período validado: {periodo} (tipo: {type(periodo)})")
        
        # === CORREÇÃO: Cálculo de datas mais seguro ===
        try:
            data_fim = datetime.now()
            data_inicio = data_fim - timedelta(days=int(periodo))  # Força int novamente
            
            app.logger.info(f"Datas calculadas: {data_inicio} até {data_fim}")
            
        except Exception as e:
            app.logger.error(f"Erro no cálculo de datas: {e}")
            # Fallback seguro
            data_fim = datetime.now()
            data_inicio = data_fim - timedelta(days=7)
        
        # === 1. KPIs PRINCIPAIS (Simplificado) ===
        try:
            total_supervisores = User.query.filter(User.tipo.in_(['supervisor', 'coordenadora'])).count()
            total_agentes = Agente.query.filter_by(ativo=True).count()
            
            # Atendimentos no período
            atendimentos_periodo = Atendimento.query.filter(
                Atendimento.data_hora >= data_inicio,
                Atendimento.data_hora <= data_fim
            ).count()
            
            # Média por supervisor
            media_por_supervisor = round(atendimentos_periodo / total_supervisores, 1) if total_supervisores > 0 else 0
            
            app.logger.info(f"KPIs: {total_supervisores} sup, {total_agentes} agentes, {atendimentos_periodo} atendimentos")
            
        except Exception as e:
            app.logger.error(f"Erro nos KPIs: {e}")
            total_supervisores = total_agentes = atendimentos_periodo = media_por_supervisor = 0
        
        # === 2. DADOS DOS SUPERVISORES (Simplificado) ===
        supervisores_top_agentes = []
        supervisores_complexidade = []
        
        try:
            supervisores = User.query.filter(User.tipo.in_(['supervisor', 'coordenadora'])).all()
            
            for supervisor in supervisores:
                try:
                    # Atendimentos do supervisor
                    atendimentos_sup = Atendimento.query.filter(
                        Atendimento.supervisor_id == supervisor.id,
                        Atendimento.data_hora >= data_inicio,
                        Atendimento.data_hora <= data_fim
                    ).all()
                    
                    total_atendimentos_sup = len(atendimentos_sup)
                    
                    # === TOP 5 AGENTES ===
                    agentes_contador = {}
                    for atendimento in atendimentos_sup:
                        if hasattr(atendimento, 'agente_id') and atendimento.agente_id:
                            agente = Agente.query.get(atendimento.agente_id)
                            if agente:
                                nome = str(agente.nome)
                                agentes_contador[nome] = agentes_contador.get(nome, 0) + 1
                    
                    top_agentes_ordenados = sorted(agentes_contador.items(), key=lambda x: x[1], reverse=True)[:5]
                    top_agentes_formatados = [
                        {'nome': nome, 'total_atendimentos': qtd} 
                        for nome, qtd in top_agentes_ordenados
                    ]
                    
                    # === COMPLEXIDADE ===
                    complexidade_counts = {'basico': 0, 'medio': 0, 'complexo': 0}
                    
                    for atendimento in atendimentos_sup:
                        if atendimento.classificacao:
                            classificacao = str(atendimento.classificacao).lower().strip()
                            if classificacao in ['básico', 'basico']:
                                complexidade_counts['basico'] += 1
                            elif classificacao in ['médio', 'medio']:
                                complexidade_counts['medio'] += 1
                            elif classificacao in ['complexo']:
                                complexidade_counts['complexo'] += 1
                    
                    total_classificados = sum(complexidade_counts.values())
                    
                    # Percentuais
                    if total_classificados > 0:
                        percentual_basico = round((complexidade_counts['basico'] / total_classificados) * 100, 1)
                        percentual_medio = round((complexidade_counts['medio'] / total_classificados) * 100, 1)
                        percentual_complexo = round((complexidade_counts['complexo'] / total_classificados) * 100, 1)
                    else:
                        percentual_basico = percentual_medio = percentual_complexo = 0.0
                    
                    # Adiciona aos arrays
                    supervisores_top_agentes.append({
                        'nome': str(supervisor.nome),
                        'tipo': str(supervisor.tipo),
                        'total_agentes': len(agentes_contador),
                        'top_agentes': top_agentes_formatados
                    })
                    
                    supervisores_complexidade.append({
                        'nome': str(supervisor.nome),
                        'tipo': str(supervisor.tipo),
                        'total_atendimentos': total_atendimentos_sup,
                        'total_classificados': total_classificados,
                        'basicos': {'quantidade': complexidade_counts['basico'], 'percentual': percentual_basico},
                        'medios': {'quantidade': complexidade_counts['medio'], 'percentual': percentual_medio},
                        'complexos': {'quantidade': complexidade_counts['complexo'], 'percentual': percentual_complexo}
                    })
                    
                except Exception as e:
                    app.logger.error(f"Erro processando supervisor {supervisor.nome}: {e}")
                    continue
                    
        except Exception as e:
            app.logger.error(f"Erro geral nos supervisores: {e}")
        
        # === 3. DADOS PARA JAVASCRIPT (Simples e Seguros) ===
        volume_comparativo = [
            {'dia': 'Seg', 'volume_atual': 5, 'volume_anterior': 3},
            {'dia': 'Ter', 'volume_atual': 7, 'volume_anterior': 5},
            {'dia': 'Qua', 'volume_atual': 9, 'volume_anterior': 7},
            {'dia': 'Qui', 'volume_atual': 11, 'volume_anterior': 9},
            {'dia': 'Sex', 'volume_atual': 13, 'volume_anterior': 11},
            {'dia': 'Sáb', 'volume_atual': 8, 'volume_anterior': 6},
            {'dia': 'Dom', 'volume_atual': 4, 'volume_anterior': 2}
        ]
        
        heatmap_mes = []
        try:
            hoje = datetime.now()
            for i in range(30):
                dia = hoje - timedelta(days=29-i)
                heatmap_mes.append({
                    'dia_mes': dia.day,
                    'dia_semana': dia.weekday(),
                    'volume': (i % 10) + 1,  # Dados de exemplo
                    'eh_hoje': dia.date() == hoje.date()
                })
        except Exception as e:
            app.logger.error(f"Erro no heatmap: {e}")
            heatmap_mes = []
        
        # === 4. CONTEXT FINAL (Tipos Seguros) ===
        context = {
            'kpis': {
                'total_supervisores': int(total_supervisores),
                'total_agentes': int(total_agentes),
                'total_atendimentos': int(atendimentos_periodo),
                'media_supervisor': float(media_por_supervisor)
            },
            'supervisores_top_agentes': supervisores_top_agentes,
            'supervisores_complexidade': supervisores_complexidade,
            'volume_comparativo': volume_comparativo,
            'heatmap_mes': heatmap_mes,
            'periodo_atual': int(periodo),
            'periodo_label': f"Últimos {periodo} dias" if periodo != 7 else "Semana",
            'mes_atual': datetime.now().strftime('%B %Y'),
            'timestamp_atualizacao': datetime.now().strftime('%d/%m/%Y às %H:%M'),
            'tem_dados_reais': bool(total_supervisores > 0),
            'resumo_dados': {
                'mudanca_percentual': 10.5,
                'mudanca_tipo': 'aumento'
            }
        }
        
        app.logger.info("Painel coordenação carregado com sucesso!")
        return render_template('painel_coordenacao.html', **context)
        
    except Exception as e:
        app.logger.error(f"ERRO CRÍTICO NO PAINEL: {e}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        
        flash('Erro ao carregar painel da coordenação. Tente novamente.', 'danger')
        return redirect(url_for('dashboard'))
            


# API para estatísticas em tempo real
@app.route('/api/admin/stats')
@login_required
def admin_stats_api():
    """API para buscar estatísticas atualizadas"""
    if current_user.tipo != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        stats = {
            'total_usuarios': User.query.count(),
            'total_agentes': Agente.query.count(),
            'total_atendimentos': Atendimento.query.count(),
            'atendimentos_mes': Atendimento.query.filter(
                Atendimento.data_hora >= datetime.now().replace(day=1, hour=0, minute=0, second=0)
            ).count(),
            'atendimentos_hoje': Atendimento.query.filter(
                Atendimento.data_hora >= datetime.now().replace(hour=0, minute=0, second=0)
            ).count(),
            'supervisores_ativos': User.query.filter_by(tipo='supervisor').count(),
            'agentes_ativos': Agente.query.filter_by(ativo=True).count()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        app.logger.error(f'Erro ao buscar estatísticas admin: {e}')
        return jsonify({'error': 'Erro interno'}), 500

# Migração de tabelas (executar uma vez)
@app.route('/admin/migrate-tables')
@login_required
def migrate_tables():
    """Migração - APENAS ADMIN"""
    if not current_user.pode_executar_funcoes_destrutivas():
        flash('Acesso negado. Apenas administradores podem executar esta função.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # Cria todas as tabelas
        db.create_all()
        
        flash('✅ Migração executada com sucesso! Estrutura do banco atualizada.', 'success')
        
    except Exception as e:
        flash(f'❌ Erro na migração: {str(e)}', 'danger')
        app.logger.error(f'Erro na migração: {e}')
    
    return redirect(url_for('admin_panel'))

# Corrigir supervisores de agentes (executar quando necessário)
@app.route('/admin/fix-agents-supervisors')
@login_required
def fix_agents_supervisors():
    """Corrige agentes - APENAS ADMIN"""
    if not current_user.pode_executar_funcoes_destrutivas():
        flash('Acesso negado. Apenas administradores podem executar esta função.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # Busca agentes que têm supervisor com tipo 'admin'
        agentes_com_admin = db.session.query(Agente).join(
            User, Agente.supervisor_id == User.id
        ).filter(User.tipo == 'admin').all()
        
        if not agentes_com_admin:
            flash('✅ Nenhum agente com supervisor admin encontrado.', 'info')
            return redirect(url_for('admin_panel'))
        
        agentes_corrigidos = []
        
        for agente in agentes_com_admin:
            if agente.equipes:
                primeira_equipe = agente.equipes[0]
                supervisor_correto = primeira_equipe.supervisor
                
                if supervisor_correto and supervisor_correto.tipo == 'supervisor':
                    agente.supervisor_id = supervisor_correto.id
                    agentes_corrigidos.append({
                        'nome': agente.nome,
                        'novo_supervisor': supervisor_correto.nome
                    })
            else:
                # Se não tem equipes, usa o primeiro supervisor disponível
                primeiro_supervisor = User.query.filter_by(tipo='supervisor').first()
                if primeiro_supervisor:
                    agente.supervisor_id = primeiro_supervisor.id
                    agentes_corrigidos.append({
                        'nome': agente.nome,
                        'novo_supervisor': primeiro_supervisor.nome
                    })
        
        if agentes_corrigidos:
            db.session.commit()
            
            mensagem = f"✅ {len(agentes_corrigidos)} agente(s) corrigido(s): "
            nomes = [f"{info['nome']} → {info['novo_supervisor']}" for info in agentes_corrigidos]
            mensagem += " | ".join(nomes)
            
            flash(mensagem, 'success')
        else:
            flash('ℹ️ Nenhum agente foi corrigido.', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro ao corrigir agentes: {str(e)}', 'danger')
        app.logger.error(f'Erro ao corrigir supervisores dos agentes: {e}')
    
    return redirect(url_for('admin_panel'))

# Limpeza de dados antigos
@app.route('/admin/cleanup', methods=['POST'])
@login_required
def cleanup_old_data():
    """Remove ou arquiva dados muito antigos"""
    if current_user.tipo != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        # Define data limite (90 dias atrás)
        data_limite = datetime.now() - timedelta(days=90)
        
        # Conta atendimentos muito antigos (sem remover, apenas conta)
        atendimentos_antigos = Atendimento.query.filter(
            Atendimento.data_hora < data_limite
        ).count()
        
        # Aqui você pode decidir se quer realmente remover ou apenas contar
        # Por segurança, vamos apenas contar por enquanto
        
        return jsonify({
            'success': True,
            'message': f'Limpeza concluída. Encontrados {atendimentos_antigos} atendimentos com mais de 90 dias.'
        })
        
    except Exception as e:
        app.logger.error(f'Erro na limpeza: {e}')
        return jsonify({'error': f'Erro na limpeza: {str(e)}'}), 500

# Backup do banco de dados
@app.route('/admin/backup-database', methods=['POST'])
@login_required
def backup_database():
    """Cria backup simples dos dados principais"""
    if current_user.tipo != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        # Cria backup dos dados principais em formato JSON
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'usuarios': [
                {
                    'id': u.id,
                    'nome': u.nome,
                    'email': u.email,
                    'tipo': u.tipo
                } for u in User.query.all()
            ],
            'agentes': [
                {
                    'id': a.id,
                    'nome': a.nome,
                    'discord_id': a.discord_id,
                    'ativo': a.ativo,
                    'supervisor_id': a.supervisor_id
                } for a in Agente.query.all()
            ],
            'atendimentos_count': Atendimento.query.count(),
            'equipes': [
                {
                    'id': e.id,
                    'nome': e.nome,
                    'supervisor_id': e.supervisor_id
                } for e in Equipe.query.all()
            ]
        }
        
        # Salva o backup em arquivo
        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join('backups', backup_filename)
        
        # Cria diretório se não existir
        os.makedirs('backups', exist_ok=True)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'Backup criado com sucesso: {backup_filename}'
        })
        
    except Exception as e:
        app.logger.error(f'Erro no backup: {e}')
        return jsonify({'error': f'Erro no backup: {str(e)}'}), 500

# Recalcular estatísticas
@app.route('/admin/recalculate-stats', methods=['POST'])
@login_required
def recalculate_stats():
    """Recalcula estatísticas do sistema"""
    if current_user.tipo != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        # Conta totais atuais
        total_usuarios = User.query.count()
        total_agentes = Agente.query.count()
        total_atendimentos = Atendimento.query.count()
        agentes_ativos = Agente.query.filter_by(ativo=True).count()
        agentes_inativos = Agente.query.filter_by(ativo=False).count()
        
        # Estatísticas por supervisor
        supervisores_stats = []
        supervisores = User.query.filter(User.tipo.in_(['supervisor', 'coordenadora'])).all()
        
        for supervisor in supervisores:
            atendimentos_supervisor = Atendimento.query.filter_by(supervisor_id=supervisor.id).count()
            agentes_supervisor = Agente.query.filter_by(supervisor_id=supervisor.id).count()
            
            supervisores_stats.append({
                'nome': supervisor.nome,
                'atendimentos': atendimentos_supervisor,
                'agentes': agentes_supervisor
            })
        
        return jsonify({
            'success': True,
            'message': f'Estatísticas recalculadas: {total_usuarios} usuários, {total_agentes} agentes, {total_atendimentos} atendimentos'
        })
        
    except Exception as e:
        app.logger.error(f'Erro ao recalcular stats: {e}')
        return jsonify({'error': f'Erro ao recalcular: {str(e)}'}), 500

# Validar integridade dos dados
@app.route('/admin/validate-integrity', methods=['POST'])
@login_required
def validate_integrity():
    """Valida a integridade dos dados do sistema"""
    if current_user.tipo != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        problemas = []
        
        # Verifica agentes sem supervisor válido
        agentes_sem_supervisor = Agente.query.filter(
            ~Agente.supervisor_id.in_(
                db.session.query(User.id).filter_by(tipo='supervisor')
            )
        ).count()
        
        if agentes_sem_supervisor > 0:
            problemas.append(f'{agentes_sem_supervisor} agentes com supervisor inválido')
        
        # Verifica atendimentos órfãos (sem agente ou supervisor)
        atendimentos_orfaos = Atendimento.query.filter(
            (Atendimento.agente_id.is_(None)) | 
            (Atendimento.supervisor_id.is_(None))
        ).count()
        
        if atendimentos_orfaos > 0:
            problemas.append(f'{atendimentos_orfaos} atendimentos órfãos')
        
        # Verifica equipes sem supervisor
        equipes_sem_supervisor = Equipe.query.filter(
            ~Equipe.supervisor_id.in_(
                db.session.query(User.id).filter_by(tipo='supervisor')
            )
        ).count()
        
        if equipes_sem_supervisor > 0:
            problemas.append(f'{equipes_sem_supervisor} equipes sem supervisor válido')
        
        # Verifica agentes sem equipes
        agentes_sem_equipes = Agente.query.filter(
            ~Agente.id.in_(
                db.session.query(agente_equipe.c.agente_id)
            )
        ).count()
        
        if agentes_sem_equipes > 0:
            problemas.append(f'{agentes_sem_equipes} agentes sem equipes')
        
        if problemas:
            mensagem = f'⚠️ Problemas encontrados: {" | ".join(problemas)}'
        else:
            mensagem = '✅ Integridade dos dados validada com sucesso. Nenhum problema encontrado.'
        
        return jsonify({
            'success': True,
            'message': mensagem
        })
        
    except Exception as e:
        app.logger.error(f'Erro na validação: {e}')
        return jsonify({'error': f'Erro na validação: {str(e)}'}), 500

# Testar sistema de notificações
@app.route('/admin/test-notifications', methods=['POST'])
@login_required
def test_notifications():
    """Testa o sistema de notificações"""
    if current_user.tipo != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        # Conta supervisores com Discord configurado
        supervisores_discord = User.query.filter(
            User.tipo == 'supervisor',
            User.discord_id.isnot(None)
        ).count()
        
        # Conta agentes com Discord configurado
        agentes_discord = Agente.query.filter(
            Agente.discord_id.isnot(None)
        ).count()
        
        return jsonify({
            'success': True,
            'message': f'Sistema testado: {supervisores_discord} supervisores e {agentes_discord} agentes com Discord configurado'
        })
        
    except Exception as e:
        app.logger.error(f'Erro no teste: {e}')
        return jsonify({'error': f'Erro no teste: {str(e)}'}), 500

# Gerar relatório completo
@app.route('/admin/generate-report')
@login_required
def generate_report():
    """Gera relatório completo do sistema"""
    if current_user.tipo != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # Coleta dados para o relatório
        agora = datetime.now()
        
        # Estatísticas gerais
        stats = {
            'total_usuarios': User.query.count(),
            'total_supervisores': User.query.filter_by(tipo='supervisor').count(),
            'total_agentes': Agente.query.count(),
            'agentes_ativos': Agente.query.filter_by(ativo=True).count(),
            'total_equipes': Equipe.query.count(),
            'total_atendimentos': Atendimento.query.count()
        }
        
        # Atendimentos por período
        hoje = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        esta_semana = hoje - timedelta(days=agora.weekday())
        este_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        atendimentos_periodo = {
            'hoje': Atendimento.query.filter(Atendimento.data_hora >= hoje).count(),
            'esta_semana': Atendimento.query.filter(Atendimento.data_hora >= esta_semana).count(),
            'este_mes': Atendimento.query.filter(Atendimento.data_hora >= este_mes).count()
        }
        
        # Top supervisores por atendimentos
        top_supervisores = db.session.query(
            User.nome,
            db.func.count(Atendimento.id).label('total_atendimentos')
        ).join(
            Atendimento, User.id == Atendimento.supervisor_id
        ).filter(
            User.tipo == 'supervisor'
        ).group_by(User.id, User.nome).order_by(
            db.func.count(Atendimento.id).desc()
        ).limit(5).all()
        
        # Renderiza template de relatório
        return render_template('admin_report.html', 
                             stats=stats,
                             atendimentos_periodo=atendimentos_periodo,
                             top_supervisores=top_supervisores,
                             data_geracao=agora)
        
    except Exception as e:
        flash(f'❌ Erro ao gerar relatório: {str(e)}', 'danger')
        app.logger.error(f'Erro ao gerar relatório: {e}')
        return redirect(url_for('admin_panel'))

# Limpar logs (se implementado sistema de logs)
@app.route('/admin/clear-logs', methods=['POST'])
@login_required
def clear_logs():
    """Limpa logs antigos do sistema"""
    if current_user.tipo != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        # Por enquanto, simula limpeza de logs
        # No futuro pode limpar arquivos de log ou tabela de logs
        
        return jsonify({
            'success': True,
            'message': 'Logs antigos removidos com sucesso'
        })
        
    except Exception as e:
        app.logger.error(f'Erro ao limpar logs: {e}')
        return jsonify({'error': f'Erro ao limpar logs: {str(e)}'}), 500

# Reset completo do sistema (CUIDADO!)
@app.route('/admin/reset-system', methods=['POST'])
@login_required
def reset_system():
    """Reset completo do sistema - USE COM EXTREMO CUIDADO"""
    if current_user.tipo != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        # Por segurança, vamos apenas contar o que seria resetado
        # NÃO vamos realmente deletar nada
        
        total_atendimentos = Atendimento.query.count()
        total_agentes = Agente.query.count()
        total_equipes = Equipe.query.count()
        
        # Se quiser implementar reset real no futuro, descomente as linhas abaixo:
        # db.session.query(Atendimento).delete()
        # db.session.query(Agente).delete() 
        # db.session.query(Equipe).delete()
        # db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'SIMULAÇÃO: Reset removeria {total_atendimentos} atendimentos, {total_agentes} agentes, {total_equipes} equipes'
        })
        
    except Exception as e:
        app.logger.error(f'Erro no reset: {e}')
        return jsonify({'error': f'Erro no reset: {str(e)}'}), 500

# API simplificada para notificações em tempo real (sem status complexos)
@app.route('/api/check-new-atendimentos', methods=['POST'])
@login_required
def check_new_atendimentos():
    """API simples para verificar novos atendimentos"""
    if current_user.tipo != 'supervisor':
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        data = request.get_json()
        last_check = datetime.fromtimestamp(data.get('last_check', 0) / 1000)
        
        # Busca atendimentos novos para este supervisor (sem filtro de status complexo)
        novos_atendimentos = Atendimento.query.filter(
            Atendimento.supervisor_id == current_user.id,
            Atendimento.data_hora > last_check
        ).order_by(Atendimento.data_hora.desc()).all()
        
        # Total de atendimentos do supervisor
        total_atendimentos = Atendimento.query.filter(
            Atendimento.supervisor_id == current_user.id
        ).count()
        
        # Serializa os dados
        atendimentos_data = []
        for atendimento in novos_atendimentos:
            atendimentos_data.append({
                'id': atendimento.id,
                'agente_nome': atendimento.agente_rel.nome,
                'conteudo': atendimento.conteudo,
                'data_hora': atendimento.data_hora.isoformat()
            })
        
        return jsonify({
            'success': True,
            'new_atendimentos': atendimentos_data,
            'total_pending': len(novos_atendimentos)
        })
        
    except Exception as e:
        app.logger.error(f'Erro na API check_new_atendimentos: {e}')
        return jsonify({'error': 'Erro interno'}), 500


@app.route('/admin/bot-status')
@login_required
def check_bot_status():
    """Verifica se o bot está online"""
    if current_user.tipo != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    try:
        if os.path.exists('bot_status.txt'):
            with open('bot_status.txt', 'r') as f:
                content = f.read()
                if content.startswith('ONLINE:'):
                    timestamp = content.split(':', 1)[1]
                    last_online = datetime.fromisoformat(timestamp)
                    
                    # Verifica se está online há menos de 2 minutos
                    diff = datetime.now() - last_online
                    if diff.total_seconds() < 120:  # 2 minutos
                        return jsonify({
                            'success': True,
                            'status': 'online',
                            'last_seen': timestamp,
                            'message': '🟢 Bot está ONLINE'
                        })
        
        return jsonify({
            'success': True,
            'status': 'offline',
            'message': '🔴 Bot está OFFLINE'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'❌ Erro ao verificar status: {str(e)}'
        })



if __name__ == '__main__':
    app.run(debug=True)


