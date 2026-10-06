"""Initial migration

Revision ID: 237782681b29
Revises: 
Create Date: 2026-10-01 19:42:10.579082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '237782681b29'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('lead',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lead_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('annual_revenue', sa.Float(), nullable=True),
    sa.Column('budget', sa.Float(), nullable=True),
    sa.Column('deal_value', sa.Float(), nullable=True),
    sa.Column('industry', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('company_size', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('lead_source', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('opportunity_stage', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lead_lead_id'), 'lead', ['lead_id'], unique=True)
    
    op.create_table('interaction',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lead_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('interaction_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interaction_lead_id'), 'interaction', ['lead_id'], unique=False)
    
    op.create_table('prediction',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lead_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('conversion_probability', sa.Float(), nullable=False),
    sa.Column('lead_score', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prediction_lead_id'), 'prediction', ['lead_id'], unique=False)
    
    op.create_table('recommendation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lead_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('recommended_action', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('recommendation_confidence', sa.Float(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recommendation_lead_id'), 'recommendation', ['lead_id'], unique=False)
    
    op.create_table('feedback',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lead_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('original_action', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('override_action', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('reason', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('actor_context', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedback_lead_id'), 'feedback', ['lead_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_feedback_lead_id'), table_name='feedback')
    op.drop_table('feedback')
    op.drop_index(op.f('ix_recommendation_lead_id'), table_name='recommendation')
    op.drop_table('recommendation')
    op.drop_index(op.f('ix_prediction_lead_id'), table_name='prediction')
    op.drop_table('prediction')
    op.drop_index(op.f('ix_interaction_lead_id'), table_name='interaction')
    op.drop_table('interaction')
    op.drop_index(op.f('ix_lead_lead_id'), table_name='lead')
    op.drop_table('lead')
