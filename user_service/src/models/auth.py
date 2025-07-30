from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import uuid
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user_roles = db.relationship('UserRole', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password: str):
        """Hash and set the user's password."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the user's password."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def get_roles(self):
        """Get all roles assigned to this user."""
        return [ur.role for ur in self.user_roles]
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.get_roles())
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        for role in self.get_roles():
            if permission in role.permissions:
                return True
        return False
    
    def to_dict(self, include_roles=False):
        """Convert user to dictionary representation."""
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_roles:
            data['roles'] = [role.name for role in self.get_roles()]
        
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'


class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    permissions = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user_roles = db.relationship('UserRole', back_populates='role', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert role to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'permissions': self.permissions,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Role {self.name}>'


class UserRole(db.Model):
    __tablename__ = 'user_roles'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    role_id = db.Column(db.String(36), db.ForeignKey('roles.id'), primary_key=True)
    assigned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', back_populates='user_roles')
    role = db.relationship('Role', back_populates='user_roles')
    
    def __repr__(self):
        return f'<UserRole user_id={self.user_id} role_id={self.role_id}>'


class RefreshToken(db.Model):
    __tablename__ = 'refresh_tokens'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User')
    
    def is_expired(self) -> bool:
        """Check if the refresh token is expired."""
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)
    
    def is_valid(self) -> bool:
        """Check if the refresh token is valid (not expired and not revoked)."""
        return not self.is_revoked and not self.is_expired()
    
    def revoke(self):
        """Revoke the refresh token."""
        self.is_revoked = True
    
    def __repr__(self):
        return f'<RefreshToken {self.id}>'

