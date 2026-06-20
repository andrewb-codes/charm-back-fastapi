"""create profile table

Revision ID: 9bef997f9dfc
Revises:
Create Date: 2026-06-20 13:52:57.740004

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9bef997f9dfc"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

gender_enum = postgresql.ENUM(
    "MALE", "FEMALE", "OTHER", name="gender", create_type=False
)
status_enum = postgresql.ENUM("ACTIVE", "INACTIVE", name="status", create_type=False)
role_enum = postgresql.ENUM("ADMIN", "USER", name="role", create_type=False)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    gender_enum.create(bind, checkfirst=True)
    status_enum.create(bind, checkfirst=True)
    role_enum.create(bind, checkfirst=True)

    op.create_table(
        "profile",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("surname", sa.String(), nullable=True),
        sa.Column("birthdate", sa.Date(), nullable=True),
        sa.Column("about", sa.Text(), nullable=True),
        sa.Column("gender", gender_enum, nullable=True),
        sa.Column("photo", sa.String(), nullable=True),
        sa.Column(
            "status",
            status_enum,
            server_default="INACTIVE",
            nullable=False,
        ),
        sa.Column(
            "role",
            role_enum,
            server_default="USER",
            nullable=False,
        ),
        sa.Column(
            "created_date",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), server_default="0", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_profile_email"), "profile", ["email"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_profile_email"), table_name="profile")
    op.drop_table("profile")

    bind = op.get_bind()
    role_enum.drop(bind, checkfirst=True)
    status_enum.drop(bind, checkfirst=True)
    gender_enum.drop(bind, checkfirst=True)
