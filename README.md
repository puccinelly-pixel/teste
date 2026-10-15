# ✓ Tarefas — To-Do List com autenticação

Aplicação completa de lista de tarefas: **API REST em Python (FastAPI)** com autenticação **JWT** e persistência em **SQLite**, e **frontend em HTML/CSS/JavaScript puro** (ES Modules, sem build).

Cada usuário se cadastra, faz login e gerencia **apenas as próprias tarefas**.

---

## Sumário

- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Como executar localmente](#como-executar-localmente)
  - [1. Clonar o repositório](#1-clonar-o-repositório)
  - [2. Backend (API)](#2-backend-api)
  - [3. Frontend](#3-frontend)
- [Rodando os testes](#rodando-os-testes)
- [Documentação da API](#documentação-da-api)
- [Segurança](#segurança)
- [Decisões técnicas](#decisões-técnicas)
- [Problemas comuns](#problemas-comuns)

---

## Funcionalidades

**Requisitos do desafio**
- Cadastro e login de usuário com token JWT.
- CRUD de tarefas: criar, listar, atualizar e excluir.
- Campos da tarefa: `id`, `titulo`, `descricao`, `status`, `data_criacao`.
- Cada usuário só acessa as próprias tarefas.
- Persistência em SQLite.
- Interface web para login, cadastro e gerenciamento das tarefas.

**Extras implementados**
- Filtro por status, busca por texto, ordenação e paginação ("carregar mais").
- Alteração rápida de status direto no card, edição em modal e confirmação antes de excluir.
- Campo `data_atualizacao` mantido automaticamente.
- Validação no frontend **e** no backend (senha com 8+ caracteres, letras e números).
- Limite de tentativas de login por IP, cabeçalhos de segurança, CSP e proteção contra XSS (ver [Segurança](#segurança)).
- Tema claro/escuro automático, layout responsivo e cuidados de acessibilidade (rótulos, foco visível, `aria-live`, navegação por teclado, `prefers-reduced-motion`).
- 17 testes automatizados (pytest) e pipeline de CI no GitHub Actions (lint PEP8 + testes).

---

## Tecnologias

| Camada    | Tecnologia |
|-----------|------------|
| Backend   | Python 3.10+, FastAPI, SQLAlchemy 2.0, Pydantic v2, PyJWT, bcrypt, Uvicorn |
| Banco     | SQLite (arquivo `todo.db`, criado automaticamente) |
| Frontend  | HTML5, CSS3 (variáveis, grid, `color-mix`), JavaScript ES Modules, `<dialog>` nativo |
| Qualidade | pytest, httpx, flake8, GitHub Actions |

---

## Estrutura do projeto

```
.
├── backend/
│   ├── app/
│   │   ├── main.py            # Criação do app, CORS, cabeçalhos de segurança, rotas
│   │   ├── config.py          # Configurações via variáveis de ambiente (.env)
│   │   ├── database.py        # Engine SQLAlchemy e sessão por requisição
│   │   ├── models.py          # Modelos ORM: User e Task
│   │   ├── schemas.py         # Schemas Pydantic (validação de entrada/saída)
│   │   ├── security.py        # bcrypt, JWT e limitador de tentativas
│   │   ├── dependencies.py    # Dependência que identifica o usuário do token
│   │   └── routers/
│   │       ├── auth.py        # /auth/register, /auth/login, /auth/me
│   │       └── tasks.py       # /tasks (CRUD)
│   ├── tests/                 # Testes automatizados (pytest)
│   ├── requirements.txt       # Dependências de execução
│   ├── requirements-dev.txt   # + dependências de teste/lint
│   ├── setup.cfg              # Configuração do flake8 e pytest
│   └── .env.example           # Modelo de configuração
├── frontend/
│   ├── index.html             # Telas de login/cadastro e de tarefas
│   ├── css/styles.css
│   └── js/
│       ├── config.js          # URL da API e constantes
│       ├── api.js             # Cliente HTTP (token, timeout, erros)
│       ├── session.js         # Armazenamento da sessão
│       ├── ui.js              # Renderização segura e componentes de UI
│       └── app.js             # Controlador: eventos e fluxo das telas
└── .github/workflows/ci.yml   # Integração contínua
```

---

## Pré-requisitos

- **Python 3.10 ou superior** — verifique com `python --version` (Windows) ou `python3 --version` (Linux/macOS).
- **Git**.
- Um navegador moderno (Chrome, Edge, Firefox ou Safari atualizados).

Não é necessário Node.js: o frontend é estático e é servido com o próprio Python.

---

## Como executar localmente

Você vai usar **dois terminais**: um para a API e outro para o frontend.

### 1. Clonar o repositório

```bash
git clone https://github.com/puccinelly-pixel/teste.git
cd teste
```

### 2. Backend (API)

**Terminal 1**, a partir da raiz do projeto:

```bash
cd backend
```

**2.1. Criar e ativar um ambiente virtual**

Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> Se o PowerShell bloquear a ativação, rode uma vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e tente de novo. No Prompt de Comando (cmd), use `.venv\Scripts\activate.bat`.

**2.2. Instalar as dependências**

```bash
pip install -r requirements.txt
```

**2.3. Configurar as variáveis de ambiente**

Copie o arquivo de exemplo:

```bash
# Linux / macOS
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

Gere uma chave secreta e cole no campo `SECRET_KEY` do arquivo `.env`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

> Se você pular este passo, a API funciona mesmo assim, mas usa uma chave temporária: todos ficam deslogados sempre que o servidor reinicia.

**2.4. Iniciar a API**

```bash
uvicorn app.main:app --reload --port 8000
```

Pronto. A API está em **http://localhost:8000** e o banco `todo.db` é criado automaticamente na primeira execução.
Confira em http://localhost:8000/health — a resposta deve ser `{"status":"ok"}`.

### 3. Frontend

**Terminal 2**, a partir da raiz do projeto:

```bash
cd frontend
python -m http.server 5500
```

> No Linux/macOS, use `python3` se `python` não existir.

Abra **http://localhost:5500** no navegador, crie uma conta e comece a usar.

> ⚠️ Abra pelo endereço `http://localhost:5500` (e não clicando duas vezes no `index.html`). Os módulos JavaScript não carregam via `file://`, e a API só aceita chamadas das origens configuradas em `CORS_ORIGINS`.
>
> Também funciona com a extensão **Live Server** do VS Code, que usa a porta 5500 por padrão.

---

## Rodando os testes

Com o ambiente virtual do backend ativado:

```bash
cd backend
pip install -r requirements-dev.txt
pytest -v          # 17 testes
flake8 app tests   # verificação PEP8
```

Os testes usam um banco SQLite **em memória**, isolado a cada teste, e cobrem: cadastro, login, e-mail duplicado, senha fraca, limite de tentativas, token inválido, CRUD completo, filtros, validações e **isolamento entre usuários** (um usuário não consegue ler, editar nem excluir a tarefa de outro).

---

## Documentação da API

Com a API rodando, a documentação interativa (Swagger) fica em **http://localhost:8000/docs** — dá para testar todos os endpoints por lá (use o botão **Authorize** e cole o token).

### Endpoints

| Método | Rota              | Autenticação | Descrição |
|--------|-------------------|:------------:|-----------|
| POST   | `/auth/register`  | –            | Cadastra o usuário e retorna o token |
| POST   | `/auth/login`     | –            | Autentica e retorna o token |
| GET    | `/auth/me`        | ✔︎           | Dados do usuário logado |
| GET    | `/tasks`          | ✔︎           | Lista as tarefas do usuário |
| POST   | `/tasks`          | ✔︎           | Cria uma tarefa |
| GET    | `/tasks/{id}`     | ✔︎           | Detalha uma tarefa |
| PATCH  | `/tasks/{id}`     | ✔︎           | Atualiza parcialmente uma tarefa (`PUT` também é aceito) |
| DELETE | `/tasks/{id}`     | ✔︎           | Exclui uma tarefa |
| GET    | `/health`         | –            | Verificação de saúde |

Rotas protegidas exigem o cabeçalho `Authorization: Bearer <token>`.

**Parâmetros de `GET /tasks`:** `status` (`pendente` · `em_andamento` · `concluida`), `busca` (texto no título/descrição), `ordem` (`recentes` · `antigas`), `limit` (1–100, padrão 50) e `offset`.

### Exemplos com curl

```bash
# Cadastro
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"nome":"Ana","email":"ana@exemplo.com","senha":"senha123"}'

# Login (guarde o access_token da resposta)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ana@exemplo.com","senha":"senha123"}'

# Criar tarefa
curl -X POST http://localhost:8000/tasks \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Estudar FastAPI","descricao":"Ler a documentação"}'

# Listar só as pendentes
curl "http://localhost:8000/tasks?status=pendente" -H "Authorization: Bearer SEU_TOKEN"

# Marcar como concluída
curl -X PATCH http://localhost:8000/tasks/1 \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"concluida"}'

# Excluir
curl -X DELETE http://localhost:8000/tasks/1 -H "Authorization: Bearer SEU_TOKEN"
```

### Exemplo de tarefa

```json
{
  "id": 1,
  "titulo": "Estudar FastAPI",
  "descricao": "Ler a documentação",
  "status": "pendente",
  "data_criacao": "2026-10-15T23:30:00.123456Z",
  "data_atualizacao": "2026-10-15T23:30:00.123456Z"
}
```

### Códigos de resposta

| Código | Quando |
|--------|--------|
| 200 / 201 / 204 | Sucesso |
| 401 | Sem token, token inválido/expirado ou credenciais erradas |
| 404 | Tarefa inexistente **ou de outro usuário** |
| 409 | E-mail já cadastrado |
| 422 | Dados inválidos (ex.: título vazio, status desconhecido, senha fraca) |
| 429 | Muitas tentativas de login |

---

## Segurança

**Autenticação e senhas**
- Senhas armazenadas com **bcrypt** (hash com salt); a senha em texto nunca é salva nem devolvida.
- JWT assinado com HS256, com expiração (`exp`), emissão (`iat`) e tipo validados. O algoritmo é fixado na validação, o que impede o ataque de troca para `alg: none`.
- `SECRET_KEY` vem do `.env` (fora do Git). Sem ela, a API gera uma chave temporária e avisa no log, em vez de usar um valor fixo inseguro.
- Login com **mensagem genérica** e tempo de resposta equivalente para e-mail inexistente e senha errada (dificulta descobrir quais e-mails têm conta).
- **Limite de 5 tentativas de login por minuto por IP** (configurável).

**Autorização**
- Toda consulta de tarefa é filtrada por `usuario_id` do token. Acessar a tarefa de outro usuário retorna **404**, sem revelar que ela existe.

**API**
- CORS restrito às origens configuradas, métodos e cabeçalhos explícitos.
- Cabeçalhos `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` e `Cache-Control: no-store` nas rotas autenticadas.
- Validação estrita com Pydantic: tamanhos máximos, e-mail válido, status por enum, títulos em branco recusados.
- Consultas via ORM (sem SQL concatenado), sem risco de SQL injection.

**Frontend**
- Todo conteúdo dinâmico é inserido com `textContent`, **nunca** `innerHTML` — um título como `<img onerror=...>` aparece como texto.
- **Content-Security-Policy** que só permite scripts e estilos locais e conexões com a API.
- Token guardado em `sessionStorage` (some ao fechar a aba) e descartado ao expirar; qualquer `401` desloga o usuário com aviso.
- Botões desabilitados durante requisições (evita envios duplicados) e timeout de 15 s nas chamadas.

> **Em produção**, seria recomendável ainda: HTTPS obrigatório, token em cookie `HttpOnly` + `SameSite` (com proteção CSRF), refresh tokens com revogação, rate limiting em armazenamento compartilhado (ex.: Redis) e migrações de banco com Alembic.

---

## Decisões técnicas

- **FastAPI**: validação automática com Pydantic, injeção de dependências (usada para sessão de banco e usuário autenticado) e documentação Swagger gerada sem esforço extra.
- **Organização em camadas** (`config`, `database`, `models`, `schemas`, `security`, `dependencies`, `routers`): cada arquivo tem uma responsabilidade, o que facilita leitura e testes.
- **`PATCH` para atualização**: permite alterar só o status sem reenviar a tarefa inteira (é o que o select do card faz). `PUT` também é aceito por compatibilidade.
- **Status como enum** (`pendente`, `em_andamento`, `concluida`): evita valores inválidos no banco.
- **Frontend sem framework**: o escopo é pequeno, então JavaScript puro com módulos mantém o projeto leve, sem etapa de build e fácil de executar. O código é dividido em cliente HTTP, sessão, UI e controlador.
- **Datas em UTC** no backend, formatadas no fuso do navegador no frontend.

---

## Problemas comuns

| Sintoma | Solução |
|---------|---------|
| "Não foi possível conectar à API" | Verifique se o Terminal 1 está com o `uvicorn` rodando na porta 8000. |
| Erro de CORS no console do navegador | Abra o frontend em `http://localhost:5500`. Se usar outra porta, adicione-a em `CORS_ORIGINS` no `.env` e reinicie a API. |
| Página em branco / módulos não carregam | Não abra o `index.html` direto do disco; use `python -m http.server 5500`. |
| Fui deslogado depois de reiniciar a API | Defina `SECRET_KEY` no `.env` (passo 2.3). |
| "Muitas tentativas de login" | Aguarde 1 minuto. |
| `python` não encontrado | Use `python3` (Linux/macOS) ou `py` (Windows). |
| Mudei a porta da API | Atualize `API_URL` em `frontend/js/config.js` e o `connect-src` da tag CSP em `frontend/index.html`. |
