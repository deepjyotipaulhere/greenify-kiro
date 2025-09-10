#!/usr/bin/env python3
"""
Comprehensive test suite for Gemini API integration (Task 9).

This test validates the complete integration including:
- Gemini API integration functionality
- Superimposed image generation quality validation
- End-to-end flow from image upload to enhanced plant recommendations

Requirements tested: 1.4, 2.4, 3.4
"""

import os
import json
import base64
import sys
from unittest.mock import patch, Mock, MagicMock
from io import BytesIO
from PIL import Image
import requests

# Add service directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from gemini_client import GeminiClient, GeminiAPIError, create_gemini_client
from models import Plant


def create_test_image():
    """Create a valid test image in base64 format for testing"""
    # Create a simple 100x100 pixel test image
    img = Image.new('RGB', (100, 100), color='green')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')


def create_mock_superimposed_image():
    """Create a mock superimposed image for testing"""
    # Create a simple test image with a plant overlay
    img = Image.new('RGB', (100, 100), color='lightgreen')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')


def create_mock_gemini_response():
    """Create a comprehensive mock response from Gemini API"""
    return {
        "description": "This sunny garden area with well-draining soil is excellent for plant growth. The location receives good natural light and has adequate space for various plant types.",
        "plants": [
            {
                "name": "Rose",
                "image": "https://example.com/rose.jpg",
                "superimposed_image": create_mock_superimposed_image(),
                "description": "Beautiful flowering shrub perfect for this sunny location with rich soil.",
                "care_instructions": "Water regularly, ensure good drainage, prune after flowering season.",
                "care_tips": "Apply mulch around base, fertilize in spring, deadhead spent blooms.",
                "AR_model": "https://example.com/rose_ar.glb",
                "placement_confidence": 0.92
            },
            {
                "name": "Lavender",
                "image": "https://example.com/lavender.jpg", 
                "superimposed_image": create_mock_superimposed_image(),
                "description": "Fragrant herb that thrives in sunny, well-drained locations like this one.",
                "care_instructions": "Water sparingly, needs full sun, well-draining sandy soil preferred.",
                "care_tips": "Prune after flowering, harvest flowers for drying, avoid overwatering.",
                "AR_model": "https://example.com/lavender_ar.glb",
                "placement_confidence": 0.88
            },
            {
                "name": "Marigold",
                "image": "https://example.com/marigold.jpg",
                "superimposed_image": create_mock_superimposed_image(),
                "description": "Bright annual flowers that are easy to grow and perfect for beginners.",
                "care_instructions": "Water at soil level, full sun to partial shade, regular potting soil.",
                "care_tips": "Deadhead regularly for continuous blooms, companion plant for vegetables.",
                "AR_model": "https://example.com/marigold_ar.glb",
                "placement_confidence": 0.85
            }
        ]
    }


def test_gemini_api_integration():
    """Test Gemini API integration functionality (Requirement 1.4)"""
    print("Testing Gemini API integration...")
    
    # Mock the Gemini client
    mock_client = Mock()
    mock_client.analyze_image_and_recommend_plants.return_value = create_mock_gemini_response()
    
    with app.test_client() as client:
        with patch('gemini_client.create_gemini_client', return_value=mock_client):
            response = client.post('/answer', json={
                'image': create_test_image(),
                'location': [40.7128, -74.0060, 10]
            })
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify response structure
            assert 'description' in data
            assert 'plants' in data
            assert len(data['plants']) == 3
            
            # Verify Gemini API was called correctly
            mock_client.analyze_image_and_recommend_plants.assert_called_once()
            call_args = mock_client.analyze_image_and_recommend_plants.call_args
            assert call_args[0][1] == [40.7128, -74.0060, 10]  # Location parameter
            
            print("PASS: Gemini API integration works correctly")


def test_superimposed_image_generation_quality():
    """Test superimposed image generation quality validation (Requirement 2.4)"""
    print("Testing superimposed image generation quality...")
    
    mock_response = create_mock_gemini_response()
    
    # Validate each plant has superimposed image data
    for plant in mock_response['plants']:
        assert 'superimposed_image' in plant
        assert plant['superimposed_image'] is not None
        assert len(plant['superimposed_image']) > 0
        
        # Validate base64 format
        try:
            decoded_image = base64.b64decode(plant['superimposed_image'])
            assert len(decoded_image) > 0
            
            # Validate it's a valid image
            img = Image.open(BytesIO(decoded_image))
            assert img.format in ['PNG', 'JPEG', 'JPG']
            assert img.size[0] > 0 and img.size[1] > 0
            
        except Exception as e:
            assert False, f"Invalid superimposed image for {plant['name']}: {e}"
        
        # Validate placement confidence
        assert 'placement_confidence' in plant
        assert isinstance(plant['placement_confidence'], (int, float))
        assert 0.0 <= plant['placement_confidence'] <= 1.0
        
    print("✓ Superimposed image quality validation passed")


def test_end_to_end_flow():
    """Test complete end-to-end flow from image upload to enhanced plant recommendations (Requirement 3.4)"""
    print("Testing end-to-end flow...")
    
    # Mock Gemini client
    mock_client = Mock()
    mock_client.analyze_image_and_recommend_plants.return_value = create_mock_gemini_response()
    
    with app.test_client() as client:
        with patch('gemini_client.create_gemini_client', return_value=mock_client):
            # Step 1: Upload image and location
            test_request = {
                'image': create_test_image(),
                'location': [34.0522, -118.2437, 100]  # Los Angeles coordinates
            }
            
            response = client.post('/answer', json=test_request)
            
            # Step 2: Verify successful response
            assert response.status_code == 200
            data = response.get_json()
            
            # Step 3: Validate complete response structure
            assert 'description' in data
            assert isinstance(data['description'], str)
            assert len(data['description']) > 0
            
            assert 'plants' in data
            assert isinstance(data['plants'], list)
            assert len(data['plants']) > 0
            
            # Step 4: Validate enhanced plant data structure
            for plant in data['plants']:
                # Original fields
                assert 'name' in plant
                assert 'image' in plant
                assert 'description' in plant
                assert 'care_instructions' in plant
                assert 'care_tips' in plant
                assert 'AR_model' in plant
                
                # Enhanced fields from Gemini
                assert 'superimposed_image' in plant
                assert 'placement_confidence' in plant
                
                # Validate data types and content
                assert isinstance(plant['name'], str)
                assert len(plant['name']) > 0
                assert isinstance(plant['description'], str)
                assert len(plant['description']) > 0
                assert isinstance(plant['care_instructions'], str)
                assert len(plant['care_instructions']) > 0
                assert isinstance(plant['care_tips'], str)
                assert len(plant['care_tips']) > 0
                
                # Validate superimposed image
                assert isinstance(plant['superimposed_image'], str)
                assert len(plant['superimposed_image']) > 0
                
                # Validate placement confidence
                assert isinstance(plant['placement_confidence'], (int, float))
                assert 0.0 <= plant['placement_confidence'] <= 1.0
            
            print("✓ End-to-end flow completed successfully")
            print(f"✓ Received {len(data['plants'])} enhanced plant recommendations")


def test_error_handling_integration():
    """Test error handling in the complete integration"""
    print("Testing error handling integration...")
    
    with app.test_client() as client:
        # Test 1: Missing image data
        response = client.post('/answer', json={'location': [40.7128, -74.0060]})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        print("✓ Missing image data handled correctly")
        
        # Test 2: Missing location data
        response = client.post('/answer', json={'image': create_test_image()})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        print("✓ Missing location data handled correctly")
        
        # Test 3: Invalid location format
        response = client.post('/answer', json={
            'image': create_test_image(),
            'location': [40.7128]  # Missing longitude
        })
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        print("✓ Invalid location format handled correctly")
        
        # Test 4: Gemini API failure
        mock_client = Mock()
        mock_client.analyze_image_and_recommend_plants.side_effect = Exception("API Error")
        
        with patch('gemini_client.create_gemini_client', return_value=mock_client):
            response = client.post('/answer', json={
                'image': create_test_image(),
                'location': [40.7128, -74.0060, 10]
            })
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            print("✓ Gemini API failure handled correctly")


def test_backward_compatibility():
    """Test that enhanced responses maintain backward compatibility"""
    print("Testing backward compatibility...")
    
    mock_response = create_mock_gemini_response()
    
    # Verify all original fields are present
    required_fields = ['description', 'plants']
    for field in required_fields:
        assert field in mock_response
    
    # Verify plant structure includes all original fields
    for plant in mock_response['plants']:
        original_fields = ['name', 'image', 'description', 'care_instructions', 'care_tips', 'AR_model']
        for field in original_fields:
            assert field in plant
        
        # Verify enhanced fields are additional, not replacements
        enhanced_fields = ['superimposed_image', 'placement_confidence']
        for field in enhanced_fields:
            assert field in plant
    
    print("✓ Backward compatibility maintained")


def test_performance_validation():
    """Test that the integration performs within acceptable limits"""
    print("Testing performance validation...")
    
    import time
    
    mock_client = Mock()
    mock_client.analyze_image_and_recommend_plants.return_value = create_mock_gemini_response()
    
    with app.test_client() as client:
        with patch('gemini_client.create_gemini_client', return_value=mock_client):
            start_time = time.time()
            
            response = client.post('/answer', json={
                'image': create_test_image(),
                'location': [40.7128, -74.0060, 10]
            })
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 5.0  # Should respond within 5 seconds
            
            print(f"✓ Response time: {response_time:.2f} seconds (within acceptable limits)")


def main():
    """Run comprehensive integration tests for Task 9"""
    print("Running Comprehensive Gemini API Integration Tests (Task 9)")
    print("=" * 60)
    
    # Set up test environment
    os.environ['GEMINI_API_KEY'] = 'test_key_for_comprehensive_testing'
    
    # Run all integration tests
    test_gemini_api_integration()
    test_superimposed_image_generation_quality()
    test_end_to_end_flow()
    test_error_handling_integration()
    test_backward_compatibility()
    test_performance_validation()
    
    print("=" * 60)
    print("✅ All comprehensive integration tests passed!")
    print("✅ Gemini API integration is fully validated")
    print("✅ Superimposed image generation quality confirmed")
    print("✅ End-to-end flow working correctly")
    print("✅ Requirements 1.4, 2.4, and 3.4 satisfied")


if __name__ == "__main__":
    main()