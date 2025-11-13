"""
Enhanced database models for Marzban features
"""

import json
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text,
    BigInteger, Float, func, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class AdminTwoFactor(Base):
    """Two-Factor Authentication settings for admins"""
    __tablename__ = "admin_two_factor"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), unique=True, nullable=False)
    secret_key = Column(String(32), nullable=False)
    is_enabled = Column(Boolean, default=False)
    backup_codes = Column(Text, nullable=True)  # JSON array of backup codes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    admin = relationship("Admin", back_populates="two_factor")


class TrafficViolation(Base):
    """Traffic violations for fail2ban integration"""
    __tablename__ = "traffic_violations"
    __table_args__ = (
        Index('idx_user_violation_time', 'user_id', 'created_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    violation_type = Column(String(50), nullable=False)  # torrent, suspicious_activity, etc.
    ip_address = Column(String(45), nullable=False)
    details = Column(Text, nullable=True)  # JSON details
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class ConnectionLog(Base):
    """User connection tracking"""
    __tablename__ = "connection_logs"
    __table_args__ = (
        Index('idx_user_connection_time', 'user_id', 'connected_at'),
        Index('idx_ip_connection_time', 'ip_address', 'connected_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ip_address = Column(String(45), nullable=False)
    connection_id = Column(String(100), unique=True, nullable=False)
    protocol = Column(String(20), nullable=False)  # vmess, vless, trojan, etc.
    inbound_tag = Column(String(50), nullable=False)
    connected_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    bytes_sent = Column(Integer, default=0)
    bytes_received = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)
    user_agent = Column(String(512), nullable=True)
    disconnected_at = Column(DateTime(timezone=True), nullable=True)
    disconnect_reason = Column(String(100), nullable=True)


class DNSRule(Base):
    """Global DNS override rules"""
    __tablename__ = "dns_rules"
    __table_args__ = (
        Index('idx_domain_priority', 'domain', 'priority'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), nullable=False, index=True)
    target_ip = Column(String(45), nullable=False)
    priority = Column(Integer, default=100)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    description = Column(String(500), nullable=True)


class UserDNSRule(Base):
    """User-specific DNS override rules"""
    __tablename__ = "user_dns_rules"
    __table_args__ = (
        Index('idx_user_domain_priority', 'user_id', 'domain', 'priority'),
        UniqueConstraint('user_id', 'domain', name='uq_user_domain'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    domain = Column(String(255), nullable=False)
    target_ip = Column(String(45), nullable=False)
    priority = Column(Integer, default=100)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DNSCache(Base):
    """DNS query cache"""
    __tablename__ = "dns_cache"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), nullable=False, index=True)
    query_type = Column(String(10), nullable=False)
    response = Column(Text, nullable=False)
    ttl = Column(Integer, default=300)
    cached_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    hit_count = Column(Integer, default=1)


class AdBlockList(Base):
    """Ad-block lists configuration"""
    __tablename__ = "adblock_lists"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    url = Column(String(500), nullable=False)
    description = Column(String(500), nullable=True)
    is_enabled = Column(Boolean, default=True)
    last_updated = Column(DateTime(timezone=True), nullable=True)
    domain_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AdBlockDomain(Base):
    """Blocked domains from ad-block lists"""
    __tablename__ = "adblock_domains"
    __table_args__ = (
        Index('idx_domain_list', 'domain', 'list_id'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), nullable=False, index=True)
    list_id = Column(Integer, ForeignKey("adblock_lists.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ServiceStatus(Base):
    """Enhanced services status tracking"""
    __tablename__ = "service_status"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(50), unique=True, nullable=False)
    is_enabled = Column(Boolean, default=True)
    is_running = Column(Boolean, default=False)
    last_check = Column(DateTime(timezone=True), server_default=func.now())
    last_restart = Column(DateTime(timezone=True), nullable=True)
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    configuration = Column(Text, nullable=True)  # JSON configuration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class SystemLog(Base):
    """Enhanced system logging"""
    __tablename__ = "system_logs"
    __table_args__ = (
        Index('idx_log_level_time', 'log_level', 'created_at'),
        Index('idx_service_time', 'service_name', 'created_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(50), nullable=False)
    log_level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON details
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AdminLoginAttempt(Base):
    """Track admin login attempts for security"""
    __tablename__ = "admin_login_attempts"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True)  # nullable for failed attempts
    username = Column(String(100), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, default=False)
    failure_reason = Column(String(100), nullable=True)  # wrong_password, invalid_2fa, etc.
    two_factor_used = Column(Boolean, default=False)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    admin = relationship("Admin", back_populates="login_attempts")


class AdminSession(Base):
    """Enhanced admin session tracking"""
    __tablename__ = "admin_sessions"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    two_factor_verified = Column(Boolean, default=False)


class PerformanceMetric(Base):
    """System performance metrics"""
    __tablename__ = "performance_metrics"
    __table_args__ = (
        Index('idx_metric_time', 'metric_name', 'recorded_at'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    details = Column(Text, nullable=True)  # JSON details
