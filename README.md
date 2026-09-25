# Sistema de Contabilidade (CRUD em Python)

Aplicação web feita com **Flask + SQLite**, com acesso direto pelo navegador.
Permite Criar, Ler, Atualizar e Excluir (CRUD) lançamentos contábeis (receitas e despesas),
com resumo automático de totais e saldo.

## Como rodar

1. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

2. Rode a aplicação:
   ```
   python app.py
   ```

3. Abra o navegador em:
   ```
   http://127.0.0.1:5000
   ```

O banco de dados (`contabilidade.db`) é criado automaticamente na primeira execução.

## Estrutura

```
contabilidade/
├── app.py              # servidor Flask + rotas CRUD
├── requirements.txt
├── contabilidade.db     # criado automaticamente
└── templates/
    ├── base.html         # layout base (Bootstrap)
    ├── index.html        # listagem + resumo financeiro
    └── form.html          # formulário de criar/editar
```

## Funcionalidades

- **Create**: cadastrar novo lançamento (data, descrição, categoria, tipo, valor)
- **Read**: listar lançamentos, com filtro por tipo (receita/despesa) e resumo de totais/saldo
- **Update**: editar um lançamento existente
- **Delete**: excluir lançamento (com confirmação)

## Próximos passos sugeridos

- Autenticação de usuário
- Exportar relatórios em PDF/Excel
- Gráficos de evolução mensal
- Categorias pré-cadastradas (dropdown em vez de texto livre)
