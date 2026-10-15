"""Testes do CRUD de tarefas e do isolamento entre usuários."""

from tests.conftest import register


def _create(client, headers, **data):
    payload = {"titulo": "Estudar FastAPI", **data}
    response = client.post("/tasks", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_task_defaults(client, auth_headers):
    task = _create(client, auth_headers, descricao="Ler a documentação")
    assert task["id"] > 0
    assert task["titulo"] == "Estudar FastAPI"
    assert task["descricao"] == "Ler a documentação"
    assert task["status"] == "pendente"
    assert task["data_criacao"]


def test_create_task_validation(client, auth_headers):
    blank = client.post("/tasks", json={"titulo": "   "}, headers=auth_headers)
    bad_status = client.post(
        "/tasks", json={"titulo": "X", "status": "feito"}, headers=auth_headers
    )
    assert blank.status_code == 422
    assert bad_status.status_code == 422


def test_list_tasks_with_filters(client, auth_headers):
    _create(client, auth_headers, titulo="Comprar pão")
    _create(client, auth_headers, titulo="Pagar contas", status="concluida")
    _create(client, auth_headers, titulo="Lavar carro", status="em_andamento")

    all_tasks = client.get("/tasks", headers=auth_headers).json()
    assert all_tasks["total"] == 3
    assert all_tasks["items"][0]["titulo"] == "Lavar carro"  # mais recente

    done = client.get(
        "/tasks", params={"status": "concluida"}, headers=auth_headers
    ).json()
    assert [t["titulo"] for t in done["items"]] == ["Pagar contas"]

    search = client.get(
        "/tasks", params={"busca": "pão"}, headers=auth_headers
    ).json()
    assert search["total"] == 1


def test_update_task_partial(client, auth_headers):
    task = _create(client, auth_headers, descricao="original")
    response = client.patch(
        f"/tasks/{task['id']}",
        json={"status": "concluida"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "concluida"
    assert body["descricao"] == "original"
    assert body["titulo"] == task["titulo"]


def test_update_rejects_null_title(client, auth_headers):
    task = _create(client, auth_headers)
    response = client.patch(
        f"/tasks/{task['id']}", json={"titulo": None}, headers=auth_headers
    )
    assert response.status_code == 422


def test_delete_task(client, auth_headers):
    task = _create(client, auth_headers)
    response = client.delete(f"/tasks/{task['id']}", headers=auth_headers)
    assert response.status_code == 204
    missing = client.get(f"/tasks/{task['id']}", headers=auth_headers)
    assert missing.status_code == 404


def test_users_cannot_access_each_others_tasks(client, auth_headers):
    task = _create(client, auth_headers)
    other = register(client, email="bruno@example.com", nome="Bruno")

    assert client.get("/tasks", headers=other).json()["total"] == 0
    url = f"/tasks/{task['id']}"
    assert client.get(url, headers=other).status_code == 404
    assert client.patch(
        url, json={"titulo": "hack"}, headers=other
    ).status_code == 404
    assert client.delete(url, headers=other).status_code == 404

    # A tarefa original continua intacta para a dona.
    original = client.get(url, headers=auth_headers).json()
    assert original["titulo"] == "Estudar FastAPI"


def test_tasks_require_auth(client):
    assert client.get("/tasks").status_code == 401
    assert client.post("/tasks", json={"titulo": "x"}).status_code == 401
