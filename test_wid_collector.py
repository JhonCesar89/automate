#!/usr/bin/env python3
"""
Test script to verify WID collector functionality.
Run this after setting up your .env file with credentials.

Usage:
    python test_wid_collector.py [service_id]
    
Example:
    python test_wid_collector.py 14815103
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from collectors import WIDCollector, ServiceData


def test_connection():
    """Test basic connection to WID."""
    logger.info("Testing WID connection...")
    
    collector = WIDCollector(headless=False)  # Set to False to see browser
    
    try:
        if collector.connect():
            logger.success("✓ Connection successful!")
            return True
        else:
            logger.error("✗ Connection failed")
            return False
    finally:
        collector.disconnect()


def test_service_search(service_id: str):
    """Test searching for a specific service."""
    logger.info(f"Testing service search for: {service_id}")
    
    with WIDCollector(headless=False) as collector:
        service = collector.search_by_service(service_id)
        
        if service:
            logger.success(f"✓ Found service: {service_id}")
            print("\n" + "="*50)
            print("SERVICE DATA EXTRACTED:")
            print("="*50)
            
            # Print all non-None fields
            for field, value in vars(service).items():
                if value is not None and field not in ['raw_data', 'collected_at']:
                    print(f"  {field}: {value}")
            
            print("\n" + "-"*50)
            print("RAW DATA FROM WID:")
            print("-"*50)
            for key, value in service.raw_data.items():
                print(f"  {key}: {value}")
            
            return service
        else:
            logger.error(f"✗ Service not found: {service_id}")
            return None


def main():
    """Run tests based on command line arguments."""
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", 
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
    
    # Check for service ID argument
    if len(sys.argv) > 1:
        service_id = sys.argv[1]
        test_service_search(service_id)
    else:
        # Default: just test connection
        print("\n" + "="*50)
        print("WID COLLECTOR TEST")
        print("="*50)
        print("\nUsage: python test_wid_collector.py [service_id]")
        print("Example: python test_wid_collector.py 14815103\n")
        
        # Test connection only
        test_connection()


if __name__ == "__main__":
    main()
