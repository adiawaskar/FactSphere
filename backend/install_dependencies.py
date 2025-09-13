# backend/install_dependencies.py
import subprocess
import sys
import os
import importlib
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("dependency-checker")

def check_dependency(module_name, package_name=None):
    """Check if a module is installed and install if missing."""
    if package_name is None:
        package_name = module_name
        
    try:
        importlib.import_module(module_name)
        logger.info(f"✅ {module_name} is installed")
        return True
    except ImportError:
        logger.warning(f"❌ {module_name} is not installed")
        return False

def install_dependencies():
    """Install all required dependencies."""
    requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    
    if not os.path.exists(requirements_file):
        logger.error(f"Requirements file not found: {requirements_file}")
        return False
    
    logger.info("Installing dependencies from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
        logger.info("All dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing dependencies: {e}")
        return False

def verify_dependencies():
    """Verify that critical dependencies are installed."""
    dependencies = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("langchain", "langchain"),
        ("langchain_community", "langchain-community"),
        ("transformers", "transformers"),
        ("newspaper", "newspaper3k"),
        ("bs4", "beautifulsoup4"),
        ("requests", "requests"),
        ("pandas", "pandas"),
        ("nltk", "nltk"),
        ("duckduckgo_search", "duckduckgo-search"),
        ("huggingface_hub", "huggingface-hub"),
    ]
    
    missing = []
    for module_name, package_name in dependencies:
        if not check_dependency(module_name, package_name):
            missing.append(package_name)
    
    if missing:
        logger.warning(f"Missing dependencies: {', '.join(missing)}")
        return False
    else:
        logger.info("All critical dependencies are installed!")
        return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        verify_dependencies()
    else:
        install_dependencies()
        verify_dependencies()
