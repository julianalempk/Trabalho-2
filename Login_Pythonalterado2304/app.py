import os
import random
import sqlite3
import smtplib
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import SECRET_KEY, EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, DATABASE
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = SECRET_KEY

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                verificado INTEGER DEFAULT 0,
                codigo_verificacao TEXT
            )
        ''')
        conn.commit()

def enviar_email_verificacao(destinatario, codigo):
    msg = MIMEText(f"Seu código de verificação é: {codigo}")
    msg["Subject"] = "Código de Verificação"
    msg["From"] = EMAIL_USER
    msg["To"] = destinatario
    
    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, destinatario, msg.as_string())
        return True
    except Exception as e:
        print("Erro ao enviar email:", e)
        return False

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]
        
        with get_db_connection() as conn:
            usuario = conn.execute("SELECT id, verificado, senha FROM usuarios WHERE email = ?", (email,)).fetchone()
        
        if usuario and check_password_hash(usuario["senha"], senha):
            if usuario["verificado"] == 0:
                flash("Conta não verificada. Verifique seu e-mail.", "danger")
                return redirect(url_for("verificar", email=email))
            session["usuario_id"] = usuario["id"]
            flash("Login bem-sucedido!", "success")
            return redirect(url_for("dashboard"))
        
        flash("E-mail ou senha incorretos.", "danger")
    return render_template("index.html")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]
        confirmar_senha = request.form["confirmar_senha"]
        
        if senha != confirmar_senha:
            flash("As senhas não coincidem.", "danger")
            return redirect(url_for("registro"))

        # Verificação da força da senha
        if len(senha) < 8 or not any(c.isupper() for c in senha) or not any(c.isdigit() for c in senha) or not any(c in "!@#$%^&*(),.?\":{}|<>" for c in senha):
            flash("A senha deve ter pelo menos 8 caracteres, incluindo uma letra maiúscula, um número e um caractere especial.", "danger")
            return redirect(url_for("registro"))
        
        # Gerando o hash da senha
        senha_hash = generate_password_hash(senha)

        codigo_verificacao = str(random.randint(100000, 999999))
        
        with get_db_connection() as conn:
            try:
                conn.execute("INSERT INTO usuarios (email, senha, codigo_verificacao) VALUES (?, ?, ?)", (email, senha_hash, codigo_verificacao))
                conn.commit()
                enviar_email_verificacao(email, codigo_verificacao)
                flash("Registro bem-sucedido! Verifique seu e-mail.", "success")
                return redirect(url_for("verificar", email=email))
            except sqlite3.IntegrityError:
                flash("E-mail já cadastrado!", "danger")
    return render_template("registro.html")

@app.route("/verificar/<email>", methods=["GET", "POST"])
def verificar(email):
    if request.method == "POST":
        codigo_digitado = request.form["codigo"]
        
        with get_db_connection() as conn:
            usuario = conn.execute("SELECT id FROM usuarios WHERE email = ? AND codigo_verificacao = ?", (email, codigo_digitado)).fetchone()
            if usuario:
                conn.execute("UPDATE usuarios SET verificado = 1 WHERE email = ?", (email,))
                conn.commit()
                flash("Conta verificada com sucesso! Faça login.", "success")
                return redirect(url_for("login"))
        
        flash("Código incorreto!", "danger")
    return render_template("verificar.html", email=email)

@app.route("/dashboard")
def dashboard():
    if "usuario_id" not in session:
        flash("Você precisa estar logado!", "danger")
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/logout")
def logout():
    session.pop("usuario_id", None)
    flash("Você saiu da sessão.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    criar_tabelas()
    app.run(debug=True)
