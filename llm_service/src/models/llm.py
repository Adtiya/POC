from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import uuid
import json

db = SQLAlchemy()

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    title = db.Column(db.String(255))
    context = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    messages = db.relationship('Message', back_populates='conversation', cascade='all, delete-orphan', order_by='Message.created_at')
    
    def to_dict(self, include_messages=False):
        """Convert conversation to dictionary representation."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'context': self.context,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'message_count': len(self.messages)
        }
        
        if include_messages:
            data['messages'] = [message.to_dict() for message in self.messages]
        
        return data
    
    def get_recent_messages(self, limit=10):
        """Get recent messages from the conversation."""
        return Message.query.filter_by(conversation_id=self.id).order_by(Message.created_at.desc()).limit(limit).all()
    
    def __repr__(self):
        return f'<Conversation {self.id}>'


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = db.Column(db.Text, nullable=False)
    metadata = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    conversation = db.relationship('Conversation', back_populates='messages')
    
    def to_dict(self):
        """Convert message to dictionary representation."""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Message {self.id} - {self.role}>'


class PromptTemplate(db.Model):
    __tablename__ = 'prompt_templates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    template = db.Column(db.Text, nullable=False)
    variables = db.Column(db.JSON, default=dict)
    model_config = db.Column(db.JSON, default=dict)
    created_by = db.Column(db.String(36), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        """Convert prompt template to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template': self.template,
            'variables': self.variables,
            'model_config': self.model_config,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def render_template(self, **kwargs):
        """Render the template with provided variables."""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable: {e}")
    
    def __repr__(self):
        return f'<PromptTemplate {self.name}>'


class DocumentProcessing(db.Model):
    __tablename__ = 'document_processing'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    document_name = db.Column(db.String(255), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # 'text', 'pdf', 'docx', etc.
    processing_type = db.Column(db.String(50), nullable=False)  # 'summarize', 'extract', 'analyze'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    input_data = db.Column(db.JSON, nullable=False)
    output_data = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    processing_time = db.Column(db.Float)  # in seconds
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        """Convert document processing record to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'document_name': self.document_name,
            'document_type': self.document_type,
            'processing_type': self.processing_type,
            'status': self.status,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'error_message': self.error_message,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def mark_completed(self, output_data, processing_time):
        """Mark the processing as completed."""
        self.status = 'completed'
        self.output_data = output_data
        self.processing_time = processing_time
        self.completed_at = datetime.now(timezone.utc)
    
    def mark_failed(self, error_message):
        """Mark the processing as failed."""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = datetime.now(timezone.utc)
    
    def __repr__(self):
        return f'<DocumentProcessing {self.id} - {self.status}>'


class LLMUsageLog(db.Model):
    __tablename__ = 'llm_usage_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id'))
    model_name = db.Column(db.String(100), nullable=False)
    operation_type = db.Column(db.String(50), nullable=False)  # 'chat', 'completion', 'summarize', etc.
    prompt_tokens = db.Column(db.Integer, default=0)
    completion_tokens = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    cost = db.Column(db.Float, default=0.0)
    response_time = db.Column(db.Float)  # in seconds
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        """Convert usage log to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'conversation_id': self.conversation_id,
            'model_name': self.model_name,
            'operation_type': self.operation_type,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'cost': self.cost,
            'response_time': self.response_time,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<LLMUsageLog {self.id} - {self.model_name}>'

