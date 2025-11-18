"""
File Manager Database Models - SQLAlchemy models with manual versioning support.

This module defines the database schema for file versioning, grouping, and tagging.
Uses manual version tracking instead of SQLAlchemy-Continuum for better control.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


# Association table for many-to-many relationship between file versions and tags
file_version_tags = Table(
    'file_version_tags', Base.metadata,
    Column('version_id', Integer, ForeignKey('file_versions.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('file_tags.id'), primary_key=True)
)


class FileGroup(Base):
    """Logical grouping for related files.
    
    A file group represents a collection of related file versions. Files with the
    same filename in the same group are considered different versions of each other.
    
    Attributes:
        group_id: Unique identifier for the group (can be user-specified or auto-generated)
        name: Human-readable name for the group
        description: Optional description of the group's purpose
        created_at: Timestamp when the group was created
        created_by: Username of the creator
    """
    __tablename__ = 'file_groups'
    
    group_id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)
    
    # Relationship to file versions
    files = relationship('FileVersion', back_populates='group', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<FileGroup(group_id='{self.group_id}', name='{self.name}')>"


class FileVersion(Base):
    """File metadata with manual versioning support.
    
    Each row represents a specific version of a file. When a file with the same name
    is uploaded to the same group, a new FileVersion is created with incremented version.
    
    Attributes:
        id: Primary key (auto-increment)
        group_id: Foreign key to FileGroup
        filename: User-facing filename (e.g., "report.pdf")
        storage_path: Path in hashfs or filesystem where file content is stored
        file_size: Size in bytes
        mime_type: MIME type (e.g., "application/pdf")
        checksum: SHA256 hash of file content
        uploaded_at: Timestamp when this version was uploaded
        uploaded_by: Username of uploader
        is_current: True if this is the current version (latest)
        source_version_id: If restored from old version, points to original
    
    Constraints:
        - Unique constraint on (group_id, filename, uploaded_at) to prevent duplicate versions
        - Index on checksum for fast deduplication queries
        - Index on (group_id, filename, is_current) for fast current version lookup
    """
    __tablename__ = 'file_versions'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(String, ForeignKey('file_groups.group_id'))
    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)  # Path in hashfs or filesystem
    file_size = Column(Integer)
    mime_type = Column(String)
    checksum = Column(String)  # SHA256 hash
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String)
    is_current = Column(Boolean, default=True)
    source_version_id = Column(Integer, ForeignKey('file_versions.id'), nullable=True)
    
    # Relationships
    group = relationship('FileGroup', back_populates='files')
    tags = relationship('FileTag', secondary=file_version_tags, back_populates='file_versions')
    source_version = relationship('FileVersion', remote_side=[id], uselist=False)
    
    # Constraints and Indexes
    __table_args__ = (
        # Index on checksum for deduplication queries
        Index('idx_checksum', 'checksum'),
        
        # Composite index for fast current version lookup
        Index('idx_group_filename_current', 'group_id', 'filename', 'is_current'),
        
        # Unique constraint on (group_id, filename, uploaded_at)
        # This prevents exact duplicate uploads at same timestamp
        UniqueConstraint('group_id', 'filename', 'uploaded_at', name='uq_group_filename_timestamp'),
    )
    
    def __repr__(self):
        return f"<FileVersion(id={self.id}, filename='{self.filename}', group_id='{self.group_id}', is_current={self.is_current})>"


class FileTag(Base):
    """Tags for file organization and searching.
    
    Tags provide a flexible way to categorize and search files beyond the group structure.
    Multiple tags can be assigned to a single file version.
    
    Attributes:
        id: Primary key (auto-increment)
        tag_name: Unique tag identifier (e.g., "invoice", "2025", "urgent")
    """
    __tablename__ = 'file_tags'
    
    id = Column(Integer, primary_key=True)
    tag_name = Column(String, unique=True, nullable=False)
    
    # Relationship
    file_versions = relationship('FileVersion', secondary=file_version_tags, back_populates='tags')
    
    def __repr__(self):
        return f"<FileTag(tag_name='{self.tag_name}')>"
