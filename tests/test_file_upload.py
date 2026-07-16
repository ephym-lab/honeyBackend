"""
Test script for file upload service

This script tests the file upload functionality without requiring a full API call.
Run this after configuring your Supabase credentials in .env
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.file_service import (
    get_supabase_client,
    upload_file_to_supabase,
    get_file_url_from_supabase,
    delete_file_from_supabase
)
from app.config import settings


def test_supabase_connection():
    """Test Supabase client connection"""
    print("Testing Supabase connection...")
    
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("❌ FAILED: Supabase credentials not configured in .env")
        print(f"   SUPABASE_URL: {'✓' if settings.SUPABASE_URL else '✗'}")
        print(f"   SUPABASE_KEY: {'✓' if settings.SUPABASE_KEY else '✗'}")
        return False
    
    client = get_supabase_client()
    if client:
        print("✅ SUCCESS: Supabase client created successfully")
        return True
    else:
        print("❌ FAILED: Could not create Supabase client")
        return False


def test_file_upload():
    """Test file upload functionality"""
    print("\nTesting file upload...")
    
    # Create a test image file
    test_file_path = "/tmp/test_candle.txt"
    test_content = "This is a test file for candle product"
    
    try:
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        # Upload the file
        url = upload_file_to_supabase(
            file_path=test_file_path,
            filename="test_candle.txt",
            file_type='images'
        )
        
        print(f"✅ SUCCESS: File uploaded successfully")
        print(f"   URL: {url}")
        return True, url
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False, None
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)


def test_file_url_retrieval(filename="test_candle.txt"):
    """Test getting file URL"""
    print("\nTesting file URL retrieval...")
    
    try:
        url = get_file_url_from_supabase(
            file_path=filename,
            file_type='images'
        )
        
        print(f"✅ SUCCESS: File URL retrieved")
        print(f"   URL: {url}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def test_file_deletion(filename="test_candle.txt"):
    """Test file deletion"""
    print("\nTesting file deletion...")
    
    try:
        result = delete_file_from_supabase(
            file_name=filename,
            file_type='images'
        )
        
        if result:
            print(f"✅ SUCCESS: File deleted successfully")
            return True
        else:
            print(f"❌ FAILED: File deletion returned False")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("File Upload Service Test Suite")
    print("=" * 60)
    
    # Test 1: Connection
    if not test_supabase_connection():
        print("\n⚠️  Cannot proceed with tests - Supabase not configured")
        print("Please add your Supabase credentials to .env file:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_KEY")
        return
    
    # Test 2: Upload
    upload_success, url = test_file_upload()
    if not upload_success:
        print("\n⚠️  Upload test failed - skipping remaining tests")
        return
    
    # Test 3: URL Retrieval
    test_file_url_retrieval()
    
    # Test 4: Deletion
    test_file_deletion()
    
    print("\n" + "=" * 60)
    print("Test suite completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
