"""v0-version

Revision ID: 76c5657366bc
Revises: 
Create Date: 2025-11-08 17:04:17.977352+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '76c5657366bc'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    scope_enum = sa.Enum('GLOBAL', 'CUSTOMER', 'FRANCHISE', 'STORE', name='scopeenum')
    redeem_type_enum = sa.Enum('BRL', 'PERCENTAGE', 'FREE_SKU', name='redeemtypeenum')
    coupon_status_enum = sa.Enum('CREATED', 'ISSUED', 'RESERVED', 'REDEEMED', 'CANCELLED', 'EXPIRED', name='couponstatusenum')

    scope_enum.create(bind, checkfirst=True)
    redeem_type_enum.create(bind, checkfirst=True)
    coupon_status_enum.create(bind, checkfirst=True)

    op.create_table(
        'person',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cpf', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('location', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cpf')
    )

    op.create_table(
        'customer',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cnpj', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('contact_email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cnpj')
    )

    op.create_table(
        'franchise',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cnpj', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cnpj')
    )

    op.create_table(
        'store',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('franchise_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cnpj', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('location', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['franchise_id'], ['franchise.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cnpj')
    )

    op.create_table(
        'device',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('registration_code', sa.String(), nullable=False),
        sa.Column('public_key', postgresql.BYTEA(), nullable=True),
        sa.Column('last_seen_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['store_id'], ['store.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'category',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'app_user',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', sa.String(), server_default=sa.text("'USER'"), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('person_id')
    )

    op.create_table(
        'refresh_token',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', postgresql.BYTEA(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'store_staff',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['store_id'], ['store.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("role IN ('STORE_MANAGER', 'CASHIER')")
    )

    op.create_table(
        'customer_marketplace_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rules', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_id')
    )

    op.create_table(
        'point_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scope', sa.Enum('GLOBAL', 'CUSTOMER', 'FRANCHISE', 'STORE', name='scopeenum', create_type=False), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('franchise_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('points_per_brl', sa.Numeric(12, 4), nullable=True),
        sa.Column('expires_in_days', sa.Integer(), nullable=True),
        sa.Column('extra', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['franchise_id'], ['franchise.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['store_id'], ['store.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "(scope = 'CUSTOMER' AND customer_id IS NOT NULL AND franchise_id IS NULL AND store_id IS NULL) OR "
            "(scope = 'FRANCHISE' AND franchise_id IS NOT NULL AND store_id IS NULL) OR "
            "(scope = 'STORE' AND store_id IS NOT NULL) OR "
            "(scope = 'GLOBAL' AND customer_id IS NULL AND franchise_id IS NULL AND store_id IS NULL)"
        )
    )

    op.create_table(
        'point_transaction',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scope', sa.Enum('GLOBAL', 'CUSTOMER', 'FRANCHISE', 'STORE', name='scopeenum', create_type=False), nullable=False),
        sa.Column('scope_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('order_id', sa.String(length=50), nullable=True),
        sa.Column('delta', sa.Integer(), nullable=False),
        sa.Column('details', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['store_id'], ['store.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('delta <> 0')
    )

    op.create_table(
        'order',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('total_brl', sa.Numeric(12, 2), nullable=False),
        sa.Column('tax_brl', sa.Numeric(12, 2), server_default=sa.text('0'), nullable=False),
        sa.Column('items', postgresql.JSONB(), nullable=False),
        sa.Column('shipping', postgresql.JSONB(), nullable=True),
        sa.Column('checkout_ref', sa.String(), nullable=True),
        sa.Column('external_id', sa.String(), nullable=True),
        sa.Column('source', sa.String(), server_default=sa.text("'PDV'"), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['person_id'], ['person.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['store_id'], ['store.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'sku',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('brand', sa.String(), nullable=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('custom_metadata', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['category.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'coupon_type',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sku_specific', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('redeem_type', sa.Enum('BRL', 'PERCENTAGE', 'FREE_SKU', name='redeemtypeenum', create_type=False), nullable=False),
        sa.Column('discount_amount_brl', sa.Numeric(12, 2), nullable=True),
        sa.Column('discount_amount_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('valid_skus', postgresql.ARRAY(sa.String()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "(redeem_type = 'BRL' AND discount_amount_brl IS NOT NULL) OR "
            "(redeem_type = 'PERCENTAGE' AND discount_amount_percentage IS NOT NULL) OR "
            "(redeem_type = 'FREE_SKU' AND valid_skus IS NOT NULL)"
        )
    )

    op.create_table(
        'coupon_offer',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_scope', sa.Enum('GLOBAL', 'CUSTOMER', 'FRANCHISE', 'STORE', name='scopeenum', create_type=False), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('coupon_type_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_segment', postgresql.JSONB(), nullable=True),
        sa.Column('initial_quantity', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('current_quantity', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('max_per_customer', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('start_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('end_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['coupon_type_id'], ['coupon_type.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("entity_scope IN ('CUSTOMER', 'FRANCHISE', 'STORE')"),
        sa.CheckConstraint('current_quantity <= initial_quantity'),
        sa.CheckConstraint('initial_quantity >= 0'),
        sa.CheckConstraint('current_quantity >= 0')
    )

    op.create_table(
        'coupon',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('offer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('issued_to_person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code_hash', postgresql.BYTEA(), nullable=False),
        sa.Column('status', sa.Enum('CREATED', 'ISSUED', 'RESERVED', 'REDEEMED', 'CANCELLED', 'EXPIRED', name='couponstatusenum', create_type=False), server_default=sa.text("'ISSUED'::couponstatusenum"), nullable=False),
        sa.Column('issued_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('redeemed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('redeemed_store_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['offer_id'], ['coupon_offer.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['issued_to_person_id'], ['person.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['redeemed_store_id'], ['store.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('ISSUED', 'RESERVED', 'REDEEMED', 'CANCELLED', 'EXPIRED')")
    )

    op.create_table(
        'offer_asset',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('offer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('position', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['offer_id'], ['coupon_offer.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("kind IN ('BANNER', 'THUMB', 'DETAIL')")
    )

    op.create_table(
        'api_key',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('key_hash', postgresql.BYTEA(), nullable=False),
        sa.Column('scopes', postgresql.ARRAY(sa.String()), server_default=sa.text("'{}'::varchar[]"), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('revoked_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'idempotency_key',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('owner_scope', sa.String(), nullable=False),
        sa.Column('request_hash', postgresql.BYTEA(), nullable=False),
        sa.Column('response_body', postgresql.BYTEA(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )

    op.create_table(
        'rate_limit_counter',
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('window_start', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )

    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_device_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('target_table', sa.String(), nullable=True),
        sa.Column('target_id', sa.String(), nullable=True),
        sa.Column('before', postgresql.JSONB(), nullable=True),
        sa.Column('after', postgresql.JSONB(), nullable=True),
        sa.Column('ip', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['actor_device_id'], ['device.id']),
        sa.ForeignKeyConstraint(['actor_user_id'], ['app_user.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'outbox_event',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(), server_default=sa.text("'PENDING'"), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('sent_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('outbox_event')
    op.drop_table('audit_log')
    op.drop_table('rate_limit_counter')
    op.drop_table('idempotency_key')
    op.drop_table('api_key')
    op.drop_table('offer_asset')
    op.drop_table('coupon')
    op.drop_table('coupon_offer')
    op.drop_table('coupon_type')
    op.drop_table('sku')
    op.drop_table('order')
    op.drop_table('point_transaction')
    op.drop_table('point_rules')
    op.drop_table('customer_marketplace_rules')
    op.drop_table('store_staff')
    op.drop_table('refresh_token')
    op.drop_table('app_user')
    op.drop_table('category')
    op.drop_table('device')
    op.drop_table('store')
    op.drop_table('franchise')
    op.drop_table('customer')
    op.drop_table('person')

    bind = op.get_bind()
    coupon_status_enum = sa.Enum('CREATED', 'ISSUED', 'RESERVED', 'REDEEMED', 'CANCELLED', 'EXPIRED', name='couponstatusenum')
    redeem_type_enum = sa.Enum('BRL', 'PERCENTAGE', 'FREE_SKU', name='redeemtypeenum')
    scope_enum = sa.Enum('GLOBAL', 'CUSTOMER', 'FRANCHISE', 'STORE', name='scopeenum')

    coupon_status_enum.drop(bind, checkfirst=True)
    redeem_type_enum.drop(bind, checkfirst=True)
    scope_enum.drop(bind, checkfirst=True)
