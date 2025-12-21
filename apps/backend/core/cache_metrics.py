"""
Cache metrics tracking service for monitoring hit rates, response times, and storage usage.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from database.models.cache import CacheMetrics
import uuid
import json


class CacheMetricsTracker:
    """Tracks cache performance metrics."""
    
    def __init__(self):
        self.current_hits = 0
        self.current_misses = 0
        self.response_times = []
        self.generation_times = []
    
    @staticmethod
    def record_cache_hit(db: Session):
        """Record a cache hit."""
        try:
            # Get or create current metrics record
            latest_metrics = db.query(CacheMetrics).order_by(
                CacheMetrics.recorded_at.desc()
            ).first()
            
            if latest_metrics and (datetime.utcnow() - latest_metrics.recorded_at).total_seconds() < 3600:
                # Update existing record (same hour)
                latest_metrics.cache_hits += 1
                latest_metrics.total_requests += 1
            else:
                # Create new record for new hour
                latest_metrics = CacheMetrics(
                    id=str(uuid.uuid4()),
                    cache_hits=1,
                    cache_misses=0,
                    total_requests=1,
                    recorded_at=datetime.utcnow()
                )
                db.add(latest_metrics)
            
            db.commit()
            print(f"[Metrics] Recorded cache hit | Total hits: {latest_metrics.cache_hits}, Misses: {latest_metrics.cache_misses}")
        except Exception as e:
            print(f"[Metrics] Warning - could not record hit: {str(e)}")
    
    @staticmethod
    def record_cache_miss(db: Session):
        """Record a cache miss."""
        try:
            # Get or create current metrics record
            latest_metrics = db.query(CacheMetrics).order_by(
                CacheMetrics.recorded_at.desc()
            ).first()
            
            if latest_metrics and (datetime.utcnow() - latest_metrics.recorded_at).total_seconds() < 3600:
                # Update existing record (same hour)
                latest_metrics.cache_misses += 1
                latest_metrics.total_requests += 1
            else:
                # Create new record for new hour
                latest_metrics = CacheMetrics(
                    id=str(uuid.uuid4()),
                    cache_hits=0,
                    cache_misses=1,
                    total_requests=1,
                    recorded_at=datetime.utcnow()
                )
                db.add(latest_metrics)
            
            db.commit()
            print(f"[Metrics] Recorded cache miss | Total hits: {latest_metrics.cache_hits}, Misses: {latest_metrics.cache_misses}")
        except Exception as e:
            print(f"[Metrics] Warning - could not record miss: {str(e)}")
    
    @staticmethod
    def record_response_time(db: Session, response_time_ms: float):
        """Record response time for averaging."""
        try:
            latest_metrics = db.query(CacheMetrics).order_by(
                CacheMetrics.recorded_at.desc()
            ).first()
            
            if latest_metrics and (datetime.utcnow() - latest_metrics.recorded_at).total_seconds() < 3600:
                # Update average response time
                current_avg = latest_metrics.avg_response_time
                total_requests = latest_metrics.total_requests
                new_avg = (current_avg * (total_requests - 1) + response_time_ms) / total_requests
                latest_metrics.avg_response_time = new_avg
                db.commit()
                print(f"[Metrics] Response time recorded: {response_time_ms:.2f}ms | Avg: {new_avg:.2f}ms")
        except Exception as e:
            print(f"[Metrics] Warning - could not record response time: {str(e)}")
    
    @staticmethod
    def get_current_metrics(db: Session) -> Optional[dict]:
        """Get current cache metrics."""
        try:
            latest_metrics = db.query(CacheMetrics).order_by(
                CacheMetrics.recorded_at.desc()
            ).first()
            
            if latest_metrics:
                return {
                    "cache_hits": latest_metrics.cache_hits,
                    "cache_misses": latest_metrics.cache_misses,
                    "hit_rate": latest_metrics.hit_rate,
                    "avg_response_time": latest_metrics.avg_response_time,
                    "avg_generation_time": latest_metrics.avg_generation_time,
                    "storage_size_mb": latest_metrics.storage_size_mb,
                    "recorded_at": latest_metrics.recorded_at.isoformat()
                }
            return None
        except Exception as e:
            print(f"[Metrics] Error getting metrics: {str(e)}")
            return None


def get_cache_metrics_tracker() -> CacheMetricsTracker:
    """Get singleton instance of metrics tracker."""
    return CacheMetricsTracker()
