"""balance + daily billing model

Revision ID: 0002_balance_billing
Revises: 0001_initial
Create Date: 2026-05-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_balance_billing"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("plan", sa.String(16), server_default="solo", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )
    op.add_column("users", sa.Column("last_billed_on", sa.Date(), nullable=True))

    op.alter_column(
        "orders",
        "tariff_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.add_column(
        "orders",
        sa.Column("kind", sa.String(16), server_default="topup", nullable=False),
    )
    op.execute("UPDATE orders SET tariff_id = NULL")
    op.execute("DELETE FROM tariffs")

    op.add_column("tariffs", sa.Column("code", sa.String(16), nullable=True))
    op.add_column(
        "tariffs",
        sa.Column("daily_rate_kopecks", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "tariffs",
        sa.Column("device_limit", sa.Integer(), server_default="1", nullable=False),
    )

    op.alter_column("tariffs", "duration_days", existing_type=sa.Integer(), nullable=True)
    op.alter_column("tariffs", "price_kopecks", existing_type=sa.BigInteger(), nullable=True)

    op.execute(
        """
        INSERT INTO tariffs
            (code, name, daily_rate_kopecks, device_limit, duration_days, price_kopecks, sort_order)
        VALUES
            ('solo',   'Solo',   700,  1, 0, 0, 10),
            ('family', 'Family', 1400, 5, 0, 0, 20)
        """
    )

    op.alter_column("tariffs", "code", existing_type=sa.String(16), nullable=False)
    op.alter_column(
        "tariffs", "daily_rate_kopecks", existing_type=sa.BigInteger(), nullable=False
    )
    op.create_unique_constraint("uq_tariffs_code", "tariffs", ["code"])


def downgrade() -> None:
    op.drop_column("orders", "kind")
    op.alter_column(
        "orders",
        "tariff_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.drop_constraint("uq_tariffs_code", "tariffs", type_="unique")
    op.execute("DELETE FROM tariffs")
    op.drop_column("tariffs", "device_limit")
    op.drop_column("tariffs", "daily_rate_kopecks")
    op.drop_column("tariffs", "code")
    op.alter_column("tariffs", "price_kopecks", existing_type=sa.BigInteger(), nullable=False)
    op.alter_column("tariffs", "duration_days", existing_type=sa.Integer(), nullable=False)

    op.drop_column("users", "last_billed_on")
    op.drop_column("users", "is_active")
    op.drop_column("users", "plan")
