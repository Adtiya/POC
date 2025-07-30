from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import secrets
import hashlib
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
from src.models.auth import User, Role, UserRole, RefreshToken, db
from src.schemas.auth import UserCreateSchema, LoginRequestSchema, UserResponseSchema


class AuthService:
    """Service class for handling authentication operations."""
    
    @staticmethod
    def register_user(user_data: UserCreateSchema) -> Dict[str, Any]:
        """Register a new user."""
        try:
            # Check if user already exists
            existing_user = User.query.filter(
                (User.email == user_data.email) | (User.username == user_data.username)
            ).first()
            
            if existing_user:
                if existing_user.email == user_data.email:
                    return {"success": False, "error": "Email already registered"}
                else:
                    return {"success": False, "error": "Username already taken"}
            
            # Create new user
            user = User(
                email=user_data.email,
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name
            )
            user.set_password(user_data.password)
            
            db.session.add(user)
            
            # Assign default user role
            default_role = Role.query.filter_by(name='user').first()
            if default_role:
                user_role = UserRole(user_id=user.id, role_id=default_role.id)
                db.session.add(user_role)
            
            db.session.commit()
            
            return {
                "success": True,
                "user": user.to_dict(include_roles=True),
                "message": "User registered successfully"
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Registration failed: {str(e)}"}
    
    @staticmethod
    def authenticate_user(login_data: LoginRequestSchema) -> Dict[str, Any]:
        """Authenticate user and return tokens."""
        try:
            # Find user by email
            user = User.query.filter_by(email=login_data.email).first()
            
            if not user or not user.check_password(login_data.password):
                return {"success": False, "error": "Invalid email or password"}
            
            if not user.is_active:
                return {"success": False, "error": "Account is deactivated"}
            
            # Create tokens
            access_token = create_access_token(
                identity=user.id,
                additional_claims={
                    "email": user.email,
                    "username": user.username,
                    "roles": [role.name for role in user.get_roles()]
                }
            )
            
            refresh_token = create_refresh_token(identity=user.id)
            
            # Store refresh token in database
            refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            refresh_token_obj = RefreshToken(
                user_id=user.id,
                token_hash=refresh_token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7)
            )
            db.session.add(refresh_token_obj)
            db.session.commit()
            
            return {
                "success": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 1800,  # 30 minutes
                "user": user.to_dict(include_roles=True)
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Authentication failed: {str(e)}"}
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        try:
            # Decode refresh token to get user ID
            decoded_token = decode_token(refresh_token)
            user_id = decoded_token['sub']
            
            # Check if refresh token exists and is valid
            refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            stored_token = RefreshToken.query.filter_by(
                user_id=user_id,
                token_hash=refresh_token_hash
            ).first()
            
            if not stored_token or not stored_token.is_valid():
                return {"success": False, "error": "Invalid or expired refresh token"}
            
            # Get user
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return {"success": False, "error": "User not found or inactive"}
            
            # Create new access token
            access_token = create_access_token(
                identity=user.id,
                additional_claims={
                    "email": user.email,
                    "username": user.username,
                    "roles": [role.name for role in user.get_roles()]
                }
            )
            
            # Create new refresh token
            new_refresh_token = create_refresh_token(identity=user.id)
            
            # Revoke old refresh token and create new one
            stored_token.revoke()
            new_refresh_token_hash = hashlib.sha256(new_refresh_token.encode()).hexdigest()
            new_refresh_token_obj = RefreshToken(
                user_id=user.id,
                token_hash=new_refresh_token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7)
            )
            db.session.add(new_refresh_token_obj)
            db.session.commit()
            
            return {
                "success": True,
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": 1800
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Token refresh failed: {str(e)}"}
    
    @staticmethod
    def logout_user(refresh_token: str) -> Dict[str, Any]:
        """Logout user by revoking refresh token."""
        try:
            refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            stored_token = RefreshToken.query.filter_by(token_hash=refresh_token_hash).first()
            
            if stored_token:
                stored_token.revoke()
                db.session.commit()
            
            return {"success": True, "message": "Logged out successfully"}
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Logout failed: {str(e)}"}
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID."""
        return User.query.get(user_id)
    
    @staticmethod
    def update_user_password(user_id: str, current_password: str, new_password: str) -> Dict[str, Any]:
        """Update user password."""
        try:
            user = User.query.get(user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            if not user.check_password(current_password):
                return {"success": False, "error": "Current password is incorrect"}
            
            user.set_password(new_password)
            user.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            return {"success": True, "message": "Password updated successfully"}
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Password update failed: {str(e)}"}
    
    @staticmethod
    def create_default_roles():
        """Create default roles if they don't exist."""
        try:
            default_roles = [
                {
                    "name": "admin",
                    "description": "Administrator with full system access",
                    "permissions": {
                        "users": ["create", "read", "update", "delete"],
                        "roles": ["create", "read", "update", "delete"],
                        "system": ["manage", "configure"]
                    }
                },
                {
                    "name": "user",
                    "description": "Standard user with basic access",
                    "permissions": {
                        "profile": ["read", "update"],
                        "llm": ["use"],
                        "analytics": ["view"]
                    }
                },
                {
                    "name": "analyst",
                    "description": "Data analyst with analytics access",
                    "permissions": {
                        "profile": ["read", "update"],
                        "analytics": ["create", "read", "update", "delete"],
                        "reports": ["create", "read", "update", "delete"]
                    }
                }
            ]
            
            for role_data in default_roles:
                existing_role = Role.query.filter_by(name=role_data["name"]).first()
                if not existing_role:
                    role = Role(
                        name=role_data["name"],
                        description=role_data["description"],
                        permissions=role_data["permissions"]
                    )
                    db.session.add(role)
            
            db.session.commit()
            return {"success": True, "message": "Default roles created successfully"}
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Failed to create default roles: {str(e)}"}


class RoleService:
    """Service class for handling role operations."""
    
    @staticmethod
    def create_role(name: str, description: str = None, permissions: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new role."""
        try:
            existing_role = Role.query.filter_by(name=name).first()
            if existing_role:
                return {"success": False, "error": "Role already exists"}
            
            role = Role(
                name=name,
                description=description,
                permissions=permissions or {}
            )
            db.session.add(role)
            db.session.commit()
            
            return {
                "success": True,
                "role": role.to_dict(),
                "message": "Role created successfully"
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Role creation failed: {str(e)}"}
    
    @staticmethod
    def get_all_roles():
        """Get all roles."""
        roles = Role.query.all()
        return [role.to_dict() for role in roles]
    
    @staticmethod
    def get_role_by_id(role_id: str) -> Optional[Role]:
        """Get role by ID."""
        return Role.query.get(role_id)
    
    @staticmethod
    def assign_role_to_user(user_id: str, role_id: str) -> Dict[str, Any]:
        """Assign role to user."""
        try:
            user = User.query.get(user_id)
            role = Role.query.get(role_id)
            
            if not user:
                return {"success": False, "error": "User not found"}
            if not role:
                return {"success": False, "error": "Role not found"}
            
            # Check if user already has this role
            existing_assignment = UserRole.query.filter_by(
                user_id=user_id, role_id=role_id
            ).first()
            
            if existing_assignment:
                return {"success": False, "error": "User already has this role"}
            
            user_role = UserRole(user_id=user_id, role_id=role_id)
            db.session.add(user_role)
            db.session.commit()
            
            return {"success": True, "message": "Role assigned successfully"}
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Role assignment failed: {str(e)}"}
    
    @staticmethod
    def remove_role_from_user(user_id: str, role_id: str) -> Dict[str, Any]:
        """Remove role from user."""
        try:
            user_role = UserRole.query.filter_by(
                user_id=user_id, role_id=role_id
            ).first()
            
            if not user_role:
                return {"success": False, "error": "User does not have this role"}
            
            db.session.delete(user_role)
            db.session.commit()
            
            return {"success": True, "message": "Role removed successfully"}
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Role removal failed: {str(e)}"}

