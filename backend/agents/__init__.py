# backend/agents/__init__.py
try:
    from .misinformation_agent import agent_service
    __all__ = ['agent_service']
except ImportError:
    # Create a fallback agent service for when the real one can't be imported
    import logging
    from datetime import datetime
    import json
    import os
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("fallback-agent")
    
    class FallbackAgentService:
        """A fallback implementation when the real agent service can't be loaded."""
        
        def __init__(self):
            logger.info("Using fallback agent service")
            self.latest_results = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "message": "Using fallback agent service",
                "analysis": "The AI agent module couldn't be loaded. Basic trend analysis is being used instead.",
                "fallback": True
            }
        
        def get_latest_results(self):
            return self.latest_results
        
        def analyze_trends(self):
            self.latest_results = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "message": "Fallback analysis completed",
                "analysis": "This is a fallback analysis as the AI agent module couldn't be loaded. Consider installing the required dependencies or checking logs for more details.",
                "fallback": True
            }
            return self.latest_results
    
    # Create the fallback service
    agent_service = FallbackAgentService()
    __all__ = ['agent_service']
