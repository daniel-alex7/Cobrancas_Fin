"""
Sistema de Contabilidade - CRUD em Python (Flask + SQLite)
Acesse pelo navegador em http://127.0.0.1:5000 após rodar `python app.py`
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "contabilidade.db")

app = Flask(__name__)
app.secret_key = "chave-secreta-troque-em-producao"


# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK (tipo IN ('receita', 'despesa')),
            categoria TEXT NOT NULL,
            valor REAL NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# CREATE + READ (listagem com resumo)
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    conn = get_db()

    filtro_tipo = request.args.get("tipo", "")
    query = "SELECT * FROM lancamentos"
    params = []
    if filtro_tipo in ("receita", "despesa"):
        query += " WHERE tipo = ?"
        params.append(filtro_tipo)
    query += " ORDER BY data DESC, id DESC"

    lancamentos = conn.execute(query, params).fetchall()

    total_receitas = conn.execute(
        "SELECT COALESCE(SUM(valor), 0) FROM lancamentos WHERE tipo = 'receita'"
    ).fetchone()[0]
    total_despesas = conn.execute(
        "SELECT COALESCE(SUM(valor), 0) FROM lancamentos WHERE tipo = 'despesa'"
    ).fetchone()[0]
    saldo = total_receitas - total_despesas

    conn.close()

    return render_template(
        "index.html",
        lancamentos=lancamentos,
        total_receitas=total_receitas,
        total_despesas=total_despesas,
        saldo=saldo,
        filtro_tipo=filtro_tipo,
    )


@app.route("/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST":
        dados = _ler_formulario()
        if dados is None:
            return redirect(url_for("novo"))

        conn = get_db()
        conn.execute(
            "INSERT INTO lancamentos (data, descricao, tipo, categoria, valor) VALUES (?, ?, ?, ?, ?)",
            (dados["data"], dados["descricao"], dados["tipo"], dados["categoria"], dados["valor"]),
        )
        conn.commit()
        conn.close()
        flash("Lançamento criado com sucesso.", "success")
        return redirect(url_for("index"))

    return render_template("form.html", lancamento=None, hoje=date.today().isoformat())


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    conn = get_db()
    lancamento = conn.execute("SELECT * FROM lancamentos WHERE id = ?", (id,)).fetchone()

    if lancamento is None:
        conn.close()
        flash("Lançamento não encontrado.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        dados = _ler_formulario()
        if dados is None:
            conn.close()
            return redirect(url_for("editar", id=id))

        conn.execute(
            "UPDATE lancamentos SET data = ?, descricao = ?, tipo = ?, categoria = ?, valor = ? WHERE id = ?",
            (dados["data"], dados["descricao"], dados["tipo"], dados["categoria"], dados["valor"], id),
        )
        conn.commit()
        conn.close()
        flash("Lançamento atualizado com sucesso.", "success")
        return redirect(url_for("index"))

    conn.close()
    return render_template("form.html", lancamento=lancamento, hoje=date.today().isoformat())


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    conn = get_db()
    conn.execute("DELETE FROM lancamentos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Lançamento excluído.", "success")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ler_formulario():
    data = request.form.get("data", "").strip()
    descricao = request.form.get("descricao", "").strip()
    tipo = request.form.get("tipo", "").strip()
    categoria = request.form.get("categoria", "").strip()
    valor_raw = request.form.get("valor", "").strip().replace(",", ".")

    if not data or not descricao or tipo not in ("receita", "despesa") or not categoria:
        flash("Preencha todos os campos corretamente.", "danger")
        return None

    try:
        valor = float(valor_raw)
        if valor <= 0:
            raise ValueError
    except ValueError:
        flash("O valor deve ser um número positivo.", "danger")
        return None

    return {"data": data, "descricao": descricao, "tipo": tipo, "categoria": categoria, "valor": valor}


if __name__ == "__main__":
    init_db()
    print("Sistema de Contabilidade rodando em http://127.0.0.1:5000")
    app.run(debug=True)
