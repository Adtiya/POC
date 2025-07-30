from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from pydantic import ValidationError
from src.services.auth_service import AuthService, RoleService
from src.schemas.auth import (
    UserCreateSchema, LoginRequestSchema, TokenRefreshSchema,
    PasswordChangeSchema, RoleCreateSchema, UserRoleAssignSchema,
    ErrorResponseSchema, SuccessResponseSchema
)

auth_bp = Blueprint('auth', __name__)


def validate_json_data(schema_class, data):
    """Validate JSON data against Pydantic schema."""
    try:
        return schema_class(**data), None
    except ValidationError as e:
        return None, {"error": "Validation failed", "details": e.errors()}


@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        user_data, error = validate_json_data(UserCreateSchema, data)
        if error:
            return jsonify(error), 400
        
        result = AuthService.register_user(user_data)
        
        if result["success"]:
            return jsonify({
                "message": result["message"],
                "user": result["user"]
            }), 201
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """Authenticate user and return tokens."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        login_data, error = validate_json_data(LoginRequestSchema, data)
        if error:
            return jsonify(error), 400
        
        result = AuthService.authenticate_user(login_data)
        
        if result["success"]:
            return jsonify({
                "access_token": result["access_token"],
                "refresh_token": result["refresh_token"],
                "token_type": result["token_type"],
                "expires_in": result["expires_in"],
                "user": result["user"]
            }), 200
        else:
            return jsonify({"error": result["error"]}), 401
            
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@auth_bp.route('/auth/refresh', methods=['POST'])
def refresh():
    """Refresh access token."""
    try:
        data = request.get_json()
        if not data or 'refresh_token' not in data:
            return jsonify({"error": "Refresh token required"}), 400
        
        refresh_data, error = validate_json_data(TokenRefreshSchema, data)
        if error:
            return jsonify(error), 400
        
        result = AuthService.refresh_access_token(refresh_data.refresh_token)
        
        if result["success"]:
            return jsonify({
                "access_token": result["access_token"],
                "refresh_token": result["refresh_token"],
                "token_type": result["token_type"],
                "expires_in": result["expires_in"]
            }), 200
        else:
            return jsonify({"error": result["error"]}), 401
            
    except Exception as e:
        return jsonify({"error": f"Token refresh failed: {str(e)}"}), 500


@auth_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user by revoking refresh token."""
    try:
        data = request.get_json()
        if not data or 'refresh_token' not in data:
            return jsonify({"error": "Refresh token required"}), 400
        
        result = AuthService.logout_user(data['refresh_token'])
        
        if result["success"]:
            return jsonify({"message": result["message"]}), 200
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500


@auth_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information."""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify(user.to_dict(include_roles=True)), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get user info: {str(e)}"}), 500


@auth_bp.route('/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        password_data, error = validate_json_data(PasswordChangeSchema, data)
        if error:
            return jsonify(error), 400
        
        result = AuthService.update_user_password(
            user_id, 
            password_data.current_password, 
            password_data.new_password
        )
        
        if result["success"]:
            return jsonify({"message": result["message"]}), 200
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": f"Password change failed: {str(e)}"}), 500


# Role management endpoints
@auth_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_roles():
    """Get all roles."""
    try:
        # Check if user has permission to view roles
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        
        if 'admin' not in user_roles:
            return jsonify({"error": "Insufficient permissions"}), 403
        
        roles = RoleService.get_all_roles()
        return jsonify({"roles": roles}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get roles: {str(e)}"}), 500


@auth_bp.route('/roles', methods=['POST'])
@jwt_required()
def create_role():
    """Create a new role."""
    try:
        # Check if user has permission to create roles
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        
        if 'admin' not in user_roles:
            return jsonify({"error": "Insufficient permissions"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        role_data, error = validate_json_data(RoleCreateSchema, data)
        if error:
            return jsonify(error), 400
        
        result = RoleService.create_role(
            role_data.name,
            role_data.description,
            role_data.permissions
        )
        
        if result["success"]:
            return jsonify({
                "message": result["message"],
                "role": result["role"]
            }), 201
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": f"Role creation failed: {str(e)}"}), 500


@auth_bp.route('/users/<user_id>/roles/<role_id>', methods=['POST'])
@jwt_required()
def assign_role_to_user(user_id, role_id):
    """Assign role to user."""
    try:
        # Check if user has permission to assign roles
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        
        if 'admin' not in user_roles:
            return jsonify({"error": "Insufficient permissions"}), 403
        
        result = RoleService.assign_role_to_user(user_id, role_id)
        
        if result["success"]:
            return jsonify({"message": result["message"]}), 200
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": f"Role assignment failed: {str(e)}"}), 500


@auth_bp.route('/users/<user_id>/roles/<role_id>', methods=['DELETE'])
@jwt_required()
def remove_role_from_user(user_id, role_id):
    """Remove role from user."""
    try:
        # Check if user has permission to remove roles
        claims = get_jwt()
        user_roles = claims.get('roles', [])
        
        if 'admin' not in user_roles:
            return jsonify({"error": "Insufficient permissions"}), 403
        
        result = RoleService.remove_role_from_user(user_id, role_id)
        
        if result["success"]:
            return jsonify({"message": result["message"]}), 200
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": f"Role removal failed: {str(e)}"}), 500


# Health check endpoint
@auth_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "user-service",
        "version": "1.0.0"
    }), 200

