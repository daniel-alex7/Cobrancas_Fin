# Cobranças Fin — Cobranças + Precificação para Pequenos Empreendedores

Sistema em **Flask + SQLite**, com CRUD completo, pensado para autônomos e pequenos negócios
organizarem cobranças e calcularem quanto cobrar por cada serviço.

## ⚠️ Estrutura de pastas — não altere

O Flask exige que os `.html` fiquem dentro de `templates/` e o CSS dentro de `static/`,
no mesmo nível de `app.py`.

```
cobrancas_fin/
├── app.py
├── requirements.txt
├── cobrancas.db          # criado automaticamente na 1ª execução
├── static/
│   └── style.css
└── templates/
    ├── base.html
    ├── index.html
    ├── form.html
    ├── servicos.html
    ├── servico_form.html
    └── configuracoes.html
```

## Como rodar

```
pip install -r requirements.txt
python app.py
```

Abra `http://127.0.0.1:5000` no navegador.

## Módulos

### 1. Cobranças (`/`)
- **Dashboard**: total recebido, pendente, em atraso e quantidade de cobranças atrasadas
- **Create**: nova cobrança (cliente, descrição, valor, forma de pagamento, vencimento, status, observações)
- **Read**: listagem com busca por cliente/descrição e filtro por status e forma de pagamento
- **Update**: editar qualquer cobrança
- **Delete**: excluir com confirmação
- **Marcar como pago**: ação rápida que registra a data de pagamento automaticamente
- **Atraso automático**: ao carregar a página, cobranças pendentes com vencimento no passado viram "atrasado" sozinhas
- Formas de pagamento: PIX · TED · Dinheiro · Cartão de Crédito · Cartão de Débito · Boleto

### 2. Precificação de Serviços (`/servicos`)
Calculadora para descobrir quanto cobrar por serviço, considerando
**horas trabalhadas, km rodados e despesas extras**:

- **Cálculo automático**: `custo total = (horas × valor da hora) + (km × valor por km) + despesas`
  e `preço sugerido = custo total × (1 + margem de lucro)`
- Pré-visualização em tempo real no formulário (calcula enquanto você digita)
- Campo opcional de "preço efetivamente cobrado", para comparar com o sugerido e ver o lucro real
- Dashboard: custo total, total sugerido, total cobrado e lucro estimado do período
- Botão **"Gerar cobrança"**: cria automaticamente uma cobrança em `/` com o valor do serviço
- **CRUD completo**: criar, listar, editar e excluir serviços

### 3. Configurações (`/configuracoes`)
Defina os valores padrão (valor da sua hora, valor por km, margem de lucro %) que pré-preenchem
automaticamente todo novo serviço cadastrado — você ainda pode ajustar caso a caso.

## Próximos passos sugeridos

- Autenticação de usuário
- Exportar relatório de cobranças/serviços em PDF/Excel
- Envio automático de cobrança por e-mail/WhatsApp
- Gráfico de recebimentos e lucro por mês e por forma de pagamento
- Templates de serviço reutilizáveis (ex: "corte de cabelo" já com horas/despesas padrão)
