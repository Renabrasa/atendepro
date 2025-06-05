# 🎯 AtendePro - Sistema de Gestão de Atendimentos

![Version](https://img.shields.io/badge/version-1.0.0--alpha-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Flask](https://img.shields.io/badge/flask-2.2.5-red)
![Discord](https://img.shields.io/badge/discord.py-2.3.2-blurple)
![License](https://img.shields.io/badge/license-MIT-yellow)

> Sistema completo para gerenciar atendimentos entre agentes e supervisores via Discord, com painel web administrativo avançado.

## ✨ **Funcionalidades Principais**

### 🤖 **Bot Discord Inteligente**
- **Criação automática de atendimentos** via comando `@@problema`
- **Seleção interativa de supervisores** quando há múltiplas opções
- **Notificações em tempo real** para supervisores e agentes
- **Multi-servidor** - um bot para vários servidores Discord

### 🌐 **Painel Web Completo**
- **Dashboard executivo** com métricas em tempo real
- **Gestão completa** de supervisores, equipes e agentes
- **Sistema de filtros avançados** para busca e organização
- **Relatórios detalhados** para análise de performance

### 🔧 **Painel Administrativo**
- **Ferramentas de manutenção** do banco de dados
- **Validação de integridade** dos dados
- **Sistema de backup** automático
- **Correção automática** de problemas comuns

## 🚀 **Início Rápido**

### **Pré-requisitos**
- Python 3.8 ou superior
- Conta Discord com bot criado
- MySQL ou SQLite (para desenvolvimento)

### **Instalação Local**

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/AtendePro.git
cd AtendePro

# 2. Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure o ambiente
cp config.py.example config.py
# Edite config.py com suas configurações

# 5. Execute em modo de desenvolvimento
python run_local_test.py
```

### **Acesso Inicial**
- **URL**: http://localhost:5000
- **Admin**: admin@admin.com / admin123
- **Painel Admin**: http://localhost:5000/admin

## 🏗️ **Arquitetura do Sistema**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Discord Bot   │────│   Flask App     │────│   MySQL/SQLite  │
│                 │    │                 │    │                 │
│ • Comandos      │    │ • API Routes    │    │ • Users         │
│ • Notificações  │    │ • Templates     │    │ • Agentes       │
│ • Multi-server  │    │ • Admin Panel   │    │ • Atendimentos  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 **Principais Tecnologias**

| Componente | Tecnologia | Versão |
|------------|------------|---------|
| **Backend** | Flask | 2.2.5 |
| **Bot** | discord.py | 2.3.2 |
| **Banco de Dados** | MySQL/SQLite | - |
| **ORM** | SQLAlchemy | 2.0.19 |
| **Autenticação** | Flask-Login | 0.6.2 |
| **Frontend** | HTML/CSS/JS | - |

## 🎮 **Como Usar**

### **Para Agentes (Discord)**
1. Use o comando `@@problema` em qualquer canal
2. Escolha o supervisor desejado nos botões
3. Receba confirmação via DM
4. Aguarde contato do supervisor

### **Para Supervisores (Web + Discord)**
1. Acesse o painel web para gerenciar equipes
2. Receba notificações via Discord quando há novos atendimentos
3. Use o dashboard para acompanhar métricas
4. Gerencie agentes e atendimentos pelo painel

### **Para Administradores (Web)**
1. Acesse `/admin` para ferramentas avançadas
2. Use o dashboard para visão geral do sistema
3. Gerencie usuários, equipes e configurações
4. Execute manutenções e gere relatórios

## 📁 **Estrutura do Projeto**

```
AtendePro/
├── app.py                  # Aplicação Flask principal
├── bot.py                  # Bot Discord
├── run.py                  # Executar em produção
├── run_local_test.py       # Desenvolvimento local
├── config.py               # Configurações
├── models/models.py        # Modelos do banco de dados
├── templates/              # Templates HTML
├── static/                 # CSS, JS, imagens
└── .github/workflows/      # CI/CD automático
```

## 🔧 **Configuração**

### **Variáveis de Ambiente**
```env
SECRET_KEY=sua-chave-secreta
DATABASE_URL=mysql://user:pass@host:port/db
DISCORD_TOKEN=seu-token-do-bot
```

### **Configuração do Discord Bot**
1. Crie um bot em https://discord.com/developers/applications
2. Copie o token para `DISCORD_TOKEN`
3. Convide o bot para seus servidores com permissões:
   - Ler mensagens
   - Enviar mensagens
   - Usar comandos slash
   - Gerenciar mensagens

## 📸 **Screenshots**

### Dashboard Principal
> Visão geral com métricas em tempo real e filtros avançados

### Painel Administrativo
> Ferramentas de manutenção e relatórios detalhados

### Bot Discord em Ação
> Seleção interativa de supervisores via botões

## 🛠️ **Desenvolvimento**

### **Estrutura de Branches**
- `main` - Versão estável para produção
- `develop` - Desenvolvimento ativo
- `feature/*` - Novas funcionalidades
- `hotfix/*` - Correções urgentes

### **Como Contribuir**
1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 🚀 **Deploy**

### **Deploy Automático (AWS EC2)**
O projeto inclui workflow do GitHub Actions para deploy automático:

```yaml
# .github/workflows/deploy.yml
# Deploy automático para EC2 quando fizer push na main
```

### **Deploy Manual**
```bash
# Produção com Docker
docker build -t atendepro .
docker run -p 5000:5000 atendepro

# Produção tradicional
python run.py
```

## 📈 **Roadmap**

### **v1.1 (Próxima)**
- [ ] Sistema de tags para atendimentos
- [ ] Notificações por email
- [ ] Dashboard em tempo real com WebSocket
- [ ] API REST completa

### **v1.2 (Futuro)**
- [ ] App mobile (PWA)
- [ ] Integração Slack
- [ ] Relatórios avançados com gráficos
- [ ] Sistema de templates de resposta

### **v2.0 (Visão)**
- [ ] Inteligência artificial para classificação
- [ ] Multi-tenancy
- [ ] Integração com CRM
- [ ] Análises preditivas

## 🐛 **Problemas Conhecidos**

- SQLite local funciona perfeitamente para desenvolvimento
- MySQL em produção requer configuração de timezone
- Bot Discord precisa de permissões adequadas em cada servidor

## 📄 **Licença**

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 **Créditos**

Desenvolvido com ❤️ para facilitar a comunicação entre equipes.

## 📞 **Suporte**

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/AtendePro/issues)
- **Documentação**: [Wiki do Projeto](https://github.com/seu-usuario/AtendePro/wiki)
- **Discussões**: [GitHub Discussions](https://github.com/seu-usuario/AtendePro/discussions)

---

⭐ **Se este projeto foi útil, considere dar uma estrela no GitHub!**