"""Initial Setup

Revision ID: 60ae78d374aa
Revises: 
Create Date: 2019-04-15 18:10:39.791299

"""
from alembic import op
import sqlalchemy as sa
import app


# revision identifiers, used by Alembic.
revision = "60ae78d374aa"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "tag",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "talk",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("speaker_name", sa.String(length=64), nullable=True),
        sa.Column("speaker_aboutme", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=True),
        sa.Column("is_organizer", sa.Boolean(), nullable=True),
        sa.Column("password_hash", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_index(op.f("ix_user_username"), "user", ["username"], unique=True)
    op.create_table(
        "collection",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_meta", sa.Boolean(), nullable=True),
        sa.Column("organizer_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["organizer_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "history_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "_type",
            sa.Enum("CREATE", "EDIT", "DELETE", name="historystates"),
            nullable=True,
        ),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("diff", app.serialization.DillField(), nullable=True),
        sa.Column("target_discriminator", sa.String(), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("target_name", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "talk_tags",
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("talk_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"]),
        sa.ForeignKeyConstraint(["talk_id"], ["talk.id"]),
        sa.PrimaryKeyConstraint("tag_id", "talk_id"),
    )
    op.create_table(
        "collection_editors",
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["collection.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("collection_id", "user_id"),
    )
    op.create_table(
        "meta_collection_connections",
        sa.Column("sub_collection_id", sa.Integer(), nullable=False),
        sa.Column("meta_collection_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["meta_collection_id"], ["collection.id"]),
        sa.ForeignKeyConstraint(["sub_collection_id"], ["collection.id"]),
        sa.PrimaryKeyConstraint("sub_collection_id", "meta_collection_id"),
    )
    op.create_table(
        "subscription",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("collection_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("remind_me", sa.Boolean(), nullable=True),
        sa.Column(
            "mode",
            sa.Enum("DAILY", "WEEKLY", "DAILY_AND_WEEKLY", name="modes"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["collection_id"], ["collection.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "talk_collections",
        sa.Column("talk_id", sa.Integer(), nullable=False),
        sa.Column("collection_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["collection.id"]),
        sa.ForeignKeyConstraint(["talk_id"], ["talk.id"]),
        sa.PrimaryKeyConstraint("talk_id", "collection_id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("talk_collections")
    op.drop_table("subscription")
    op.drop_table("meta_collection_connections")
    op.drop_table("collection_editors")
    op.drop_table("talk_tags")
    op.drop_table("history_item")
    op.drop_table("collection")
    op.drop_index(op.f("ix_user_username"), table_name="user")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
    op.drop_table("talk")
    op.drop_table("tag")
    # ### end Alembic commands ###
