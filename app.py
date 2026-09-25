"""
Sistema de Cobranças Financeiras - CRUD em Python (Flask + SQLite)
Formas de pagamento: PIX, TED, Dinheiro, Cartão de Crédito, Cartão de Débito, Boleto

IMPORTANTE: os arquivos .html precisam estar dentro da pasta templates/,
ao lado deste app.py. Não mova ou solte os .html fora dessa pasta.

Rodar: python app.py  ->  abrir http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "cobrancas.db")

FORMAS_PAGAMENTO = ["PIX", "TED", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "Boleto"]
STATUS_OPCOES = ["pendente", "pago", "atrasado", "cancelado"]

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
        CREATE TABLE IF NOT EXISTS cobrancas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            forma_pagamento TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente',
            data_vencimento TEXT NOT NULL,
            data_pagamento TEXT,
            observacoes TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cliente TEXT,
            data TEXT NOT NULL,
            horas REAL NOT NULL DEFAULT 0,
            valor_hora REAL NOT NULL DEFAULT 0,
            km REAL NOT NULL DEFAULT 0,
            valor_km REAL NOT NULL DEFAULT 0,
            despesas REAL NOT NULL DEFAULT 0,
            margem REAL NOT NULL DEFAULT 0,
            preco_cobrado REAL,
            observacoes TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            valor_hora REAL NOT NULL DEFAULT 50,
            valor_km REAL NOT NULL DEFAULT 1.5,
            margem_lucro REAL NOT NULL DEFAULT 30
        )
        """
    )
    conn.execute(
        "INSERT OR IGNORE INTO configuracoes (id, valor_hora, valor_km, margem_lucro) VALUES (1, 50, 1.5, 30)"
    )
    conn.commit()
    conn.close()


def get_config(conn):
    return conn.execute("SELECT * FROM configuracoes WHERE id = 1").fetchone()


def calcular_servico(s):
    """Recebe uma linha (dict-like) de serviço e devolve os valores calculados."""
    custo_mao_obra = s["horas"] * s["valor_hora"]
    custo_deslocamento = s["km"] * s["valor_km"]
    custo_total = custo_mao_obra + custo_deslocamento + s["despesas"]
    preco_sugerido = custo_total * (1 + s["margem"] / 100)
    preco_cobrado = s["preco_cobrado"]
    lucro_estimado = (preco_cobrado if preco_cobrado is not None else preco_sugerido) - custo_total
    return {
        "custo_mao_obra": custo_mao_obra,
        "custo_deslocamento": custo_deslocamento,
        "custo_total": custo_total,
        "preco_sugerido": preco_sugerido,
        "lucro_estimado": lucro_estimado,
    }


def _atualizar_atrasadas(conn):
    """Marca como 'atrasado' toda cobrança pendente cujo vencimento já passou."""
    hoje = date.today().isoformat()
    conn.execute(
        "UPDATE cobrancas SET status = 'atrasado' WHERE status = 'pendente' AND data_vencimento < ?",
        (hoje,),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# READ (dashboard + listagem + filtros)
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    conn = get_db()
    _atualizar_atrasadas(conn)

    filtro_status = request.args.get("status", "")
    filtro_forma = request.args.get("forma", "")
    busca = request.args.get("busca", "").strip()

    query = "SELECT * FROM cobrancas WHERE 1=1"
    params = []
    if filtro_status in STATUS_OPCOES:
        query += " AND status = ?"
        params.append(filtro_status)
    if filtro_forma in FORMAS_PAGAMENTO:
        query += " AND forma_pagamento = ?"
        params.append(filtro_forma)
    if busca:
        query += " AND (cliente LIKE ? OR descricao LIKE ?)"
        params.extend([f"%{busca}%", f"%{busca}%"])
    query += " ORDER BY data_vencimento ASC, id DESC"

    cobrancas = conn.execute(query, params).fetchall()

    resumo = {
        "recebido": conn.execute("SELECT COALESCE(SUM(valor),0) FROM cobrancas WHERE status='pago'").fetchone()[0],
        "pendente": conn.execute("SELECT COALESCE(SUM(valor),0) FROM cobrancas WHERE status='pendente'").fetchone()[0],
        "atrasado": conn.execute("SELECT COALESCE(SUM(valor),0) FROM cobrancas WHERE status='atrasado'").fetchone()[0],
        "qtd_atrasado": conn.execute("SELECT COUNT(*) FROM cobrancas WHERE status='atrasado'").fetchone()[0],
    }

    conn.close()
    return render_template(
        "index.html",
        cobrancas=cobrancas,
        resumo=resumo,
        formas=FORMAS_PAGAMENTO,
        status_opcoes=STATUS_OPCOES,
        filtro_status=filtro_status,
        filtro_forma=filtro_forma,
        busca=busca,
    )


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
@app.route("/nova", methods=["GET", "POST"])
def nova():
    if request.method == "POST":
        dados = _ler_formulario()
        if dados is None:
            return redirect(url_for("nova"))

        conn = get_db()
        conn.execute(
            """INSERT INTO cobrancas
               (cliente, descricao, valor, forma_pagamento, status, data_vencimento, data_pagamento, observacoes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                dados["cliente"], dados["descricao"], dados["valor"], dados["forma_pagamento"],
                dados["status"], dados["data_vencimento"], dados["data_pagamento"], dados["observacoes"],
            ),
        )
        conn.commit()
        conn.close()
        flash("Cobrança criada com sucesso.", "success")
        return redirect(url_for("index"))

    return render_template(
        "form.html", cobranca=None, formas=FORMAS_PAGAMENTO,
        status_opcoes=STATUS_OPCOES, hoje=date.today().isoformat(),
    )


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    conn = get_db()
    cobranca = conn.execute("SELECT * FROM cobrancas WHERE id = ?", (id,)).fetchone()

    if cobranca is None:
        conn.close()
        flash("Cobrança não encontrada.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        dados = _ler_formulario()
        if dados is None:
            conn.close()
            return redirect(url_for("editar", id=id))

        conn.execute(
            """UPDATE cobrancas SET cliente=?, descricao=?, valor=?, forma_pagamento=?,
               status=?, data_vencimento=?, data_pagamento=?, observacoes=? WHERE id=?""",
            (
                dados["cliente"], dados["descricao"], dados["valor"], dados["forma_pagamento"],
                dados["status"], dados["data_vencimento"], dados["data_pagamento"], dados["observacoes"], id,
            ),
        )
        conn.commit()
        conn.close()
        flash("Cobrança atualizada com sucesso.", "success")
        return redirect(url_for("index"))

    conn.close()
    return render_template(
        "form.html", cobranca=cobranca, formas=FORMAS_PAGAMENTO,
        status_opcoes=STATUS_OPCOES, hoje=date.today().isoformat(),
    )


@app.route("/marcar-pago/<int:id>", methods=["POST"])
def marcar_pago(id):
    conn = get_db()
    conn.execute(
        "UPDATE cobrancas SET status='pago', data_pagamento=? WHERE id=?",
        (date.today().isoformat(), id),
    )
    conn.commit()
    conn.close()
    flash("Cobrança marcada como paga.", "success")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    conn = get_db()
    conn.execute("DELETE FROM cobrancas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Cobrança excluída.", "success")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# PRECIFICAÇÃO DE SERVIÇOS (CRUD)
# ---------------------------------------------------------------------------
@app.route("/servicos")
def servicos():
    conn = get_db()
    linhas = conn.execute("SELECT * FROM servicos ORDER BY data DESC, id DESC").fetchall()

    lista = []
    totais = {"custo": 0.0, "sugerido": 0.0, "cobrado": 0.0, "lucro": 0.0}
    for s in linhas:
        calc = calcular_servico(s)
        lista.append({"s": s, "calc": calc})
        totais["custo"] += calc["custo_total"]
        totais["sugerido"] += calc["preco_sugerido"]
        totais["cobrado"] += s["preco_cobrado"] if s["preco_cobrado"] is not None else calc["preco_sugerido"]
        totais["lucro"] += calc["lucro_estimado"]

    conn.close()
    return render_template("servicos.html", lista=lista, totais=totais)


@app.route("/servicos/novo", methods=["GET", "POST"])
def servico_novo():
    conn = get_db()
    config = get_config(conn)

    if request.method == "POST":
        dados = _ler_formulario_servico()
        if dados is None:
            conn.close()
            return redirect(url_for("servico_novo"))

        conn.execute(
            """INSERT INTO servicos
               (nome, cliente, data, horas, valor_hora, km, valor_km, despesas, margem, preco_cobrado, observacoes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                dados["nome"], dados["cliente"], dados["data"], dados["horas"], dados["valor_hora"],
                dados["km"], dados["valor_km"], dados["despesas"], dados["margem"],
                dados["preco_cobrado"], dados["observacoes"],
            ),
        )
        conn.commit()
        conn.close()
        flash("Serviço cadastrado com sucesso.", "success")
        return redirect(url_for("servicos"))

    conn.close()
    return render_template("servico_form.html", servico=None, config=config, hoje=date.today().isoformat())


@app.route("/servicos/editar/<int:id>", methods=["GET", "POST"])
def servico_editar(id):
    conn = get_db()
    servico = conn.execute("SELECT * FROM servicos WHERE id = ?", (id,)).fetchone()
    config = get_config(conn)

    if servico is None:
        conn.close()
        flash("Serviço não encontrado.", "danger")
        return redirect(url_for("servicos"))

    if request.method == "POST":
        dados = _ler_formulario_servico()
        if dados is None:
            conn.close()
            return redirect(url_for("servico_editar", id=id))

        conn.execute(
            """UPDATE servicos SET nome=?, cliente=?, data=?, horas=?, valor_hora=?, km=?, valor_km=?,
               despesas=?, margem=?, preco_cobrado=?, observacoes=? WHERE id=?""",
            (
                dados["nome"], dados["cliente"], dados["data"], dados["horas"], dados["valor_hora"],
                dados["km"], dados["valor_km"], dados["despesas"], dados["margem"],
                dados["preco_cobrado"], dados["observacoes"], id,
            ),
        )
        conn.commit()
        conn.close()
        flash("Serviço atualizado com sucesso.", "success")
        return redirect(url_for("servicos"))

    conn.close()
    return render_template("servico_form.html", servico=servico, config=config, hoje=date.today().isoformat())


@app.route("/servicos/excluir/<int:id>", methods=["POST"])
def servico_excluir(id):
    conn = get_db()
    conn.execute("DELETE FROM servicos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Serviço excluído.", "success")
    return redirect(url_for("servicos"))


@app.route("/servicos/gerar-cobranca/<int:id>", methods=["POST"])
def servico_gerar_cobranca(id):
    """Cria uma cobrança pendente a partir do preço sugerido (ou cobrado) do serviço."""
    conn = get_db()
    s = conn.execute("SELECT * FROM servicos WHERE id = ?", (id,)).fetchone()
    if s is None:
        conn.close()
        flash("Serviço não encontrado.", "danger")
        return redirect(url_for("servicos"))

    calc = calcular_servico(s)
    valor_final = s["preco_cobrado"] if s["preco_cobrado"] is not None else calc["preco_sugerido"]
    cliente = s["cliente"] or s["nome"]

    conn.execute(
        """INSERT INTO cobrancas
           (cliente, descricao, valor, forma_pagamento, status, data_vencimento, data_pagamento, observacoes)
           VALUES (?, ?, ?, ?, 'pendente', ?, NULL, ?)""",
        (cliente, s["nome"], round(valor_final, 2), "PIX", date.today().isoformat(), s["observacoes"]),
    )
    conn.commit()
    conn.close()
    flash("Cobrança gerada a partir do serviço. Ajuste a forma de pagamento se necessário.", "success")
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# CONFIGURAÇÕES (valores padrão usados para pré-preencher novos serviços)
# ---------------------------------------------------------------------------
@app.route("/configuracoes", methods=["GET", "POST"])
def configuracoes():
    conn = get_db()

    if request.method == "POST":
        try:
            valor_hora = float(request.form.get("valor_hora", "0").replace(",", "."))
            valor_km = float(request.form.get("valor_km", "0").replace(",", "."))
            margem_lucro = float(request.form.get("margem_lucro", "0").replace(",", "."))
            if valor_hora < 0 or valor_km < 0 or margem_lucro < 0:
                raise ValueError
        except ValueError:
            flash("Os valores padrão precisam ser números positivos.", "danger")
            conn.close()
            return redirect(url_for("configuracoes"))

        conn.execute(
            "UPDATE configuracoes SET valor_hora=?, valor_km=?, margem_lucro=? WHERE id=1",
            (valor_hora, valor_km, margem_lucro),
        )
        conn.commit()
        conn.close()
        flash("Valores padrão atualizados. Eles serão usados para pré-preencher novos serviços.", "success")
        return redirect(url_for("configuracoes"))

    config = get_config(conn)
    conn.close()
    return render_template("configuracoes.html", config=config)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ler_formulario_servico():
    nome = request.form.get("nome", "").strip()
    cliente = request.form.get("cliente", "").strip() or None
    data_serv = request.form.get("data", "").strip()
    observacoes = request.form.get("observacoes", "").strip() or None
    preco_cobrado_raw = request.form.get("preco_cobrado", "").strip().replace(",", ".")

    campos_numericos = {}
    for campo, rotulo in (
        ("horas", "Horas trabalhadas"), ("valor_hora", "Valor da hora"),
        ("km", "Km rodados"), ("valor_km", "Valor por km"),
        ("despesas", "Despesas"), ("margem", "Margem de lucro"),
    ):
        bruto = request.form.get(campo, "0").strip().replace(",", ".")
        try:
            valor = float(bruto) if bruto else 0.0
            if valor < 0:
                raise ValueError
        except ValueError:
            flash(f"O campo '{rotulo}' precisa ser um número válido (>= 0).", "danger")
            return None
        campos_numericos[campo] = valor

    if not nome or not data_serv:
        flash("Preencha ao menos o nome do serviço e a data.", "danger")
        return None

    preco_cobrado = None
    if preco_cobrado_raw:
        try:
            preco_cobrado = float(preco_cobrado_raw)
            if preco_cobrado < 0:
                raise ValueError
        except ValueError:
            flash("O preço cobrado precisa ser um número positivo.", "danger")
            return None

    return {
        "nome": nome, "cliente": cliente, "data": data_serv,
        "preco_cobrado": preco_cobrado, "observacoes": observacoes,
        **campos_numericos,
    }


def _ler_formulario():
    cliente = request.form.get("cliente", "").strip()
    descricao = request.form.get("descricao", "").strip()
    valor_raw = request.form.get("valor", "").strip().replace(",", ".")
    forma_pagamento = request.form.get("forma_pagamento", "").strip()
    status = request.form.get("status", "pendente").strip()
    data_vencimento = request.form.get("data_vencimento", "").strip()
    data_pagamento = request.form.get("data_pagamento", "").strip() or None
    observacoes = request.form.get("observacoes", "").strip() or None

    if not cliente or not descricao or not data_vencimento:
        flash("Preencha cliente, descrição e data de vencimento.", "danger")
        return None
    if forma_pagamento not in FORMAS_PAGAMENTO:
        flash("Selecione uma forma de pagamento válida.", "danger")
        return None
    if status not in STATUS_OPCOES:
        status = "pendente"

    try:
        valor = float(valor_raw)
        if valor <= 0:
            raise ValueError
    except ValueError:
        flash("O valor deve ser um número positivo.", "danger")
        return None

    return {
        "cliente": cliente, "descricao": descricao, "valor": valor,
        "forma_pagamento": forma_pagamento, "status": status,
        "data_vencimento": data_vencimento, "data_pagamento": data_pagamento,
        "observacoes": observacoes,
    }


if __name__ == "__main__":
    init_db()
    print("Sistema de Cobranças rodando em http://127.0.0.1:5000")
    app.run(debug=True)
