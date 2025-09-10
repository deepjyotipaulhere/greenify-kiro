#!/usr/bin/env python3
"""
Test script for Gemini API error handling implementation.

This script tests the error handling functionality implemented in task 7
to ensure it meets the requirements 6.1, 6.2, 6.3, and 6.4.
"""

import os
import sys
import json
from unittest.mock import Mock, patch
from gemini_client import GeminiClient, GeminiAPIError, create_gemini_client


def test_authentication_error_handling():
    """Test handling of authentication errors (Requirement 6.1)"""
    print("Testing authentication error handling...")
    
    try:
        # Test with invalid API key
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'invalid_key'}):
            client = GeminiClient()
            
            # Simulate authentication error
            auth_error = Exception("Authentication failed: Invalid API key")
            error_response = client.handle_api_errors(auth_error)
            
            assert "error" in error_response
            assert isinstance(error_response["error"], str)
            assert "authentication" in error_response["error"].lower() or "credential" in error_response["error"].lower()
            assert error_response["plants"] == []
            print("PASS: Authentication error handling works correctly")
            
    except Exception as e:
        print(f"FAIL: Authentication error test failed: {e}")


def test_quota_error_handling():
    """Test handling of quota exceeded errors (Requirement 6.4)"""
    print("Testing quota error handling...")
    
    try:
        client = GeminiClient()
        
        # Simulate quota exceeded error
        quota_error = Exception("Quota exceeded: API rate limit reached")
        error_response = client.handle_api_errors(quota_error)
        
        assert isinstance(error_response["error"], str)
        assert "quota" in error_response["error"].lower() or "limit" in error_response["error"].lower() or "demand" in error_response["error"].lower()
        assert len(error_response["plants"]) > 0  # Should provide fallback plants
        print("PASS: Quota error handling works correctly")
        
    except Exception as e:
        print(f"FAIL: Quota error test failed: {e}")


def test_network_error_handling():
    """Test handling of network errors (Requirement 6.3)"""
    print("Testing network error handling...")
    
    try:
        client = GeminiClient()
        
        # Simulate network error
        network_error = Exception("Network connection failed: Unable to reach server")
        error_response = client.handle_api_errors(network_error)
        
        assert isinstance(error_response["error"], str)
        assert "network" in error_response["error"].lower() or "connection" in error_response["error"].lower()
        assert len(error_response["plants"]) > 0  # Should provide fallback plants
        print("PASS: Network error handling works correctly")
        
    except Exception as e:
        print(f"FAIL: Network error test failed: {e}")


def test_malformed_response_handling():
    """Test handling of malformed responses (Requirement 6.2)"""
    print("Testing malformed response handling...")
    
    try:
        client = GeminiClient()
        
        # Test fallback response creation
        fallback_response = client._create_comprehensive_fallback_response("Invalid JSON response")
        
        assert "description" in fallback_response
        assert "plants" in fallback_response
        assert len(fallback_response["plants"]) > 0
        
        # Verify plant structure
        for plant in fallback_response["plants"]:
            assert "name" in plant
            assert "description" in plant
            assert "care_instructions" in plant
            assert "care_tips" in plant
            assert "superimposed_image" in plant
            assert "placement_confidence" in plant
            
        print("PASS: Malformed response handling works correctly")
        
    except Exception as e:
        print(f"FAIL: Malformed response test failed: {e}")


def test_fallback_plants():
    """Test that fallback plants are properly structured"""
    print("Testing fallback plants structure...")
    
    try:
        client = GeminiClient()
        fallback_plants = client._get_fallback_plants()
        
        assert len(fallback_plants) > 0
        
        for plant in fallback_plants:
            # Verify all required fields are present
            required_fields = ["name", "description", "care_instructions", "care_tips", 
                             "superimposed_image", "placement_confidence"]
            for field in required_fields:
                assert field in plant, f"Missing field: {field}"
            
            # Verify placement_confidence is valid
            confidence = plant["placement_confidence"]
            assert isinstance(confidence, (int, float))
            assert 0.0 <= confidence <= 1.0
            
        print("PASS: Fallback plants structure is correct")
        
    except Exception as e:
        print(f"FAIL: Fallback plants test failed: {e}")


def test_image_validation_errors():
    """Test handling of image validation errors"""
    print("Testing image validation error handling...")
    
    try:
        client = GeminiClient()
        
        # Test with invalid image data
        try:
            client._prepare_image_for_api("invalid_base64_data")
            print("FAIL: Should have raised GeminiAPIError for invalid image")
        except GeminiAPIError as e:
            assert e.error_type == "image"
            print("PASS: Image validation error handling works correctly")
            
    except Exception as e:
        print(f"FAIL: Image validation test failed: {e}")


def main():
    """Run all error handling tests"""
    print("Running Gemini API Error Handling Tests")
    print("=" * 50)
    
    # Set up test environment
    if not os.getenv('GEMINI_API_KEY'):
        os.environ['GEMINI_API_KEY'] = 'test_key_for_testing'
    
    # Run tests
    test_authentication_error_handling()
    test_quota_error_handling()
    test_network_error_handling()
    test_malformed_response_handling()
    test_fallback_plants()
    test_image_validation_errors()
    
    print("=" * 50)
    print("Error handling tests completed!")


if __name__ == "__main__":
    main()