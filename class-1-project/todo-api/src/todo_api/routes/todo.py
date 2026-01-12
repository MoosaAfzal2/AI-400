"""Todo API routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..error_handler import create_error_response
from ..exceptions import ResourceNotFoundException
from ..schemas import TodoCreate, TodoListResponse, TodoResponse, TodoUpdate
from ..services import TodoService

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
    session: AsyncSession = Depends(get_session),
    user_id: int = Query(..., description="User ID (authenticated user)"),
) -> TodoResponse:
    """Create new todo for authenticated user.

    Args:
        data: Todo creation request
        session: Database session
        user_id: Authenticated user ID

    Returns:
        Created TodoResponse

    Raises:
        ValidationException: If validation fails
    """
    try:
        todo_service = TodoService(session)
        todo = await todo_service.create_todo(
            user_id=user_id,
            title=data.title,
            description=data.description,
        )
        await todo_service.commit()

        return TodoResponse.from_attributes(todo)

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
    session: AsyncSession = Depends(get_session),
    user_id: int = Query(..., description="User ID (authenticated user)"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    is_completed: bool | None = Query(None, description="Filter by completion status"),
    sort_by: str = Query(
        "created_at",
        regex="^(created_at|updated_at|title)$",
        description="Field to sort by",
    ),
    sort_order: str = Query(
        "desc",
        regex="^(asc|desc)$",
        description="Sort order",
    ),
) -> TodoListResponse:
    """List todos for authenticated user with pagination and filtering.

    Args:
        session: Database session
        user_id: Authenticated user ID
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
        todo_service = TodoService(session)
        todos, total = await todo_service.list_todos(
            user_id=user_id,
            skip=skip,
            limit=limit,
            is_completed=is_completed,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return TodoListResponse(
            items=[TodoResponse.from_attributes(todo) for todo in todos],
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
    session: AsyncSession = Depends(get_session),
    user_id: int = Query(..., description="User ID (authenticated user)"),
) -> TodoResponse:
    """Get single todo by ID for authenticated user.

    Args:
        todo_id: Todo ID
        session: Database session
        user_id: Authenticated user ID

    Returns:
        TodoResponse

    Raises:
        HTTPException: If todo not found or user doesn't own it
    """
    try:
        todo_service = TodoService(session)
        todo = await todo_service.get_todo(todo_id, user_id)

        if not todo:
            error_response = create_error_response(
                error_code="NOT_FOUND_002",
                message="Todo not found",
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response.model_dump(),
            )

        return TodoResponse.from_attributes(todo)

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
    session: AsyncSession = Depends(get_session),
    user_id: int = Query(..., description="User ID (authenticated user)"),
) -> TodoResponse:
    """Update todo for authenticated user.

    Args:
        todo_id: Todo ID
        data: Todo update request
        session: Database session
        user_id: Authenticated user ID

    Returns:
        Updated TodoResponse

    Raises:
        HTTPException: If todo not found or user doesn't own it
    """
    try:
        todo_service = TodoService(session)
        todo = await todo_service.update_todo(
            todo_id=todo_id,
            user_id=user_id,
            **data.model_dump(exclude_unset=True),
        )
        await todo_service.commit()

        return TodoResponse.from_attributes(todo)

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
    session: AsyncSession = Depends(get_session),
    user_id: int = Query(..., description="User ID (authenticated user)"),
) -> None:
    """Delete todo for authenticated user.

    Args:
        todo_id: Todo ID
        session: Database session
        user_id: Authenticated user ID

    Raises:
        HTTPException: If todo not found or user doesn't own it
    """
    try:
        todo_service = TodoService(session)
        await todo_service.delete_todo(todo_id, user_id)
        await todo_service.commit()

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
