from flask import Flask, render_template, request, url_for, redirect, flash
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jkqk mzcm socn kopq'

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configuração do Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'julianalempk29@gmail.com'
app.config['MAIL_PASSWORD'] = 'Ju@01051990'
app.config['MAIL_DEFAULT_SENDER'] = 'julianalempk29@gmail.com'

mail = Mail(app)

# Modelo de Usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(120), nullable=False)
    token_reset_senha = db.Column(db.String(120), nullable=True)
    token_expiracao = db.Column(db.DateTime, nullable=True)

# Gere o banco de dados (só na primeira vez)
# Rode isso interativamente ou crie um script separado
# with app.app_context():
#     db.create_all()

def gerar_token_reset():
    return secrets.token_urlsafe(16)

def enviar_email_reset_senha(email, token):
    msg = Message('Redefinição de Senha', recipients=[email])
    link_redefinicao = url_for('redefinir_senha', token=token, _external=True)
    msg.body = f'Clique no link abaixo para redefinir sua senha:\n\n{link_redefinicao}\n\nEste link é válido por 1 hora.'
    mail.send(msg)

@app.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = gerar_token_reset()
            user.token_reset_senha = token
            user.token_expiracao = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            enviar_email_reset_senha(email, token)
            flash('Um link para redefinição de senha foi enviado para o seu e-mail.', 'info')
            return redirect(url_for('login'))
        else:
            flash('Não encontramos um usuário com este e-mail.', 'danger')
    return render_template('esqueci_senha.html')

@app.route('/redefinir_senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    user = User.query.filter_by(token_reset_senha=token).first()
    if user and user.token_expiracao > datetime.utcnow():
        if request.method == 'POST':
            nova_senha = request.form['nova_senha']
            confirmar_nova_senha = request.form['confirmar_nova_senha']
            if nova_senha == confirmar_nova_senha:
                user.senha = nova_senha
                user.token_reset_senha = None
                user.token_expiracao = None
                db.session.commit()
                flash('Sua senha foi redefinida com sucesso. Faça login com a nova senha.', 'success')
                return redirect(url_for('login'))
            else:
                flash('As novas senhas não coincidem.', 'danger')
        return render_template('redefinir_senha.html')
    flash('Este link de redefinição de senha é inválido ou expirou.', 'danger')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        user = User.query.filter_by(email=email, senha=senha).first()
        if user:
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('pagina_principal'))
        else:
            flash('Credenciais inválidas.', 'danger')
    return render_template('registro.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        if User.query.filter_by(email=email).first():
            flash('Email já registrado.', 'danger')
        else:
            novo_user = User(email=email, senha=senha)
            db.session.add(novo_user)
            db.session.commit()
            flash('Usuário registrado com sucesso!', 'success')
            return redirect(url_for('login'))
    return render_template('registro.html')

@app.route('/pagina_principal')
def pagina_principal():
    return "Página Principal"

if __name__ == '__main__':
    app.run(debug=True)

