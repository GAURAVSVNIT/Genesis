"""
Structured logging and error handling for Genesis backend.
Replaces print() statements with proper logging.
"""

import logging
import json
import traceback
from typing import Optional, Any, Dict
from datetime import datetime
import sys
from pathlib import Path


class StructuredLogger:
    """Structured logging with JSON output for production."""
    
    LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    
    def __init__(self, name: str, level: str = "INFO"):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (usually __name__)
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.LEVELS.get(level, logging.INFO))
        
        # Console handler (always)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (for errors and above)
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "genesis.log")
        file_handler.setLevel(logging.WARNING)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def _format_message(
        self,
        level: str,
        message: str,
        **kwargs
    ) -> str:
        """Format message with context."""
        context = {}
        
        # Add timing if provided
        if "duration_ms" in kwargs:
            context["duration_ms"] = kwargs["duration_ms"]
        
        # Add user/request context if provided
        if "user_id" in kwargs:
            context["user_id"] = kwargs["user_id"]
        if "request_id" in kwargs:
            context["request_id"] = kwargs["request_id"]
        
        # Add error details if provided
        if "error" in kwargs:
            context["error"] = str(kwargs["error"])
        if "error_type" in kwargs:
            context["error_type"] = kwargs["error_type"]
        
        # Build final message
        if context:
            context_str = " | " + json.dumps(context)
        else:
            context_str = ""
        
        return f"{message}{context_str}"
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(self._format_message("DEBUG", message, **kwargs))
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(self._format_message("INFO", message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(self._format_message("WARNING", message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """Log error message with traceback."""
        exc_info = kwargs.pop("exc_info", True)
        self.logger.error(
            self._format_message("ERROR", message, **kwargs),
            exc_info=exc_info
        )
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(self._format_message("CRITICAL", message, **kwargs))


class ErrorHandler:
    """Centralized error handling for API endpoints."""
    
    @staticmethod
    def handle_validation_error(error: Any, context: Optional[Dict] = None) -> Dict:
        """
        Handle validation errors (Pydantic, etc.).
        
        Args:
            error: The error exception
            context: Additional context
            
        Returns:
            Formatted error response
        """
        return {
            "success": False,
            "error": {
                "type": "ValidationError",
                "message": str(error),
                "context": context or {}
            }
        }
    
    @staticmethod
    def handle_rate_limit_error(
        reset_after: int,
        limit: int,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Handle rate limit errors.
        
        Args:
            reset_after: Seconds until reset
            limit: Request limit
            context: Additional context
            
        Returns:
            Formatted error response
        """
        return {
            "success": False,
            "error": {
                "type": "RateLimitError",
                "message": f"Rate limit of {limit} requests exceeded",
                "reset_after_seconds": reset_after,
                "context": context or {}
            }
        }
    
    @staticmethod
    def handle_database_error(
        error: Any,
        operation: str = "database operation",
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Handle database errors.
        
        Args:
            error: The error exception
            operation: What operation failed
            context: Additional context
            
        Returns:
            Formatted error response
        """
        return {
            "success": False,
            "error": {
                "type": "DatabaseError",
                "message": f"Failed to complete {operation}",
                "details": str(error),
                "context": context or {}
            }
        }
    
    @staticmethod
    def handle_llm_error(
        error: Any,
        model: str = "unknown",
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Handle LLM API errors.
        
        Args:
            error: The error exception
            model: The model that failed
            context: Additional context
            
        Returns:
            Formatted error response
        """
        error_str = str(error).lower()
        
        # Detect specific error types
        if "rate limit" in error_str:
            error_type = "RateLimitError"
        elif "timeout" in error_str or "timed out" in error_str:
            error_type = "TimeoutError"
        elif "auth" in error_str:
            error_type = "AuthenticationError"
        elif "not found" in error_str or "404" in error_str:
            error_type = "NotFoundError"
        else:
            error_type = "APIError"
        
        return {
            "success": False,
            "error": {
                "type": error_type,
                "message": f"Failed to get response from {model}",
                "details": str(error),
                "context": context or {}
            }
        }
    
    @staticmethod
    def handle_generic_error(
        error: Any,
        operation: str = "operation",
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Handle generic unexpected errors.
        
        Args:
            error: The error exception
            operation: What operation failed
            context: Additional context
            
        Returns:
            Formatted error response
        """
        return {
            "success": False,
            "error": {
                "type": "InternalError",
                "message": f"An unexpected error occurred during {operation}",
                "context": context or {}
            }
        }


class PerformanceMonitor:
    """Monitor and log performance metrics."""
    
    def __init__(self, operation_name: str):
        """
        Initialize performance monitor.
        
        Args:
            operation_name: Name of operation to monitor
        """
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
        self.logger = StructuredLogger(__name__)
    
    def __enter__(self):
        """Start timing."""
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log."""
        import time
        self.end_time = time.time()
        duration_ms = int((self.end_time - self.start_time) * 1000)
        
        if exc_type is not None:
            self.logger.error(
                f"{self.operation_name} failed",
                duration_ms=duration_ms,
                error=str(exc_val),
                error_type=exc_type.__name__
            )
        else:
            self.logger.info(
                f"{self.operation_name} completed",
                duration_ms=duration_ms
            )
        
        return False  # Don't suppress exceptions
    
    @property
    def duration_ms(self) -> int:
        """Get duration in milliseconds."""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time) * 1000)
        return 0


# Module-level logger
logger = StructuredLogger(__name__)


if __name__ == "__main__":
    # Test logging
    test_logger = StructuredLogger("test")
    
    test_logger.info("Application started")
    test_logger.debug("Debug message", user_id="user123")
    test_logger.warning("This is a warning")
    
    # Test error handling
    try:
        raise ValueError("Test error")
    except Exception as e:
        test_logger.error("An error occurred", error=str(e), user_id="user123")
    
    # Test performance monitoring
    import time
    with PerformanceMonitor("Test Operation") as monitor:
        time.sleep(0.1)
    
    print("\n✅ Logging and error handling module working correctly")
