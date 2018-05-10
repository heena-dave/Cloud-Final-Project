"""empty message

Revision ID: 2a1f56ceda57
Revises: 34dada2362b1
Create Date: 2018-05-08 20:31:35.762846

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a1f56ceda57'
down_revision = '34dada2362b1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('displayProfilePicture', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'displayProfilePicture')
    # ### end Alembic commands ###
