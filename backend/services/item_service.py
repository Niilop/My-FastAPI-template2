from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.database import Item
from backend.models.schemas import ItemWrite


def list_items(db: Session, owner_id: int, limit: int, offset: int) -> tuple[list[Item], int]:
    items = list(
        db.scalars(
            select(Item)
            .where(Item.owner_id == owner_id)
            .order_by(Item.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    total = db.scalar(select(func.count()).select_from(Item).where(Item.owner_id == owner_id))
    return items, total or 0


def get_item(db: Session, item_id: int, owner_id: int) -> Item | None:
    return db.scalar(select(Item).where(Item.id == item_id, Item.owner_id == owner_id))


def create_item(db: Session, owner_id: int, body: ItemWrite) -> Item:
    item = Item(owner_id=owner_id, **body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item: Item, body: ItemWrite) -> Item:
    item.title = body.title
    item.description = body.description
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item: Item) -> None:
    db.delete(item)
    db.commit()
