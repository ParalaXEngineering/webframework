"""Tooltip Manager - Core class for managing tooltips"""

import csv
import io
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import create_engine, or_, func
from sqlalchemy.orm import sessionmaker, Session

from src.modules.log.logger_factory import get_logger
from .models import Base, Context, Tooltip, TooltipContext
from .utils import process_image_to_base64

logger = get_logger(__name__)

# Global context - always available, cannot be deleted
GLOBAL_CONTEXT_NAME = "Global"
GLOBAL_CONTEXT_DESCRIPTION = "Global context available on all pages"


class TooltipManager:
    """Manages tooltips and contexts with caching"""
    
    def __init__(self, settings_manager=None):
        """
        Initialize TooltipManager with database and cache.
        
        Args:
            settings_manager: SettingsManager instance for configuration
        """
        # Get DB path from settings or use default
        if settings_manager:
            try:
                db_path = settings_manager.get_setting('tooltip_system.db_path') or 'resources/tooltip_data.db'
            except:
                db_path = 'resources/tooltip_data.db'
            
            try:
                self.cache_ttl = settings_manager.get_setting('tooltip_system.cache_ttl') or 300
            except:
                self.cache_ttl = 300
                
            try:
                self.image_max_width = settings_manager.get_setting('tooltip_system.image_max_width') or 800
            except:
                self.image_max_width = 800
                
            try:
                self.image_max_height = settings_manager.get_setting('tooltip_system.image_max_height') or 600
            except:
                self.image_max_height = 600
                
            try:
                self.image_quality = settings_manager.get_setting('tooltip_system.image_quality') or 85
            except:
                self.image_quality = 85
        else:
            db_path = 'resources/tooltip_data.db'
            self.cache_ttl = 300
            self.image_max_width = 800
            self.image_max_height = 600
            self.image_quality = 85
        
        # Ensure directory exists
        db_path_obj = Path(db_path)
        db_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Cache: {frozenset(contexts): (tooltips_dict, timestamp)}
        self._cache: Dict[frozenset, Tuple[Dict, float]] = {}
        
        # Ensure Global context exists
        self._ensure_global_context()
        
        logger.info(f"TooltipManager initialized with DB: {db_path}")
    
    def _get_session(self) -> Session:
        """Create new database session"""
        return self.Session()
    
    def _ensure_global_context(self):
        """Ensure Global context exists in database"""
        try:
            session = self._get_session()
            global_ctx = session.query(Context).filter_by(name=GLOBAL_CONTEXT_NAME).first()
            
            if not global_ctx:
                global_ctx = Context(
                    name=GLOBAL_CONTEXT_NAME,
                    description=GLOBAL_CONTEXT_DESCRIPTION,
                    matching_strategy='exact'
                )
                session.add(global_ctx)
                session.commit()
                logger.info(f"Created {GLOBAL_CONTEXT_NAME} context")
            
            session.close()
        except Exception as e:
            logger.error(f"Error ensuring Global context: {e}")
    
    def _invalidate_cache(self, context: Optional[str] = None):
        """Clear cache for specific context or all"""
        if context is None:
            self._cache.clear()
            logger.debug("Cache cleared (all)")
        else:
            # Remove all cache entries containing this context
            keys_to_remove = [k for k in self._cache.keys() if context in k]
            for key in keys_to_remove:
                del self._cache[key]
            logger.debug(f"Cache cleared for context: {context}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Returns cache statistics"""
        entries = []
        current_time = time.time()
        for contexts, (_, timestamp) in self._cache.items():
            age = current_time - timestamp
            entries.append({
                'contexts': list(contexts),
                'age_seconds': age
            })
        
        return {
            'size': len(self._cache),
            'entries': entries
        }
    
    # Query API
    def get_tooltips_for_contexts(self, contexts: List[str]) -> Dict[str, Dict[str, str]]:
        """
        Get merged tooltips for given contexts.
        
        Args:
            contexts: List of context names (order matters, last wins)
        
        Returns:
            Dict mapping keyword to tooltip data:
            {
                "R34": {"content": "<img...>", "type": "html", "strategy": "word_boundary"},
                "PartNumber": {"content": "Text...", "type": "text", "strategy": "exact"}
            }
        """
        if not contexts:
            return {}
        
        # Check cache
        cache_key = frozenset(contexts)
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for contexts: {contexts}")
                return cached_data
        
        try:
            session = self._get_session()
            
            # Get all tooltips for these contexts
            result = {}
            context_strategies = {}
            
            # Get context strategies
            ctx_objs = session.query(Context).filter(Context.name.in_(contexts)).all()
            for ctx in ctx_objs:
                context_strategies[ctx.name] = ctx.matching_strategy
            
            # Process contexts in order (last wins)
            for context_name in contexts:
                ctx = session.query(Context).filter_by(name=context_name).first()
                if not ctx:
                    continue
                
                # Get tooltips for this context
                tooltips = session.query(Tooltip).join(TooltipContext).filter(
                    TooltipContext.context_id == ctx.id
                ).all()
                
                for tooltip in tooltips:
                    result[tooltip.keyword] = {
                        'content': tooltip.content,
                        'type': tooltip.content_type,
                        'strategy': ctx.matching_strategy
                    }
            
            session.close()
            
            # Cache result
            self._cache[cache_key] = (result, time.time())
            logger.debug(f"Loaded {len(result)} tooltips for contexts: {contexts}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error loading tooltips: {e}")
            return {}
    
    def get_context_strategy(self, context_name: str) -> str:
        """Get matching strategy for context"""
        try:
            session = self._get_session()
            ctx = session.query(Context).filter_by(name=context_name).first()
            session.close()
            return ctx.matching_strategy if ctx else 'exact'
        except Exception as e:
            logger.error(f"Error getting context strategy: {e}")
            return 'exact'
    
    # Registration API
    def register_tooltip(
        self,
        keyword: str,
        content: str,
        contexts: List[str],
        content_type: str = 'text'
    ) -> int:
        """
        Create or update tooltip.
        
        Args:
            keyword: Tooltip keyword
            content: Tooltip content
            contexts: List of context names
            content_type: 'text' or 'html'
        
        Returns:
            Tooltip ID
        """
        try:
            session = self._get_session()
            
            # Check if tooltip with same keyword in same contexts exists
            existing = None
            for ctx_name in contexts:
                ctx = session.query(Context).filter_by(name=ctx_name).first()
                if ctx:
                    existing = session.query(Tooltip).join(TooltipContext).filter(
                        Tooltip.keyword == keyword,
                        TooltipContext.context_id == ctx.id
                    ).first()
                    if existing:
                        break
            
            if existing:
                # Update existing
                existing.content = content
                existing.content_type = content_type
                existing.updated_at = datetime.utcnow()
                tooltip_id = existing.id
            else:
                # Create new
                tooltip = Tooltip(
                    keyword=keyword,
                    content=content,
                    content_type=content_type
                )
                session.add(tooltip)
                session.flush()  # Get ID
                tooltip_id = tooltip.id
                
                # Assign to contexts
                for ctx_name in contexts:
                    ctx = session.query(Context).filter_by(name=ctx_name).first()
                    if not ctx:
                        # Create context if doesn't exist
                        ctx = Context(name=ctx_name, description=f"Auto-created for {keyword}")
                        session.add(ctx)
                        session.flush()
                    
                    # Create association
                    tc = TooltipContext(tooltip_id=tooltip_id, context_id=ctx.id)
                    session.add(tc)
            
            session.commit()
            session.close()
            
            # Invalidate cache
            for ctx_name in contexts:
                self._invalidate_cache(ctx_name)
            
            logger.info(f"Registered tooltip: {keyword} in contexts: {contexts}")
            return tooltip_id
        
        except Exception as e:
            logger.error(f"Error registering tooltip: {e}")
            raise
    
    def register_batch_tooltips(self, tooltips: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        Bulk insert tooltips.
        
        Args:
            tooltips: List of dicts with keys: keyword, content, contexts, content_type
        
        Returns:
            Dict mapping keyword to success status
        """
        results = {}
        try:
            session = self._get_session()
            
            for item in tooltips:
                keyword = item['keyword']
                try:
                    # Create tooltip
                    tooltip = Tooltip(
                        keyword=keyword,
                        content=item['content'],
                        content_type=item.get('content_type', 'text')
                    )
                    session.add(tooltip)
                    session.flush()
                    
                    # Assign to contexts
                    for ctx_name in item['contexts']:
                        ctx = session.query(Context).filter_by(name=ctx_name).first()
                        if not ctx:
                            ctx = Context(name=ctx_name, description=f"Auto-created")
                            session.add(ctx)
                            session.flush()
                        
                        tc = TooltipContext(tooltip_id=tooltip.id, context_id=ctx.id)
                        session.add(tc)
                    
                    results[keyword] = True
                except Exception as e:
                    logger.error(f"Error in batch for keyword {keyword}: {e}")
                    results[keyword] = False
            
            session.commit()
            session.close()
            
            # Invalidate entire cache
            self._invalidate_cache()
            
            logger.info(f"Batch registered {sum(results.values())}/{len(tooltips)} tooltips")
            return results
        
        except Exception as e:
            logger.error(f"Error in batch registration: {e}")
            return {item['keyword']: False for item in tooltips}
    
    # Management API
    def list_tooltips(
        self,
        context: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """
        List tooltips with filtering.
        
        Returns:
            (tooltip_rows, total_count)
        """
        try:
            session = self._get_session()
            
            query = session.query(Tooltip)
            
            # Filter by context
            if context:
                ctx = session.query(Context).filter_by(name=context).first()
                if ctx:
                    query = query.join(TooltipContext).filter(TooltipContext.context_id == ctx.id)
            
            # Search by keyword
            if search:
                query = query.filter(or_(
                    Tooltip.keyword.ilike(f'%{search}%'),
                    Tooltip.content.ilike(f'%{search}%')
                ))
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            tooltips = query.limit(limit).offset(offset).all()
            
            # Build result with context names
            result = []
            for tooltip in tooltips:
                contexts = [tc.context.name for tc in tooltip.tooltip_contexts]
                result.append({
                    **tooltip.to_dict(),
                    'contexts': contexts
                })
            
            session.close()
            return result, total
        
        except Exception as e:
            logger.error(f"Error listing tooltips: {e}")
            return [], 0
    
    def get_tooltip(self, tooltip_id: int) -> Optional[Dict]:
        """Get single tooltip with all contexts"""
        try:
            session = self._get_session()
            tooltip = session.query(Tooltip).filter_by(id=tooltip_id).first()
            if not tooltip:
                session.close()
                return None
            
            contexts = [tc.context.name for tc in tooltip.tooltip_contexts]
            result = {
                **tooltip.to_dict(),
                'contexts': contexts
            }
            session.close()
            return result
        
        except Exception as e:
            logger.error(f"Error getting tooltip: {e}")
            return None
    
    def update_tooltip(self, tooltip_id: int, **fields):
        """Update tooltip fields"""
        try:
            session = self._get_session()
            tooltip = session.query(Tooltip).filter_by(id=tooltip_id).first()
            if not tooltip:
                session.close()
                return False
            
            for key, value in fields.items():
                if hasattr(tooltip, key):
                    setattr(tooltip, key, value)
            
            tooltip.updated_at = datetime.utcnow()
            session.commit()
            session.close()
            
            self._invalidate_cache()
            return True
        
        except Exception as e:
            logger.error(f"Error updating tooltip: {e}")
            return False
    
    def delete_tooltip(self, tooltip_id: int):
        """Delete tooltip (cascades to TooltipContext)"""
        try:
            session = self._get_session()
            tooltip = session.query(Tooltip).filter_by(id=tooltip_id).first()
            if tooltip:
                session.delete(tooltip)
                session.commit()
            session.close()
            
            self._invalidate_cache()
            return True
        
        except Exception as e:
            logger.error(f"Error deleting tooltip: {e}")
            return False
    
    # Context Management
    def create_context(self, name: str, description: str = "", matching_strategy: str = 'exact') -> int:
        """Create new context"""
        # Prevent creating another Global context
        if name == GLOBAL_CONTEXT_NAME:
            raise ValueError(f"Cannot create context named '{GLOBAL_CONTEXT_NAME}' - it is a reserved system context")
        
        # Validate name
        if not re.match(r'^[a-zA-Z0-9_]+$', name):
            raise ValueError(f"Invalid context name: {name}. Use only alphanumeric and underscore.")
        
        try:
            session = self._get_session()
            ctx = Context(
                name=name,
                description=description,
                matching_strategy=matching_strategy
            )
            session.add(ctx)
            session.commit()
            ctx_id = ctx.id
            session.close()
            
            logger.info(f"Created context: {name}")
            return ctx_id
        
        except Exception as e:
            logger.error(f"Error creating context: {e}")
            raise
    
    def list_contexts(self) -> List[Dict]:
        """List all contexts with tooltip counts"""
        try:
            session = self._get_session()
            contexts = session.query(
                Context,
                func.count(TooltipContext.id).label('tooltip_count')
            ).outerjoin(TooltipContext).group_by(Context.id).all()
            
            result = []
            for ctx, count in contexts:
                result.append({
                    **ctx.to_dict(),
                    'tooltip_count': count
                })
            
            session.close()
            return result
        
        except Exception as e:
            logger.error(f"Error listing contexts: {e}")
            return []
    
    def update_context(self, context_id: int, **fields):
        """Update context fields"""
        try:
            session = self._get_session()
            ctx = session.query(Context).filter_by(id=context_id).first()
            if not ctx:
                session.close()
                return False
            
            for key, value in fields.items():
                if hasattr(ctx, key):
                    setattr(ctx, key, value)
            
            ctx.updated_at = datetime.utcnow()
            session.commit()
            session.close()
            
            self._invalidate_cache(ctx.name)
            return True
        
        except Exception as e:
            logger.error(f"Error updating context: {e}")
            return False
    
    def delete_context(self, context_id: int):
        """Delete context (cascades to TooltipContext)"""
        try:
            session = self._get_session()
            ctx = session.query(Context).filter_by(id=context_id).first()
            if ctx:
                # Prevent deletion of Global context
                if ctx.name == GLOBAL_CONTEXT_NAME:
                    session.close()
                    raise ValueError(f"Cannot delete {GLOBAL_CONTEXT_NAME} context - it is a system context")
                
                ctx_name = ctx.name
                session.delete(ctx)
                session.commit()
                self._invalidate_cache(ctx_name)
            session.close()
            return True
        
        except Exception as e:
            logger.error(f"Error deleting context: {e}")
            return False
    
    def assign_tooltip_to_contexts(self, tooltip_id: int, context_ids: List[int]):
        """Replace all context assignments for tooltip"""
        try:
            session = self._get_session()
            
            # Remove existing assignments
            session.query(TooltipContext).filter_by(tooltip_id=tooltip_id).delete()
            
            # Add new assignments
            for ctx_id in context_ids:
                tc = TooltipContext(tooltip_id=tooltip_id, context_id=ctx_id)
                session.add(tc)
            
            session.commit()
            session.close()
            
            self._invalidate_cache()
            return True
        
        except Exception as e:
            logger.error(f"Error assigning tooltip to contexts: {e}")
            return False
    
    # Import API
    def import_from_csv(
        self,
        csv_content: str,
        context_name: str,
        column_mapping: Dict[str, int],
        content_type: str = 'text',
        auto_html_template: Optional[str] = None
    ) -> Tuple[int, List[str]]:
        """
        Import tooltips from CSV.
        
        Args:
            csv_content: CSV string
            context_name: Assign all to this context
            column_mapping: {"keyword": 0, "content": 1, "image_path": 2}
            content_type: 'text' or 'html'
            auto_html_template: Template string with {image}, {keyword}, {content}
        
        Returns:
            (success_count, error_messages)
        """
        errors = []
        success_count = 0
        
        try:
            # Ensure context exists
            session = self._get_session()
            ctx = session.query(Context).filter_by(name=context_name).first()
            if not ctx:
                ctx = Context(name=context_name, description="CSV imported")
                session.add(ctx)
                session.commit()
            session.close()
            
            # Parse CSV
            reader = csv.reader(io.StringIO(csv_content))
            rows = list(reader)
            
            for idx, row in enumerate(rows):
                try:
                    # Skip header or empty rows
                    if idx == 0 or not row:
                        continue
                    
                    # Extract fields
                    keyword_col = column_mapping.get('keyword')
                    content_col = column_mapping.get('content')
                    image_col = column_mapping.get('image_path')
                    
                    if keyword_col is None or keyword_col >= len(row):
                        errors.append(f"Row {idx+1}: Missing keyword column")
                        continue
                    
                    keyword = row[keyword_col].strip()
                    if not keyword:
                        continue
                    
                    content = row[content_col].strip() if content_col is not None and content_col < len(row) else ""
                    
                    # Handle image
                    if image_col is not None and image_col < len(row) and auto_html_template:
                        image_path = row[image_col].strip()
                        if image_path and Path(image_path).exists():
                            try:
                                base64_img = process_image_to_base64(
                                    image_path,
                                    self.image_max_width,
                                    self.image_max_height,
                                    self.image_quality
                                )
                                content = auto_html_template.format(
                                    image=base64_img,
                                    keyword=keyword,
                                    content=content
                                )
                                content_type = 'html'
                            except Exception as e:
                                errors.append(f"Row {idx+1}: Image error: {e}")
                    
                    # Register tooltip
                    self.register_tooltip(keyword, content, [context_name], content_type)
                    success_count += 1
                
                except Exception as e:
                    errors.append(f"Row {idx+1}: {str(e)}")
            
            return success_count, errors
        
        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            return 0, [str(e)]
