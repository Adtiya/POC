from flask import Blueprint, request, jsonify, Response, stream_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError, BaseModel
from typing import Optional, Dict, Any
import json
from src.services.llm_service import LLMService, PromptTemplateService
from src.models.llm import db

llm_bp = Blueprint('llm', __name__)
llm_service = LLMService()

# Pydantic schemas for request validation
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = 'gpt-3.5-turbo'
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000

class DocumentSummarizeRequest(BaseModel):
    content: str
    max_length: Optional[int] = 500
    style: Optional[str] = 'concise'

class ContentGenerationRequest(BaseModel):
    prompt: str
    content_type: Optional[str] = 'text'
    model: Optional[str] = 'gpt-3.5-turbo'
    parameters: Optional[Dict[str, Any]] = {}

def validate_json_data(schema_class, data):
    """Validate JSON data against Pydantic schema."""
    try:
        return schema_class(**data), None
    except ValidationError as e:
        return None, {"error": "Validation failed", "details": e.errors()}

@llm_bp.route('/llm/health', methods=['GET'])
def health_check():
    """Health check endpoint for LLM service."""
    return jsonify({
        "status": "healthy",
        "service": "llm-service",
        "version": "1.0.0"
    }), 200

@llm_bp.route('/llm/chat', methods=['POST'])
@jwt_required()
def chat():
    """Process a chat message."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        chat_data, error = validate_json_data(ChatRequest, data)
        if error:
            return jsonify(error), 400
        
        result = llm_service.chat(
            user_id=user_id,
            message=chat_data.message,
            conversation_id=chat_data.conversation_id,
            model=chat_data.model,
            temperature=chat_data.temperature,
            max_tokens=chat_data.max_tokens
        )
        
        if result["success"]:
            return jsonify({
                "message": result["message"],
                "conversation_id": result["conversation_id"],
                "message_id": result["message_id"],
                "model": result["model"],
                "usage": result.get("usage", {}),
                "response_time": result["response_time"]
            }), 200
        else:
            return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        return jsonify({"error": f"Chat failed: {str(e)}"}), 500

@llm_bp.route('/llm/chat/stream', methods=['POST'])
@jwt_required()
def chat_stream():
    """Process a chat message with streaming response."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        chat_data, error = validate_json_data(ChatRequest, data)
        if error:
            return jsonify(error), 400
        
        def generate():
            for chunk in llm_service.chat_stream(
                user_id=user_id,
                message=chat_data.message,
                conversation_id=chat_data.conversation_id,
                model=chat_data.model,
                temperature=chat_data.temperature,
                max_tokens=chat_data.max_tokens
            ):
                yield chunk
        
        return Response(generate(), mimetype='text/plain')
        
    except Exception as e:
        return jsonify({"error": f"Streaming chat failed: {str(e)}"}), 500

@llm_bp.route('/llm/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """Get user's conversations."""
    try:
        user_id = get_jwt_identity()
        limit = request.args.get('limit', 20, type=int)
        
        conversations = llm_service.get_user_conversations(user_id, limit)
        return jsonify({"conversations": conversations}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get conversations: {str(e)}"}), 500

@llm_bp.route('/llm/conversations', methods=['POST'])
@jwt_required()
def create_conversation():
    """Create a new conversation."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        result = llm_service.create_conversation(
            user_id=user_id,
            title=data.get('title'),
            context=data.get('context', {})
        )
        
        if result["success"]:
            return jsonify({
                "conversation": result["conversation"],
                "message": result["message"]
            }), 201
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": f"Failed to create conversation: {str(e)}"}), 500

@llm_bp.route('/llm/conversations/<conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(conversation_id):
    """Get a specific conversation with messages."""
    try:
        user_id = get_jwt_identity()
        
        conversation = llm_service.get_conversation(conversation_id, user_id)
        
        if conversation:
            return jsonify({"conversation": conversation}), 200
        else:
            return jsonify({"error": "Conversation not found"}), 404
            
    except Exception as e:
        return jsonify({"error": f"Failed to get conversation: {str(e)}"}), 500

@llm_bp.route('/llm/conversations/<conversation_id>', methods=['DELETE'])
@jwt_required()
def delete_conversation(conversation_id):
    """Delete a conversation."""
    try:
        user_id = get_jwt_identity()
        
        result = llm_service.delete_conversation(conversation_id, user_id)
        
        if result["success"]:
            return jsonify({"message": result["message"]}), 200
        else:
            return jsonify({"error": result["error"]}), 404
            
    except Exception as e:
        return jsonify({"error": f"Failed to delete conversation: {str(e)}"}), 500

@llm_bp.route('/llm/documents/summarize', methods=['POST'])
@jwt_required()
def summarize_document():
    """Summarize a document."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        doc_data, error = validate_json_data(DocumentSummarizeRequest, data)
        if error:
            return jsonify(error), 400
        
        result = llm_service.summarize_document(
            user_id=user_id,
            content=doc_data.content,
            max_length=doc_data.max_length,
            style=doc_data.style
        )
        
        if result["success"]:
            return jsonify({
                "summary": result["summary"],
                "processing_id": result["processing_id"],
                "processing_time": result["processing_time"]
            }), 200
        else:
            return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        return jsonify({"error": f"Document summarization failed: {str(e)}"}), 500

@llm_bp.route('/llm/generate/<content_type>', methods=['POST'])
@jwt_required()
def generate_content(content_type):
    """Generate content based on prompt and type."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        content_data, error = validate_json_data(ContentGenerationRequest, data)
        if error:
            return jsonify(error), 400
        
        result = llm_service.generate_content(
            user_id=user_id,
            prompt=content_data.prompt,
            content_type=content_type,
            parameters=content_data.parameters
        )
        
        if result["success"]:
            return jsonify({
                "content": result["content"],
                "content_type": result["content_type"],
                "model": result["model"],
                "processing_time": result["processing_time"],
                "usage": result.get("usage", {})
            }), 200
        else:
            return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        return jsonify({"error": f"Content generation failed: {str(e)}"}), 500

@llm_bp.route('/llm/usage/stats', methods=['GET'])
@jwt_required()
def get_usage_stats():
    """Get user's LLM usage statistics."""
    try:
        user_id = get_jwt_identity()
        days = request.args.get('days', 30, type=int)
        
        stats = llm_service.get_user_usage_stats(user_id, days)
        return jsonify({"stats": stats}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get usage stats: {str(e)}"}), 500

# Prompt Template Management
@llm_bp.route('/llm/templates', methods=['GET'])
@jwt_required()
def get_templates():
    """Get all prompt templates."""
    try:
        templates = PromptTemplateService.get_all_templates()
        return jsonify({"templates": templates}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get templates: {str(e)}"}), 500

@llm_bp.route('/llm/templates', methods=['POST'])
@jwt_required()
def create_template():
    """Create a new prompt template."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        result = PromptTemplateService.create_template(
            name=data.get('name'),
            template=data.get('template'),
            description=data.get('description'),
            variables=data.get('variables', {}),
            model_config=data.get('model_config', {}),
            created_by=user_id
        )
        
        if result["success"]:
            return jsonify({
                "template": result["template"],
                "message": result["message"]
            }), 201
        else:
            return jsonify({"error": result["error"]}), 400
            
    except Exception as e:
        return jsonify({"error": f"Template creation failed: {str(e)}"}), 500

@llm_bp.route('/llm/templates/<template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id):
    """Get a specific template."""
    try:
        template = PromptTemplateService.get_template_by_id(template_id)
        
        if template:
            return jsonify({"template": template}), 200
        else:
            return jsonify({"error": "Template not found"}), 404
            
    except Exception as e:
        return jsonify({"error": f"Failed to get template: {str(e)}"}), 500

@llm_bp.route('/llm/templates/<template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    """Update a prompt template."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        result = PromptTemplateService.update_template(template_id, **data)
        
        if result["success"]:
            return jsonify({
                "template": result["template"],
                "message": result["message"]
            }), 200
        else:
            return jsonify({"error": result["error"]}), 404
            
    except Exception as e:
        return jsonify({"error": f"Template update failed: {str(e)}"}), 500

@llm_bp.route('/llm/templates/<template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    """Delete a prompt template."""
    try:
        result = PromptTemplateService.delete_template(template_id)
        
        if result["success"]:
            return jsonify({"message": result["message"]}), 200
        else:
            return jsonify({"error": result["error"]}), 404
            
    except Exception as e:
        return jsonify({"error": f"Template deletion failed: {str(e)}"}), 500

