"""CRUD de tarefas. Toda consulta é filtrada pelo usuário autenticado."""

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, select

from app.dependencies import CurrentUser, DbSession
from app.models import Task, TaskStatus, User
from app.schemas import TaskCreate, TaskList, TaskOut, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["Tarefas"])


def _get_owned_task(db: DbSession, task_id: int, user: User) -> Task:
    """Busca a tarefa garantindo que pertence ao usuário.

    Retorna 404 (e não 403) para tarefas de outros usuários, para não
    revelar que o id existe.
    """
    task = db.scalar(
        select(Task).where(Task.id == task_id, Task.usuario_id == user.id)
    )
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarefa não encontrada.",
        )
    return task


@router.get("", response_model=TaskList, summary="Listar tarefas")
def list_tasks(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: Annotated[
        TaskStatus | None, Query(alias="status", description="Filtra por status")
    ] = None,
    busca: Annotated[
        str | None,
        Query(max_length=100, description="Busca no título e na descrição"),
    ] = None,
    ordem: Annotated[
        Literal["recentes", "antigas"], Query(description="Ordenação")
    ] = "recentes",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TaskList:
    """Lista as tarefas do usuário com filtros e paginação."""
    query = select(Task).where(Task.usuario_id == current_user.id)
    if status_filter is not None:
        query = query.where(Task.status == status_filter)
    if busca and busca.strip():
        termo = f"%{busca.strip()}%"
        query = query.where(
            Task.titulo.ilike(termo) | Task.descricao.ilike(termo)
        )

    total = db.scalar(select(func.count()).select_from(query.subquery()))

    order = Task.data_criacao.desc() if ordem == "recentes" else (
        Task.data_criacao.asc()
    )
    items = db.scalars(
        query.order_by(order, Task.id.desc()).limit(limit).offset(offset)
    ).all()

    return TaskList(
        total=total or 0,
        limit=limit,
        offset=offset,
        items=[TaskOut.model_validate(t) for t in items],
    )


@router.post(
    "",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    summary="Criar tarefa",
)
def create_task(
    payload: TaskCreate, db: DbSession, current_user: CurrentUser
) -> Task:
    """Cria uma tarefa para o usuário autenticado."""
    task = Task(**payload.model_dump(), usuario_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskOut, summary="Detalhar tarefa")
def get_task(task_id: int, db: DbSession, current_user: CurrentUser) -> Task:
    """Retorna uma tarefa do usuário."""
    return _get_owned_task(db, task_id, current_user)


@router.patch(
    "/{task_id}", response_model=TaskOut, summary="Atualizar tarefa"
)
@router.put(
    "/{task_id}",
    response_model=TaskOut,
    summary="Atualizar tarefa",
    include_in_schema=False,
)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Task:
    """Atualiza parcialmente uma tarefa (só os campos enviados)."""
    task = _get_owned_task(db, task_id, current_user)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("titulo", "") is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O título não pode ser nulo.",
        )
    if changes.get("status", "") is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="O status não pode ser nulo.",
        )
    for field, value in changes.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir tarefa",
)
def delete_task(
    task_id: int, db: DbSession, current_user: CurrentUser
) -> Response:
    """Exclui uma tarefa do usuário."""
    task = _get_owned_task(db, task_id, current_user)
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
