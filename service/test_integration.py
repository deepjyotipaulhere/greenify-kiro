#!/usr/bin/env python3
"""
Integration test for error handling in the Flask app.

Tests the complete error handling flow from the /answer endpoint
through the Gemini client error handling.
"""

import os
import json
import base64
from unittest.mock import patch, Mock
from app import app


def create_test_image():
    """Create a simple test image in base64 format"""
    # Create a minimal valid base64 image (1x1 pixel PNG)
    test_image_bytes = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77yQAAAABJRU5ErkJggg=='
    )
    return base64.b64encode(test_image_bytes).decode('utf-8')


def test_invalid_request_data():
    """Test error handling for invalid request data"""
    print("Testing invalid request data handling...")
    
    with app.test_client() as client:
        # Test with no data
        response = client.post('/answer', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        print("PASS: Invalid request data handled correctly")


def test_missing_fields():
    """Test error handling for missing required fields"""
    print("Testing missing fields handling...")
    
    with app.test_client() as client:
        # Test with missing image
        response = client.post('/answer', json={'location': [40.7128, -74.0060]})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'required' in data['error'].lower()
        
        # Test with missing location
        response = client.post('/answer', json={'image': create_test_image()})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'required' in data['error'].lower()
        
        print("PASS: Missing fields handled correctly")


def test_invalid_location_format():
    """Test error handling for invalid location format"""
    print("Testing invalid location format handling...")
    
    with app.test_client() as client:
        # Test with invalid location format
        response = client.post('/answer', json={
            'image': create_test_image(),
            'location': [40.7128]  # Missing longitude
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'location' in data['error'].lower()
        print("PASS: Invalid location format handled correctly")


def test_gemini_client_creation_failure():
    """Test error handling when Gemini client creation fails"""
    print("Testing Gemini client creation failure...")
    
    with app.test_client() as client:
        # Mock environment without API key
        with patch.dict(os.environ, {}, clear=True):
            response = client.post('/answer', json={
                'image': create_test_image(),
                'location': [40.7128, -74.0060, 10]
            })
            assert response.status_code == 503
            data = response.get_json()
            assert 'error' in data
            assert 'service' in data['error'].lower() or 'unavailable' in data['error'].lower()
            print("PASS: Gemini client creation failure handled correctly")


def main():
    """Run integration tests"""
    print("Running Integration Error Handling Tests")
    print("=" * 50)
    
    # Set up test environment
    os.environ['GEMINI_API_KEY'] = 'test_key_for_integration_testing'
    
    # Run tests
    test_invalid_request_data()
    test_missing_fields()
    test_invalid_location_format()
    test_gemini_client_creation_failure()
    
    print("=" * 50)
    print("Integration error handling tests completed!")


if __name__ == "__main__":
    main()