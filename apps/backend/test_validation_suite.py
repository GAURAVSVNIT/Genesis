"""
Comprehensive validation test suite for Genesis implementation.
Tests all critical paths to ensure production readiness.
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


class TestSuite:
    """Comprehensive test suite for Genesis."""
    
    def __init__(self):
        """Initialize test suite."""
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.start_time = None
        self.end_time = None
    
    def run_all(self):
        """Run all tests."""
        print("\n" + "="*80)
        print("🧪 GENESIS IMPLEMENTATION VALIDATION TEST SUITE")
        print("="*80 + "\n")
        
        self.start_time = time.time()
        
        # Test categories
        self.test_database()
        self.test_imports()
        self.test_config()
        self.test_guardrails()
        self.test_token_counter()
        self.test_cost_calculation()
        self.test_logging()
        self.test_error_handling()
        
        self.end_time = time.time()
        self.print_summary()
    
    def test_database(self):
        """Test database connectivity and models."""
        print("\n📦 DATABASE TESTS")
        print("-" * 80)
        
        try:
            from database.database import SessionLocal
            from database.models.user import User
            from database.models.conversation import Conversation, Message
            from database.models.content import GeneratedContent, ContentEmbedding
            from database.models.cache import (
                ConversationCache, MessageCache, PromptCache, CacheMetrics
            )
            from database.models.advanced import ContentVersion, MessageFeedback
            from database.models.analytics import UsageStatistics
            
            # Test connection
            db = SessionLocal()
            try:
                db.execute("SELECT 1")
                db.close()
                self.pass_test("Database connection works")
            except Exception as e:
                self.fail_test(f"Database connection failed: {e}")
                return
            
            # Test models imported
            models = [
                User, Conversation, Message, GeneratedContent, ContentEmbedding,
                ConversationCache, MessageCache, PromptCache, CacheMetrics,
                ContentVersion, MessageFeedback, UsageStatistics
            ]
            self.pass_test(f"All {len(models)} database models loaded")
            
        except Exception as e:
            self.fail_test(f"Database test failed: {e}")
            self.errors.append(f"Database: {str(e)}")
    
    def test_imports(self):
        """Test critical imports."""
        print("\n🔌 IMPORT TESTS")
        print("-" * 80)
        
        imports_to_test = [
            ("FastAPI", "from fastapi import FastAPI, APIRouter, HTTPException"),
            ("Pydantic", "from pydantic import BaseModel, BaseSettings"),
            ("SQLAlchemy", "from sqlalchemy import Column, String, Integer"),
            ("LangChain", "from langchain_core.messages import HumanMessage, AIMessage"),
            ("LangGraph", "from langgraph.graph import StateGraph"),
            ("Vertex AI", "from langchain_google_vertexai import ChatVertexAI"),
        ]
        
        for name, import_statement in imports_to_test:
            try:
                exec(import_statement)
                self.pass_test(f"{name} import successful")
            except ImportError as e:
                self.fail_test(f"{name} import failed: {e}")
                self.errors.append(f"Import {name}: {str(e)}")
    
    def test_config(self):
        """Test configuration loading."""
        print("\n⚙️  CONFIGURATION TESTS")
        print("-" * 80)
        
        try:
            from core.config import settings
            
            # Check required settings
            required = ["GCP_PROJECT_ID"]
            for setting in required:
                if hasattr(settings, setting):
                    self.pass_test(f"Setting {setting} available")
                else:
                    self.fail_test(f"Setting {setting} missing")
            
        except Exception as e:
            self.fail_test(f"Configuration test failed: {e}")
            self.errors.append(f"Config: {str(e)}")
    
    def test_guardrails(self):
        """Test safety guardrails."""
        print("\n🛡️  GUARDRAILS TESTS")
        print("-" * 80)
        
        try:
            from core.guardrails import get_message_guardrails, SafetyLevel
            
            # Test different safety levels
            for level in ["strict", "moderate", "permissive"]:
                guardrails = get_message_guardrails(level)
                self.pass_test(f"Safety level '{level}' initialized")
            
            # Test safe message
            guardrails = get_message_guardrails("moderate")
            result = guardrails.validate_user_message("Hello, how are you?", role="user")
            if result.is_safe:
                self.pass_test("Safe message validated correctly")
            else:
                self.fail_test("Safe message incorrectly marked unsafe")
            
            # Test harmful message (injection)
            result = guardrails.validate_user_message("'; DROP TABLE users; --", role="user")
            if not result.is_safe:
                self.pass_test("Injection attack detected correctly")
            else:
                self.fail_test("Injection attack not detected")
            
        except Exception as e:
            self.fail_test(f"Guardrails test failed: {e}")
            self.errors.append(f"Guardrails: {str(e)}")
    
    def test_token_counter(self):
        """Test token counting."""
        print("\n🔢 TOKEN COUNTER TESTS")
        print("-" * 80)
        
        try:
            from core.token_counter import get_token_counter
            
            counter = get_token_counter()
            
            # Test empty text
            tokens = counter.count_tokens("")
            if tokens == 0:
                self.pass_test("Empty text counts as 0 tokens")
            else:
                self.fail_test(f"Empty text counted as {tokens} tokens")
            
            # Test simple text
            text = "This is a test sentence."
            tokens = counter.count_tokens(text)
            if 3 <= tokens <= 6:  # Should be around 4-5 tokens
                self.pass_test(f"Simple text counted as {tokens} tokens (reasonable)")
            else:
                self.fail_test(f"Token count {tokens} seems unreasonable")
            
            # Test long text
            long_text = " ".join(["word"] * 100)
            tokens = counter.count_tokens(long_text)
            if tokens > 30:  # 100 words should be many tokens
                self.pass_test(f"Long text counted as {tokens} tokens")
            else:
                self.fail_test(f"Long text token count {tokens} too low")
            
        except Exception as e:
            self.fail_test(f"Token counter test failed: {e}")
            self.errors.append(f"TokenCounter: {str(e)}")
    
    def test_cost_calculation(self):
        """Test cost calculation."""
        print("\n💰 COST CALCULATION TESTS")
        print("-" * 80)
        
        try:
            from core.token_counter import CostCalculator
            
            # Test zero cost
            cost = CostCalculator.calculate_cost("gemini-2.0-flash", 0, 0)
            if cost == 0.0:
                self.pass_test("Zero tokens = zero cost")
            else:
                self.fail_test(f"Zero tokens = ${cost}")
            
            # Test small cost
            cost = CostCalculator.calculate_cost("gemini-2.0-flash", 100, 200)
            if 0 < cost < 0.01:  # Should be tiny
                self.pass_test(f"100 input + 200 output tokens = ${cost}")
            else:
                self.fail_test(f"Cost ${cost} out of expected range")
            
            # Test pricing info
            pricing = CostCalculator.get_pricing_info("gemini-2.0-flash")
            if "input_cost_per_1m" in pricing and "output_cost_per_1m" in pricing:
                self.pass_test("Pricing information available")
            else:
                self.fail_test("Pricing information incomplete")
            
            # Test monthly estimate
            monthly = CostCalculator.estimate_monthly_cost(
                "gemini-2.0-flash",
                daily_requests=100,
                avg_input_tokens=100,
                avg_output_tokens=200
            )
            if 0 < monthly < 100:  # Should be reasonable
                self.pass_test(f"Monthly cost estimate: ${monthly:.2f}")
            else:
                self.fail_test(f"Monthly cost ${monthly} unreasonable")
            
        except Exception as e:
            self.fail_test(f"Cost calculation test failed: {e}")
            self.errors.append(f"CostCalculator: {str(e)}")
    
    def test_logging(self):
        """Test logging system."""
        print("\n📝 LOGGING TESTS")
        print("-" * 80)
        
        try:
            from core.logging_handler import StructuredLogger, PerformanceMonitor
            
            # Test logger creation
            logger = StructuredLogger("test")
            self.pass_test("StructuredLogger created")
            
            # Test logging methods
            logger.info("Test info message")
            logger.warning("Test warning message")
            self.pass_test("Logger methods work")
            
            # Test performance monitor
            with PerformanceMonitor("Test Operation") as monitor:
                time.sleep(0.01)
            
            if monitor.duration_ms > 0:
                self.pass_test(f"Performance monitor: {monitor.duration_ms}ms")
            else:
                self.fail_test("Performance monitor duration 0")
            
        except Exception as e:
            self.fail_test(f"Logging test failed: {e}")
            self.errors.append(f"Logging: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling."""
        print("\n🚨 ERROR HANDLING TESTS")
        print("-" * 80)
        
        try:
            from core.logging_handler import ErrorHandler
            
            # Test validation error
            error = ErrorHandler.handle_validation_error(
                ValueError("test"),
                {"field": "test"}
            )
            if error["success"] == False and error["error"]["type"] == "ValidationError":
                self.pass_test("Validation error handling works")
            else:
                self.fail_test("Validation error format incorrect")
            
            # Test rate limit error
            error = ErrorHandler.handle_rate_limit_error(60, 5)
            if error["success"] == False and error["error"]["type"] == "RateLimitError":
                self.pass_test("Rate limit error handling works")
            else:
                self.fail_test("Rate limit error format incorrect")
            
            # Test database error
            error = ErrorHandler.handle_database_error(
                Exception("connection failed"),
                "insert"
            )
            if error["success"] == False and error["error"]["type"] == "DatabaseError":
                self.pass_test("Database error handling works")
            else:
                self.fail_test("Database error format incorrect")
            
        except Exception as e:
            self.fail_test(f"Error handling test failed: {e}")
            self.errors.append(f"ErrorHandler: {str(e)}")
    
    def pass_test(self, message: str):
        """Record passing test."""
        self.passed += 1
        print(f"  ✅ {message}")
    
    def fail_test(self, message: str):
        """Record failing test."""
        self.failed += 1
        print(f"  ❌ {message}")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        
        total = self.passed + self.failed
        passed_pct = (self.passed / total * 100) if total > 0 else 0
        duration = self.end_time - self.start_time
        
        print(f"\n  Total Tests:  {total}")
        print(f"  ✅ Passed:   {self.passed}")
        print(f"  ❌ Failed:   {self.failed}")
        print(f"  Success Rate: {passed_pct:.1f}%")
        print(f"  Duration:    {duration:.2f}s")
        
        if self.errors:
            print(f"\n⚠️  ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"    - {error}")
        
        print("\n" + "="*80)
        
        if self.failed == 0:
            print("🎉 ALL TESTS PASSED - READY FOR PRODUCTION")
        else:
            print(f"⚠️  {self.failed} TEST(S) FAILED - NEEDS ATTENTION")
        
        print("="*80 + "\n")
        
        return self.failed == 0


def main():
    """Run test suite."""
    suite = TestSuite()
    success = suite.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
