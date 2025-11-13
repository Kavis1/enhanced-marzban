"""Enhanced Marzban features migration

Revision ID: 001_enhanced_features
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001_enhanced_features'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add enhanced features tables and columns"""
    
    # Add columns to existing admin table
    try:
        op.add_column('admins', sa.Column('two_factor_enabled', sa.Boolean(), nullable=False, default=False))
    except:
        pass  # Column might already exist
    
    # Add columns to existing users table
    try:
        op.add_column('users', sa.Column('max_connections', sa.Integer(), nullable=False, default=5))
        op.add_column('users', sa.Column('current_connections', sa.Integer(), nullable=False, default=0))
        op.add_column('users', sa.Column('fail2ban_violations', sa.Integer(), nullable=False, default=0))
        op.add_column('users', sa.Column('last_violation_at', sa.DateTime(), nullable=True))
        op.add_column('users', sa.Column('adblock_enabled', sa.Boolean(), nullable=False, default=True))
        op.add_column('users', sa.Column('custom_blocked_domains', sa.String(length=2000), nullable=True))
    except:
        pass  # Columns might already exist
    
    # Add columns to existing nodes table
    try:
        op.add_column('nodes', sa.Column('adblock_enabled', sa.Boolean(), nullable=False, default=False))
        op.add_column('nodes', sa.Column('adblock_lists', sa.Text(), nullable=True))
    except:
        pass  # Columns might already exist
    
    # Create admin_two_factor table
    op.create_table('admin_two_factor',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('secret_key', sa.String(length=32), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('backup_codes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('admin_id')
    )
    op.create_index(op.f('ix_admin_two_factor_id'), 'admin_two_factor', ['id'], unique=False)
    
    # Create traffic_violations table
    op.create_table('traffic_violations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('violation_type', sa.String(length=50), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_traffic_violations_id'), 'traffic_violations', ['id'], unique=False)
    op.create_index('idx_user_violation_time', 'traffic_violations', ['user_id', 'created_at'], unique=False)
    
    # Create connection_logs table
    op.create_table('connection_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('connection_id', sa.String(length=100), nullable=False),
        sa.Column('protocol', sa.String(length=20), nullable=False),
        sa.Column('inbound_tag', sa.String(length=50), nullable=False),
        sa.Column('connected_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('bytes_sent', sa.Integer(), nullable=True),
        sa.Column('bytes_received', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('node_id', sa.Integer(), nullable=True),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('disconnected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disconnect_reason', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('connection_id')
    )
    op.create_index(op.f('ix_connection_logs_id'), 'connection_logs', ['id'], unique=False)
    op.create_index('idx_user_connection_time', 'connection_logs', ['user_id', 'connected_at'], unique=False)
    op.create_index('idx_ip_connection_time', 'connection_logs', ['ip_address', 'connected_at'], unique=False)
    
    # Create dns_rules table
    op.create_table('dns_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('target_ip', sa.String(length=45), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dns_rules_domain'), 'dns_rules', ['domain'], unique=False)
    op.create_index(op.f('ix_dns_rules_id'), 'dns_rules', ['id'], unique=False)
    op.create_index('idx_domain_priority', 'dns_rules', ['domain', 'priority'], unique=False)
    
    # Create user_dns_rules table
    op.create_table('user_dns_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('target_ip', sa.String(length=45), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'domain', name='uq_user_domain')
    )
    op.create_index(op.f('ix_user_dns_rules_id'), 'user_dns_rules', ['id'], unique=False)
    op.create_index('idx_user_domain_priority', 'user_dns_rules', ['user_id', 'domain', 'priority'], unique=False)
    
    # Create dns_cache table
    op.create_table('dns_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('query_type', sa.String(length=10), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('ttl', sa.Integer(), nullable=True),
        sa.Column('cached_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('hit_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dns_cache_domain'), 'dns_cache', ['domain'], unique=False)
    op.create_index(op.f('ix_dns_cache_id'), 'dns_cache', ['id'], unique=False)
    
    # Create adblock_lists table
    op.create_table('adblock_lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('domain_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_adblock_lists_id'), 'adblock_lists', ['id'], unique=False)
    
    # Create adblock_domains table
    op.create_table('adblock_domains',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('list_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['list_id'], ['adblock_lists.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_adblock_domains_domain'), 'adblock_domains', ['domain'], unique=False)
    op.create_index(op.f('ix_adblock_domains_id'), 'adblock_domains', ['id'], unique=False)
    op.create_index('idx_domain_list', 'adblock_domains', ['domain', 'list_id'], unique=False)
    
    # Create service_status table
    op.create_table('service_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_name', sa.String(length=50), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('is_running', sa.Boolean(), nullable=True),
        sa.Column('last_check', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('last_restart', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('configuration', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('service_name')
    )
    op.create_index(op.f('ix_service_status_id'), 'service_status', ['id'], unique=False)
    
    # Create system_logs table
    op.create_table('system_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_name', sa.String(length=50), nullable=False),
        sa.Column('log_level', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_logs_id'), 'system_logs', ['id'], unique=False)
    op.create_index('idx_log_level_time', 'system_logs', ['log_level', 'created_at'], unique=False)
    op.create_index('idx_service_time', 'system_logs', ['service_name', 'created_at'], unique=False)
    
    # Create admin_login_attempts table
    op.create_table('admin_login_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('failure_reason', sa.String(length=100), nullable=True),
        sa.Column('two_factor_used', sa.Boolean(), nullable=True),
        sa.Column('attempted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_login_attempts_id'), 'admin_login_attempts', ['id'], unique=False)
    op.create_index(op.f('ix_admin_login_attempts_username'), 'admin_login_attempts', ['username'], unique=False)
    
    # Create admin_sessions table
    op.create_table('admin_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('two_factor_verified', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token')
    )
    op.create_index(op.f('ix_admin_sessions_id'), 'admin_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_admin_sessions_session_token'), 'admin_sessions', ['session_token'], unique=False)
    
    # Create performance_metrics table
    op.create_table('performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=50), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_unit', sa.String(length=20), nullable=True),
        sa.Column('node_id', sa.Integer(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_performance_metrics_id'), 'performance_metrics', ['id'], unique=False)
    op.create_index('idx_metric_time', 'performance_metrics', ['metric_name', 'recorded_at'], unique=False)


def downgrade():
    """Remove enhanced features tables and columns"""
    
    # Drop tables
    op.drop_table('performance_metrics')
    op.drop_table('admin_sessions')
    op.drop_table('admin_login_attempts')
    op.drop_table('system_logs')
    op.drop_table('service_status')
    op.drop_table('adblock_domains')
    op.drop_table('adblock_lists')
    op.drop_table('dns_cache')
    op.drop_table('user_dns_rules')
    op.drop_table('dns_rules')
    op.drop_table('connection_logs')
    op.drop_table('traffic_violations')
    op.drop_table('admin_two_factor')
    
    # Remove columns from existing tables
    try:
        op.drop_column('nodes', 'adblock_lists')
        op.drop_column('nodes', 'adblock_enabled')
        op.drop_column('users', 'custom_blocked_domains')
        op.drop_column('users', 'adblock_enabled')
        op.drop_column('users', 'last_violation_at')
        op.drop_column('users', 'fail2ban_violations')
        op.drop_column('users', 'current_connections')
        op.drop_column('users', 'max_connections')
        op.drop_column('admins', 'two_factor_enabled')
    except:
        pass  # Columns might not exist
