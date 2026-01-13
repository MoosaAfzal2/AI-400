"""Todo API routes."""

from fastapi import APIRouter, HTTPException, Query, status

from ..dependencies import (
    CurrentUserDep,
    SessionDep,
    TodoServiceDep,
)
from ..error_handler import create_error_response
from ..exceptions import ResourceNotFoundException
from ..schemas import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate

router = APIRouter(prefix="/api/v1/todos", tags=["todos"])


@router.post(
    "",
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        422: {"description": "Validation failed"},
    },
)
async def create_todo(
    data: TodoCreate,
    current_user: CurrentUserDep,
    todo_service: TodoServiceDep,
    session: SessionDep,
) -> TodoResponse:
    """Create new todo for authenticated user.

    Args:
        data: Todo creation request
        current_user: Authenticated user from JWT token
        todo_service: Injected todo service
        session: Database session

    Returns:
        Created TodoResponse

    Raises:
        ValidationException: If validation fails
    """
    try:
        todo = await todo_service.create_todo(
            user_id=current_user.id,
            title=data.title,
            description=data.description,
        )
        await session.commit()

        return TodoResponse.model_validate(todo, from_attributes=True)

    except Exception as exc:
        await session.rollback()
        error_response = create_error_response(
            error_code="SERVER_001",
            message="Failed to create todo",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )


@router.get(
    "",
    response_model=TodoListResponse,
    responses={
        400: {"description": "Invalid query parameters"},
    },
)
async def list_todos(
    current_user: CurrentUserDep,
    todo_service: TodoServiceDep,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    is_completed: bool | None = Query(None, description="Filter by completion status"),
    sort_by: str = Query(
        "created_at",
        pattern="^(created_at|updated_at|title)$",
        description="Field to sort by",
    ),
    sort_order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
        description="Sort order",
    ),
) -> TodoListResponse:
    """List todos for authenticated user with pagination and filtering.

    Args:
        current_user: Authenticated user from JWT token
        todo_service: Injected todo service
        skip: Number of items to skip
        limit: Number of items to return
        is_completed: Optional filter by completion status
        sort_by: Field to sort by
        sort_order: Sort order (asc or desc)

    Returns:
        TodoListResponse with paginated todos

    Raises:
        HTTPException: If query invalid
    """
    try:
        todos, total = await todo_service.list_todos(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            is_completed=is_completed,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return TodoListResponse(
            items=[TodoResponse.model_validate(todo, from_attributes=True) for todo in todos],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    except Exception as exc:
        error_response = create_error_response(
            error_code="VALIDATION_001",
            message="Invalid query parameters",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response.model_dump(),
        )


@router.get(
    "/{todo_id}",
    response_model=TodoResponse,
    responses={
        404: {"description": "Todo not found"},
    },
)
async def get_todo(
    todo_id: int,
    current_user: CurrentUserDep,
    todo_service: TodoServiceDep,
) -> TodoResponse:
    """Get single todo by ID for authenticated user.

    Args:
        todo_id: Todo ID
        current_user: Authenticated user from JWT token
        todo_service: Injected todo service

    Returns:
        TodoResponse

    Raises:
        HTTPException: If todo not found or user doesn't own it
    """
    try:
        todo = await todo_service.get_todo(todo_id, current_user.id)

        if not todo:
            error_response = create_error_response(
                error_code="NOT_FOUND_002",
                message="Todo not found",
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response.model_dump(),
            )

        return TodoResponse.model_validate(todo, from_attributes=True)

    except HTTPException:
        raise
    except Exception as exc:
        error_response = create_error_response(
            error_code="SERVER_001",
            message="Failed to retrieve todo",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )


@router.put(
    "/{todo_id}",
    response_model=TodoResponse,
    responses={
        404: {"description": "Todo not found"},
        422: {"description": "Validation failed"},
    },
)
async def update_todo(
    todo_id: int,
    data: TodoUpdate,
    current_user: CurrentUserDep,
    todo_service: TodoServiceDep,
    session: SessionDep,
) -> TodoResponse:
    """Update todo for authenticated user.

    Args:
        todo_id: Todo ID
        data: Todo update request
        current_user: Authenticated user from JWT token
        todo_service: Injected todo service
        session: Database session

    Returns:
        Updated TodoResponse

    Raises:
        HTTPException: If todo not found or user doesn't own it
    """
    try:
        todo = await todo_service.update_todo(
            todo_id=todo_id,
            user_id=current_user.id,
            **data.model_dump(exclude_unset=True),
        )
        await session.commit()

        return TodoResponse.model_validate(todo, from_attributes=True)

    except ResourceNotFoundException as exc:
        await session.rollback()
        error_response = create_error_response(
            error_code=exc.error_code,
            message=exc.message,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response.model_dump(),
        )
    except Exception as exc:
        await session.rollback()
        error_response = create_error_response(
            error_code="SERVER_001",
            message="Failed to update todo",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )


@router.delete(
    "/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Todo not found"},
    },
)
async def delete_todo(
    todo_id: int,
    current_user: CurrentUserDep,
    todo_service: TodoServiceDep,
    session: SessionDep,
) -> None:
    """Delete todo for authenticated user.

    Args:
        todo_id: Todo ID
        current_user: Authenticated user from JWT token
        todo_service: Injected todo service
        session: Database session

    Raises:
        HTTPException: If todo not found or user doesn't own it
    """
    try:
        await todo_service.delete_todo(todo_id, current_user.id)
        await session.commit()

    except ResourceNotFoundException as exc:
        await session.rollback()
        error_response = create_error_response(
            error_code=exc.error_code,
            message=exc.message,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response.model_dump(),
        )
    except Exception as exc:
        await session.rollback()
        error_response = create_error_response(
            error_code="SERVER_001",
            message="Failed to delete todo",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.model_dump(),
        )
