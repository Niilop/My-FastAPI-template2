"""Replace the catalog with generic items, retaining names, owners, and timestamps."""

import sqlalchemy as sa
from alembic import op

revision = "0002_items"
down_revision = "0001_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_data_catalogs_user_id", table_name="data_catalogs")
    op.rename_table("data_catalogs", "items")
    with op.batch_alter_table("items") as batch:
        batch.alter_column("user_id", new_column_name="owner_id")
        batch.alter_column("name", new_column_name="title")
        batch.drop_column("file_path")
        batch.drop_column("data_metadata")
    op.create_index("ix_items_owner_id", "items", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_items_owner_id", table_name="items")
    with op.batch_alter_table("items") as batch:
        batch.alter_column("owner_id", new_column_name="user_id")
        batch.alter_column("title", new_column_name="name")
        # The removed file paths and profiling metadata cannot be reconstructed.
        batch.add_column(sa.Column("file_path", sa.String(500), nullable=False, server_default=""))
        batch.add_column(sa.Column("data_metadata", sa.JSON(), nullable=False, server_default="{}"))
    with op.batch_alter_table("items") as batch:
        batch.alter_column("file_path", server_default=None)
        batch.alter_column("data_metadata", server_default=None)
    op.rename_table("items", "data_catalogs")
    op.create_index("ix_data_catalogs_user_id", "data_catalogs", ["user_id"])
