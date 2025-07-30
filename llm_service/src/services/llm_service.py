import os
import time
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime, timezone
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage
from src.models.llm import Conversation, Message, PromptTemplate, DocumentProcessing, LLMUsageLog, db


class LLMService:
    """Service class for handling LLM operations."""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Default model configurations
        self.model_configs = {
            'gpt-4': {
                'model': 'gpt-4',
                'temperature': 0.7,
                'max_tokens': 2000,
                'cost_per_1k_prompt': 0.03,
                'cost_per_1k_completion': 0.06
            },
            'gpt-3.5-turbo': {
                'model': 'gpt-3.5-turbo',
                'temperature': 0.7,
                'max_tokens': 2000,
                'cost_per_1k_prompt': 0.001,
                'cost_per_1k_completion': 0.002
            }
        }
    
    def _get_llm_client(self, model: str = 'gpt-3.5-turbo', **kwargs) -> ChatOpenAI:
        """Get LLM client with specified configuration."""
        config = self.model_configs.get(model, self.model_configs['gpt-3.5-turbo'])
        config.update(kwargs)
        
        return ChatOpenAI(
            openai_api_key=self.openai_api_key,
            model=config['model'],
            temperature=config.get('temperature', 0.7),
            max_tokens=config.get('max_tokens', 2000)
        )
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate the cost of LLM usage."""
        config = self.model_configs.get(model, self.model_configs['gpt-3.5-turbo'])
        prompt_cost = (prompt_tokens / 1000) * config['cost_per_1k_prompt']
        completion_cost = (completion_tokens / 1000) * config['cost_per_1k_completion']
        return prompt_cost + completion_cost
    
    def _log_usage(self, user_id: str, conversation_id: str, model: str, operation_type: str,
                   prompt_tokens: int, completion_tokens: int, response_time: float):
        """Log LLM usage for analytics and billing."""
        total_tokens = prompt_tokens + completion_tokens
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)
        
        usage_log = LLMUsageLog(
            user_id=user_id,
            conversation_id=conversation_id,
            model_name=model,
            operation_type=operation_type,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            response_time=response_time
        )
        
        db.session.add(usage_log)
        db.session.commit()
    
    def create_conversation(self, user_id: str, title: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new conversation."""
        try:
            conversation = Conversation(
                user_id=user_id,
                title=title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                context=context or {}
            )
            
            db.session.add(conversation)
            db.session.commit()
            
            return {
                "success": True,
                "conversation": conversation.to_dict(),
                "message": "Conversation created successfully"
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Failed to create conversation: {str(e)}"}
    
    def get_user_conversations(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's conversations."""
        conversations = Conversation.query.filter_by(user_id=user_id).order_by(
            Conversation.updated_at.desc()
        ).limit(limit).all()
        
        return [conv.to_dict() for conv in conversations]
    
    def get_conversation(self, conversation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific conversation with messages."""
        conversation = Conversation.query.filter_by(
            id=conversation_id, user_id=user_id
        ).first()
        
        if not conversation:
            return None
        
        return conversation.to_dict(include_messages=True)
    
    def delete_conversation(self, conversation_id: str, user_id: str) -> Dict[str, Any]:
        """Delete a conversation."""
        try:
            conversation = Conversation.query.filter_by(
                id=conversation_id, user_id=user_id
            ).first()
            
            if not conversation:
                return {"success": False, "error": "Conversation not found"}
            
            db.session.delete(conversation)
            db.session.commit()
            
            return {"success": True, "message": "Conversation deleted successfully"}
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Failed to delete conversation: {str(e)}"}
    
    def chat(self, user_id: str, message: str, conversation_id: str = None, 
             model: str = 'gpt-3.5-turbo', **kwargs) -> Dict[str, Any]:
        """Process a chat message."""
        start_time = time.time()
        
        try:
            # Get or create conversation
            if conversation_id:
                conversation = Conversation.query.filter_by(
                    id=conversation_id, user_id=user_id
                ).first()
                if not conversation:
                    return {"success": False, "error": "Conversation not found"}
            else:
                result = self.create_conversation(user_id)
                if not result["success"]:
                    return result
                conversation = Conversation.query.get(result["conversation"]["id"])
            
            # Save user message
            user_message = Message(
                conversation_id=conversation.id,
                role='user',
                content=message
            )
            db.session.add(user_message)
            
            # Get conversation history
            messages = conversation.get_recent_messages(limit=10)
            messages.reverse()  # Chronological order
            
            # Prepare messages for LLM
            llm_messages = []
            for msg in messages:
                if msg.role == 'user':
                    llm_messages.append(HumanMessage(content=msg.content))
                elif msg.role == 'assistant':
                    llm_messages.append(AIMessage(content=msg.content))
                elif msg.role == 'system':
                    llm_messages.append(SystemMessage(content=msg.content))
            
            # Add current user message
            llm_messages.append(HumanMessage(content=message))
            
            # Get LLM response
            llm = self._get_llm_client(model, **kwargs)
            response = llm.invoke(llm_messages)
            
            # Save assistant message
            assistant_message = Message(
                conversation_id=conversation.id,
                role='assistant',
                content=response.content,
                metadata={
                    'model': model,
                    'usage': getattr(response, 'usage_metadata', {}),
                    'response_time': time.time() - start_time
                }
            )
            db.session.add(assistant_message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.now(timezone.utc)
            
            db.session.commit()
            
            # Log usage
            usage = getattr(response, 'usage_metadata', {})
            self._log_usage(
                user_id=user_id,
                conversation_id=conversation.id,
                model=model,
                operation_type='chat',
                prompt_tokens=usage.get('input_tokens', 0),
                completion_tokens=usage.get('output_tokens', 0),
                response_time=time.time() - start_time
            )
            
            return {
                "success": True,
                "message": response.content,
                "conversation_id": conversation.id,
                "message_id": assistant_message.id,
                "model": model,
                "usage": usage,
                "response_time": time.time() - start_time
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Chat failed: {str(e)}"}
    
    def chat_stream(self, user_id: str, message: str, conversation_id: str = None,
                   model: str = 'gpt-3.5-turbo', **kwargs) -> Generator[str, None, None]:
        """Process a chat message with streaming response."""
        start_time = time.time()
        
        try:
            # Get or create conversation
            if conversation_id:
                conversation = Conversation.query.filter_by(
                    id=conversation_id, user_id=user_id
                ).first()
                if not conversation:
                    yield f"data: {{'error': 'Conversation not found'}}\n\n"
                    return
            else:
                result = self.create_conversation(user_id)
                if not result["success"]:
                    yield f"data: {{'error': '{result['error']}'}}\n\n"
                    return
                conversation = Conversation.query.get(result["conversation"]["id"])
            
            # Save user message
            user_message = Message(
                conversation_id=conversation.id,
                role='user',
                content=message
            )
            db.session.add(user_message)
            db.session.commit()
            
            # Get conversation history
            messages = conversation.get_recent_messages(limit=10)
            messages.reverse()
            
            # Prepare messages for LLM
            llm_messages = []
            for msg in messages:
                if msg.role == 'user':
                    llm_messages.append(HumanMessage(content=msg.content))
                elif msg.role == 'assistant':
                    llm_messages.append(AIMessage(content=msg.content))
                elif msg.role == 'system':
                    llm_messages.append(SystemMessage(content=msg.content))
            
            llm_messages.append(HumanMessage(content=message))
            
            # Stream LLM response
            llm = self._get_llm_client(model, **kwargs)
            full_response = ""
            
            for chunk in llm.stream(llm_messages):
                if chunk.content:
                    full_response += chunk.content
                    yield f"data: {{'content': '{chunk.content}', 'conversation_id': '{conversation.id}'}}\n\n"
            
            # Save assistant message
            assistant_message = Message(
                conversation_id=conversation.id,
                role='assistant',
                content=full_response,
                metadata={
                    'model': model,
                    'response_time': time.time() - start_time,
                    'streaming': True
                }
            )
            db.session.add(assistant_message)
            
            # Update conversation timestamp
            conversation.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            # Send completion signal
            yield f"data: {{'done': true, 'message_id': '{assistant_message.id}'}}\n\n"
            
        except Exception as e:
            yield f"data: {{'error': 'Streaming failed: {str(e)}'}}\n\n"
    
    def summarize_document(self, user_id: str, content: str, max_length: int = 500,
                          style: str = 'concise') -> Dict[str, Any]:
        """Summarize a document."""
        start_time = time.time()
        
        try:
            # Create document processing record
            doc_processing = DocumentProcessing(
                user_id=user_id,
                document_name="Text Document",
                document_type="text",
                processing_type="summarize",
                status="processing",
                input_data={
                    "content": content[:1000] + "..." if len(content) > 1000 else content,
                    "max_length": max_length,
                    "style": style
                }
            )
            db.session.add(doc_processing)
            db.session.commit()
            
            # Prepare prompt
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", f"You are a helpful assistant that summarizes documents. "
                          f"Create a {style} summary of the following text in approximately {max_length} words."),
                ("human", "{content}")
            ])
            
            # Get LLM response
            llm = self._get_llm_client('gpt-3.5-turbo')
            chain = prompt_template | llm
            response = llm.invoke([
                SystemMessage(content=f"You are a helpful assistant that summarizes documents. "
                                    f"Create a {style} summary of the following text in approximately {max_length} words."),
                HumanMessage(content=content)
            ])
            
            processing_time = time.time() - start_time
            
            # Update processing record
            doc_processing.mark_completed(
                output_data={"summary": response.content},
                processing_time=processing_time
            )
            db.session.commit()
            
            # Log usage
            usage = getattr(response, 'usage_metadata', {})
            self._log_usage(
                user_id=user_id,
                conversation_id=None,
                model='gpt-3.5-turbo',
                operation_type='summarize',
                prompt_tokens=usage.get('input_tokens', 0),
                completion_tokens=usage.get('output_tokens', 0),
                response_time=processing_time
            )
            
            return {
                "success": True,
                "summary": response.content,
                "processing_id": doc_processing.id,
                "processing_time": processing_time
            }
            
        except Exception as e:
            if 'doc_processing' in locals():
                doc_processing.mark_failed(str(e))
                db.session.commit()
            
            return {"success": False, "error": f"Document summarization failed: {str(e)}"}
    
    def generate_content(self, user_id: str, prompt: str, content_type: str = 'text',
                        parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate content based on prompt and type."""
        start_time = time.time()
        
        try:
            parameters = parameters or {}
            model = parameters.get('model', 'gpt-3.5-turbo')
            
            # Prepare system message based on content type
            system_messages = {
                'text': "You are a helpful assistant that generates high-quality text content.",
                'code': "You are an expert programmer that generates clean, well-documented code.",
                'report': "You are a professional report writer that creates structured, comprehensive reports.",
                'email': "You are a professional communication assistant that writes clear, effective emails.",
                'blog': "You are a skilled content writer that creates engaging blog posts."
            }
            
            system_message = system_messages.get(content_type, system_messages['text'])
            
            # Get LLM response
            llm = self._get_llm_client(model, **parameters)
            response = llm.invoke([
                SystemMessage(content=system_message),
                HumanMessage(content=prompt)
            ])
            
            processing_time = time.time() - start_time
            
            # Log usage
            usage = getattr(response, 'usage_metadata', {})
            self._log_usage(
                user_id=user_id,
                conversation_id=None,
                model=model,
                operation_type=f'generate_{content_type}',
                prompt_tokens=usage.get('input_tokens', 0),
                completion_tokens=usage.get('output_tokens', 0),
                response_time=processing_time
            )
            
            return {
                "success": True,
                "content": response.content,
                "content_type": content_type,
                "model": model,
                "processing_time": processing_time,
                "usage": usage
            }
            
        except Exception as e:
            return {"success": False, "error": f"Content generation failed: {str(e)}"}
    
    def get_user_usage_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user's LLM usage statistics."""
        from datetime import timedelta
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        usage_logs = LLMUsageLog.query.filter(
            LLMUsageLog.user_id == user_id,
            LLMUsageLog.created_at >= start_date
        ).all()
        
        if not usage_logs:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "avg_response_time": 0.0,
                "usage_by_model": {},
                "usage_by_operation": {}
            }
        
        total_requests = len(usage_logs)
        total_tokens = sum(log.total_tokens for log in usage_logs)
        total_cost = sum(log.cost for log in usage_logs)
        avg_response_time = sum(log.response_time or 0 for log in usage_logs) / total_requests
        
        # Usage by model
        usage_by_model = {}
        for log in usage_logs:
            if log.model_name not in usage_by_model:
                usage_by_model[log.model_name] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            usage_by_model[log.model_name]["requests"] += 1
            usage_by_model[log.model_name]["tokens"] += log.total_tokens
            usage_by_model[log.model_name]["cost"] += log.cost
        
        # Usage by operation
        usage_by_operation = {}
        for log in usage_logs:
            if log.operation_type not in usage_by_operation:
                usage_by_operation[log.operation_type] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            usage_by_operation[log.operation_type]["requests"] += 1
            usage_by_operation[log.operation_type]["tokens"] += log.total_tokens
            usage_by_operation[log.operation_type]["cost"] += log.cost
        
        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 4),
            "avg_response_time": round(avg_response_time, 2),
            "usage_by_model": usage_by_model,
            "usage_by_operation": usage_by_operation,
            "period_days": days
        }


class PromptTemplateService:
    """Service for managing prompt templates."""
    
    @staticmethod
    def create_template(name: str, template: str, description: str = None,
                       variables: Dict[str, Any] = None, model_config: Dict[str, Any] = None,
                       created_by: str = None) -> Dict[str, Any]:
        """Create a new prompt template."""
        try:
            existing_template = PromptTemplate.query.filter_by(name=name).first()
            if existing_template:
                return {"success": False, "error": "Template with this name already exists"}
            
            template_obj = PromptTemplate(
                name=name,
                description=description,
                template=template,
                variables=variables or {},
                model_config=model_config or {},
                created_by=created_by
            )
            
            db.session.add(template_obj)
            db.session.commit()
            
            return {
                "success": True,
                "template": template_obj.to_dict(),
                "message": "Template created successfully"
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Template creation failed: {str(e)}"}
    
    @staticmethod
    def get_all_templates() -> List[Dict[str, Any]]:
        """Get all prompt templates."""
        templates = PromptTemplate.query.all()
        return [template.to_dict() for template in templates]
    
    @staticmethod
    def get_template_by_id(template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by ID."""
        template = PromptTemplate.query.get(template_id)
        return template.to_dict() if template else None
    
    @staticmethod
    def update_template(template_id: str, **kwargs) -> Dict[str, Any]:
        """Update a prompt template."""
        try:
            template = PromptTemplate.query.get(template_id)
            if not template:
                return {"success": False, "error": "Template not found"}
            
            for key, value in kwargs.items():
                if hasattr(template, key) and value is not None:
                    setattr(template, key, value)
            
            template.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            return {
                "success": True,
                "template": template.to_dict(),
                "message": "Template updated successfully"
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Template update failed: {str(e)}"}
    
    @staticmethod
    def delete_template(template_id: str) -> Dict[str, Any]:
        """Delete a prompt template."""
        try:
            template = PromptTemplate.query.get(template_id)
            if not template:
                return {"success": False, "error": "Template not found"}
            
            db.session.delete(template)
            db.session.commit()
            
            return {"success": True, "message": "Template deleted successfully"}
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": f"Template deletion failed: {str(e)}"}

