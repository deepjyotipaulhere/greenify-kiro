#!/usr/bin/env python3
"""
Test community endpoint compatibility with Gemini-enhanced plant data.

Tests that the community matching algorithm works with both:
1. Legacy format: simple plant name strings
2. Enhanced format: full Plant objects with superimposed_image and placement_confidence
"""

import json
import os
from unittest.mock import patch, Mock
from app import app, extract_plant_names, normalize_user_data_for_community


def test_extract_plant_names():
    """Test plant name extraction from various formats"""
    print("Testing plant name extraction...")
    
    # Test with simple string array (legacy format)
    legacy_plants = ["Rose", "Jasmine", "Hibiscus"]
    extracted = extract_plant_names(legacy_plants)
    assert extracted == ["Rose", "Jasmine", "Hibiscus"]
    print("PASS: Legacy plant name extraction works")
    
    # Test with enhanced Plant objects (Gemini format)
    enhanced_plants = [
        {
            "name": "Rose",
            "image": "https://example.com/rose.jpg",
            "superimposed_image": "base64_encoded_image_data",
            "placement_confidence": 0.85,
            "description": "Beautiful flowering plant",
            "care_instructions": "Water regularly",
            "care_tips": "Prune in spring",
            "AR_model": "https://example.com/rose_ar.glb"
        },
        {
            "name": "Jasmine",
            "image": "https://example.com/jasmine.jpg",
            "superimposed_image": "base64_encoded_image_data_2",
            "placement_confidence": 0.92,
            "description": "Fragrant flowering vine",
            "care_instructions": "Needs support structure",
            "care_tips": "Fertilize monthly",
            "AR_model": "https://example.com/jasmine_ar.glb"
        }
    ]
    extracted = extract_plant_names(enhanced_plants)
    assert extracted == ["Rose", "Jasmine"]
    print("PASS: Enhanced plant name extraction works")
    
    # Test with mixed format
    mixed_plants = [
        "Hibiscus",
        {
            "name": "Marigold",
            "superimposed_image": "base64_data",
            "placement_confidence": 0.78
        }
    ]
    extracted = extract_plant_names(mixed_plants)
    assert extracted == ["Hibiscus", "Marigold"]
    print("PASS: Mixed format plant name extraction works")
    
    # Test with empty/invalid data
    assert extract_plant_names([]) == []
    assert extract_plant_names(None) == []
    assert extract_plant_names([{}, "Valid Plant", {"invalid": "no_name"}]) == ["Valid Plant"]
    print("PASS: Invalid data handling works")


def test_normalize_user_data_for_community():
    """Test user data normalization for community matching"""
    print("Testing user data normalization...")
    
    # Test with mixed user data formats
    mixed_users = [
        {
            "name": "Maria",
            "plants": ["Rose", "Jasmine", "Hibiscus"]  # Legacy format
        },
        {
            "name": "John",
            "plants": [  # Enhanced format from Gemini
                {
                    "name": "Oak",
                    "superimposed_image": "base64_oak_data",
                    "placement_confidence": 0.88
                },
                {
                    "name": "Maple",
                    "superimposed_image": "base64_maple_data",
                    "placement_confidence": 0.91
                }
            ]
        },
        {
            "name": "Aisha",
            "plants": [  # Mixed format
                "Guava",
                {
                    "name": "Lemon",
                    "superimposed_image": "base64_lemon_data",
                    "placement_confidence": 0.85
                }
            ]
        }
    ]
    
    normalized = normalize_user_data_for_community(mixed_users)
    
    # Verify normalization
    assert len(normalized) == 3
    assert normalized[0]["name"] == "Maria"
    assert normalized[0]["plants"] == ["Rose", "Jasmine", "Hibiscus"]
    assert normalized[1]["name"] == "John"
    assert normalized[1]["plants"] == ["Oak", "Maple"]
    assert normalized[2]["name"] == "Aisha"
    assert normalized[2]["plants"] == ["Guava", "Lemon"]
    
    print("PASS: User data normalization works correctly")
    
    # Test with invalid user data
    invalid_users = [
        {"name": "Valid User", "plants": ["Plant1"]},
        {"invalid": "no_plants_field"},
        "not_a_dict",
        {"name": "Empty Plants", "plants": []}
    ]
    
    normalized = normalize_user_data_for_community(invalid_users)
    assert len(normalized) == 2  # Only valid users should remain
    assert normalized[0]["name"] == "Valid User"
    assert normalized[1]["name"] == "Empty Plants"
    
    print("PASS: Invalid user data filtering works")


def test_community_endpoint_with_legacy_data():
    """Test community endpoint with legacy plant data format"""
    print("Testing community endpoint with legacy data...")
    
    legacy_request = {
        "users": [
            {"name": "Maria", "plants": ["Rose", "Jasmine", "Hibiscus"]},
            {"name": "Olivia", "plants": ["Lavender", "Thyme", "Basil"]},
            {"name": "John", "plants": ["Oak", "Maple", "Pine"]}
        ]
    }
    
    # Mock the Perplexity API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"choices": [{"message": {"content": "{\\"match\\": [{\\"users\\": [\\"Maria\\", \\"Olivia\\"], \\"description\\": [\\"Both users prefer flowering plants\\"], \\"benefits\\": [{\\"type\\": \\"air_quality\\", \\"amount\\": \\"15%\\", \\"direction\\": true}]}]}"}}]}'
    mock_response.json.return_value = json.loads(mock_response.text)
    
    with app.test_client() as client:
        with patch('requests.post', return_value=mock_response):
            response = client.post('/community', json=legacy_request)
            assert response.status_code == 200
            data = response.get_json()
            assert 'match' in data
            print("PASS: Legacy data format works with community endpoint")


def test_community_endpoint_with_enhanced_data():
    """Test community endpoint with Gemini-enhanced plant data format"""
    print("Testing community endpoint with enhanced data...")
    
    enhanced_request = {
        "users": [
            {
                "name": "Maria",
                "plants": [
                    {
                        "name": "Rose",
                        "superimposed_image": "base64_rose_data",
                        "placement_confidence": 0.85
                    },
                    {
                        "name": "Jasmine",
                        "superimposed_image": "base64_jasmine_data",
                        "placement_confidence": 0.92
                    }
                ]
            },
            {
                "name": "John",
                "plants": [
                    {
                        "name": "Oak",
                        "superimposed_image": "base64_oak_data",
                        "placement_confidence": 0.88
                    }
                ]
            }
        ]
    }
    
    # Mock the Perplexity API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '{"choices": [{"message": {"content": "{\\"match\\": [{\\"users\\": [\\"Maria\\", \\"John\\"], \\"description\\": [\\"Both users have outdoor plants\\"], \\"benefits\\": [{\\"type\\": \\"carbon_absorption\\", \\"amount\\": \\"20%\\", \\"direction\\": true}]}]}"}}]}'
    mock_response.json.return_value = json.loads(mock_response.text)
    
    with app.test_client() as client:
        with patch('requests.post', return_value=mock_response):
            response = client.post('/community', json=enhanced_request)
            assert response.status_code == 200
            data = response.get_json()
            assert 'match' in data
            print("PASS: Enhanced data format works with community endpoint")


def test_community_endpoint_error_handling():
    """Test community endpoint error handling"""
    print("Testing community endpoint error handling...")
    
    with app.test_client() as client:
        # Test with no data
        response = client.post('/community', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        print("PASS: Missing users field handled correctly")
        
        # Test with invalid users data
        response = client.post('/community', json={"users": []})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        print("PASS: Empty users array handled correctly")
        
        # Test API failure
        with patch('requests.post', side_effect=Exception("API Error")):
            response = client.post('/community', json={
                "users": [{"name": "Test", "plants": ["Plant1"]}]
            })
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
            print("PASS: API failure handled correctly")


def main():
    """Run community compatibility tests"""
    print("Running Community Compatibility Tests")
    print("=" * 50)
    
    # Set up test environment
    os.environ['PPLX_API_KEY'] = 'test_key_for_community_testing'
    
    # Run tests
    test_extract_plant_names()
    test_normalize_user_data_for_community()
    test_community_endpoint_with_legacy_data()
    test_community_endpoint_with_enhanced_data()
    test_community_endpoint_error_handling()
    
    print("=" * 50)
    print("Community compatibility tests completed successfully!")


if __name__ == "__main__":
    main()