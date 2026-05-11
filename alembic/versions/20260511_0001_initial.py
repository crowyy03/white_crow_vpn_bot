"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-11
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(64)),
        sa.Column("first_name", sa.String(128)),
        sa.Column("language_code", sa.String(8), server_default="ru"),
        sa.Column("remnawave_uuid", postgresql.UUID(as_uuid=True)),
        sa.Column("remnawave_short_uuid", sa.String(32)),
        sa.Column("subscription_url", sa.Text()),
        sa.Column("subscription_until", sa.DateTime(timezone=True)),
        sa.Column("traffic_limit_bytes", sa.BigInteger()),
        sa.Column("trial_used", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("referrer_id", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("balance_kopecks", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("is_banned", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "tariffs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("price_kopecks", sa.BigInteger(), nullable=False),
        sa.Column("price_stars", sa.Integer()),
        sa.Column("traffic_limit_bytes", sa.BigInteger()),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("tariff_id", sa.Integer(), sa.ForeignKey("tariffs.id")),
        sa.Column("amount_kopecks", sa.BigInteger(), nullable=False),
        sa.Column("promo_code", sa.String(32)),
        sa.Column("discount_kopecks", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("payment_method", sa.String(32)),
        sa.Column("payment_external_id", sa.String(128)),
        sa.Column("payment_url", sa.Text()),
        sa.Column("status", sa.String(32), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_orders_status", "orders", ["status"])
    op.create_index("idx_orders_payment_external_id", "orders", ["payment_external_id"])
    op.create_index("ix_orders_user_id", "orders", ["user_id"])

    op.create_table(
        "promocodes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("discount_percent", sa.Integer()),
        sa.Column("discount_fixed_kopecks", sa.BigInteger()),
        sa.Column("bonus_days", sa.Integer()),
        sa.Column("usage_limit", sa.Integer()),
        sa.Column("used_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "referrals",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("referrer_id", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("referred_id", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("bonus_paid_kopecks", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "notifications_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("type", sa.String(64)),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_log_user_id", "notifications_log", ["user_id"])

    op.execute(
        """
        INSERT INTO tariffs (name, duration_days, price_kopecks, price_stars, sort_order)
        VALUES
            ('1 месяц',  30,  29900,  150, 10),
            ('3 месяца', 90,  79900,  400, 20),
            ('6 месяцев',180, 149900, 750, 30),
            ('12 месяцев',365,269900, 1300, 40)
        """
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_log_user_id", table_name="notifications_log")
    op.drop_table("notifications_log")
    op.drop_table("referrals")
    op.drop_table("promocodes")
    op.drop_index("ix_orders_user_id", table_name="orders")
    op.drop_index("idx_orders_payment_external_id", table_name="orders")
    op.drop_index("idx_orders_status", table_name="orders")
    op.drop_table("orders")
    op.drop_table("tariffs")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
