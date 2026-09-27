from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response
from sqlalchemy.orm import Session

from backend.api.endpoints.auth import get_current_user
from backend.core.database import get_db
from backend.core.rate_limit import limiter
from backend.models.database import Item, User
from backend.models.schemas import ItemListResponse, ItemResponse, ItemWrite
from backend.services import item_service

router = APIRouter(prefix="/items", tags=["Items"])


def get_owned_item(
    item_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Item:
    item = item_service.get_item(db, item_id, current_user.id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("", response_model=ItemListResponse)
def list_items(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ItemListResponse:
    items, total = item_service.list_items(db, current_user.id, limit, offset)
    return ItemListResponse(
        items=[ItemResponse.model_validate(item) for item in items], total=total
    )


@router.post("", response_model=ItemResponse, status_code=201)
@limiter.limit("30/minute")
def create_item(
    request: Request,
    body: ItemWrite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Item:
    return item_service.create_item(db, current_user.id, body)


@router.get("/{item_id}", response_model=ItemResponse)
def read_item(item: Item = Depends(get_owned_item)) -> Item:
    return item


@router.put("/{item_id}", response_model=ItemResponse)
@limiter.limit("30/minute")
def update_item(
    request: Request,
    body: ItemWrite,
    item: Item = Depends(get_owned_item),
    db: Session = Depends(get_db),
) -> Item:
    return item_service.update_item(db, item, body)


@router.delete("/{item_id}", status_code=204)
@limiter.limit("30/minute")
def delete_item(
    request: Request,
    item: Item = Depends(get_owned_item),
    db: Session = Depends(get_db),
) -> Response:
    item_service.delete_item(db, item)
    return Response(status_code=204)
