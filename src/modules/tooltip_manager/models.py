"""Database models for tooltip system"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Context(Base):
    """Tooltip context (e.g., global, module_123, board_R34)"""
    __tablename__ = 'contexts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    matching_strategy = Column(String(50), default='exact')  # 'exact', 'word_boundary', 'regex'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    tooltip_contexts = relationship('TooltipContext', back_populates='context', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'matching_strategy': self.matching_strategy,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Tooltip(Base):
    """Individual tooltip entry"""
    __tablename__ = 'tooltips'
    
    id = Column(Integer, primary_key=True)
    keyword = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default='text')  # 'text' or 'html'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    tooltip_contexts = relationship('TooltipContext', back_populates='tooltip', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'keyword': self.keyword,
            'content': self.content,
            'content_type': self.content_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TooltipContext(Base):
    """Many-to-many relationship between tooltips and contexts"""
    __tablename__ = 'tooltip_contexts'
    
    id = Column(Integer, primary_key=True)
    tooltip_id = Column(Integer, ForeignKey('tooltips.id', ondelete='CASCADE'), nullable=False)
    context_id = Column(Integer, ForeignKey('contexts.id', ondelete='CASCADE'), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('tooltip_id', 'context_id', name='_tooltip_context_uc'),
    )
    
    # Relationships
    tooltip = relationship('Tooltip', back_populates='tooltip_contexts')
    context = relationship('Context', back_populates='tooltip_contexts')
