"""
API data schemas for the CDP Support Agent Chatbot.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field


@dataclass
class ChatRequest:
    """Chat request schema."""
    
    message: str
    conversation_id: Optional[str] = None


@dataclass
class ChatResponse:
    """Chat response schema."""
    
    response: Dict[str, Any]
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class QueryAnalysis:
    """Query analysis schema."""
    
    cdp: Optional[str] = None
    query_type: Optional[str] = None
    is_relevant: bool = True
    cdps: List[str] = field(default_factory=list)
    feature: Optional[str] = None


@dataclass
class DocumentResult:
    """Document result schema."""
    
    content: str
    metadata: Dict[str, Any]
    id: str
    distance: Optional[float] = None
    content_score: Optional[float] = None
    metadata_score: Optional[float] = None
    final_score: Optional[float] = None


@dataclass
class QueryResponse:
    """Query response schema."""
    
    type: str
    query: str
    analysis: QueryAnalysis
    results: Union[List[DocumentResult], Dict[str, List[DocumentResult]], None] = None
    message: Optional[str] = None