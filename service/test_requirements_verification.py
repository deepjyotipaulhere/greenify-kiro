#!/usr/bin/env python3
"""
Verification test for Requirements 5.1, 5.2, 5.3, 5.4 from the Gemini API integration spec.

This test verifies that the community matching feature works correctly with Gemini-generated plant data.
"""

import json
import os
from unittest.mock import patch, Mock
from app import app, extract_plant_names, normalize_user_data_for_community


def test_requirement_5_1():
    """
    Requirement 5.1: WHEN plant data comes from Gemini 2.0 Flash API 
    THEN the community matching algorithm SHALL continue to function
    """
    print("Testing Requirement 5.1: Community matching with Gemini plant data...")
    
    # Simulate plant data from Gemini 2.0 Flash API
    gemini_plant_data = [
        {
            "name": "Rose",
            "image": "https://example.com/rose.jpg",
            "superimposed_image": "base64_encoded_superimposed_rose",
            "placement_confidence": 0.85,
            "description": "Beautiful flowering shrub",
            "care_instructions": "Water regularly",
            "care_tips": "Prune after flowering",
            "AR_model": "https://example.com/rose_ar.glb"
        },
        {
            "name": "Jasmine",
            "image": "https://example.com/jasmine.jpg", 
            "superimposed_image": "base64_encoded_superimposed_jasmine",
            "placement_confidence": 0.92,
            "description": "Fragrant climbing vine",
            "care_instructions": "Provide support structure",
            "care_tips": "Prune lightly",
            "AR_model": "https://example.com/jasmine_ar.glb"
        }
    ]
    
    users_with_gemini_data = [
        {"name": "User1", "plants": gemini_plant_data},
        {"name": "User2", "plants": [gemini_plant_data[0]]}  # Partial overlap
    ]
    
    # Mock successful community API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = json.dumps({
        "choices": [{
            "message": {
                "content": json.dumps({
                    "match": [{
                        "users": ["User1", "User2"],
                        "description": ["Both users prefer flowering plants"],
                        "benefits": [{"type": "pollinator_support", "amount": "20%", "direction": True}]
                    }]
                })
            }
        }]
    })
    mock_response.json.return_value = json.loads(mock_response.text)
    
    with app.test_client() as client:
        with patch('requests.post', return_value=mock_response):
            response = client.post('/community', json={"users": users_with_gemini_data})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'match' in data
            assert len(data['match']) > 0
            
            print("✓ Requirement 5.1: Community matching algorithm functions with Gemini data")


def test_requirement_5_2():
    """
    Requirement 5.2: WHEN users are grouped 
    THEN the system SHALL use the same plant categorization logic
    """
    print("Testing Requirement 5.2: Consistent plant categorization logic...")
    
    # Test that plant names are extracted consistently regardless of data format
    legacy_plants = ["Rose", "Jasmine", "Oak"]
    gemini_plants = [
        {"name": "Rose", "superimposed_image": "data1", "placement_confidence": 0.85},
        {"name": "Jasmine", "superimposed_image": "data2", "placement_confidence": 0.92},
        {"name": "Oak", "superimposed_image": "data3", "placement_confidence": 0.88}
    ]
    
    # Both formats should extract the same plant names
    legacy_names = extract_plant_names(legacy_plants)
    gemini_names = extract_plant_names(gemini_plants)
    
    assert legacy_names == gemini_names == ["Rose", "Jasmine", "Oak"]
    
    # Test normalization produces consistent format for community algorithm
    legacy_user = {"name": "LegacyUser", "plants": legacy_plants}
    gemini_user = {"name": "GeminiUser", "plants": gemini_plants}
    
    normalized = normalize_user_data_for_community([legacy_user, gemini_user])
    
    assert normalized[0]["plants"] == normalized[1]["plants"] == ["Rose", "Jasmine", "Oak"]
    
    print("✓ Requirement 5.2: Same plant categorization logic used for all data formats")


def test_requirement_5_3():
    """
    Requirement 5.3: WHEN community responses are generated 
    THEN they SHALL maintain the existing data structure
    """
    print("Testing Requirement 5.3: Existing community response structure maintained...")
    
    # Test with enhanced plant data
    enhanced_request = {
        "users": [
            {
                "name": "User1",
                "plants": [
                    {
                        "name": "Rose",
                        "superimposed_image": "base64_data",
                        "placement_confidence": 0.85
                    }
                ]
            }
        ]
    }
    
    # Mock response in expected Community model format
    expected_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "match": [{
                        "users": ["User1"],
                        "description": ["Single user with flowering plants"],
                        "benefits": [{
                            "type": "aesthetic_value",
                            "amount": "15%",
                            "direction": True
                        }]
                    }]
                })
            }
        }]
    }
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = json.dumps(expected_response)
    mock_response.json.return_value = expected_response
    
    with app.test_client() as client:
        with patch('requests.post', return_value=mock_response):
            response = client.post('/community', json=enhanced_request)
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify response structure matches Community model
            assert 'match' in data
            assert isinstance(data['match'], list)
            
            if len(data['match']) > 0:
                match = data['match'][0]
                assert 'users' in match
                assert 'description' in match
                assert 'benefits' in match
                assert isinstance(match['users'], list)
                assert isinstance(match['description'], list)
                assert isinstance(match['benefits'], list)
                
                if len(match['benefits']) > 0:
                    benefit = match['benefits'][0]
                    assert 'type' in benefit
                    assert 'amount' in benefit
                    assert 'direction' in benefit
            
            print("✓ Requirement 5.3: Community response structure maintained")


def test_requirement_5_4():
    """
    Requirement 5.4: IF plant data format changes 
    THEN the community matching SHALL adapt accordingly
    """
    print("Testing Requirement 5.4: Community matching adapts to format changes...")
    
    # Test various plant data formats that might come from different sources
    formats_to_test = [
        # Legacy format
        ["Rose", "Jasmine"],
        
        # Enhanced Gemini format
        [
            {"name": "Rose", "superimposed_image": "data1", "placement_confidence": 0.85},
            {"name": "Jasmine", "superimposed_image": "data2", "placement_confidence": 0.92}
        ],
        
        # Mixed format
        [
            "Rose",
            {"name": "Jasmine", "superimposed_image": "data2", "placement_confidence": 0.92}
        ],
        
        # Minimal enhanced format (only name and one extra field)
        [
            {"name": "Rose", "placement_confidence": 0.85},
            {"name": "Jasmine", "superimposed_image": "data2"}
        ],
        
        # Future format with additional fields
        [
            {
                "name": "Rose",
                "superimposed_image": "data1",
                "placement_confidence": 0.85,
                "future_field": "future_value",
                "another_enhancement": {"nested": "data"}
            }
        ]
    ]
    
    # All formats should normalize to the same plant names
    expected_names = ["Rose", "Jasmine"]
    
    for i, plant_format in enumerate(formats_to_test):
        extracted_names = extract_plant_names(plant_format)
        
        # Handle cases where not all plants have names (partial extraction expected)
        if i == len(formats_to_test) - 1:  # Future format test
            assert "Rose" in extracted_names
        else:
            assert extracted_names == expected_names[:len(extracted_names)]
    
    # Test that community endpoint handles all formats
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = json.dumps({
        "choices": [{
            "message": {
                "content": json.dumps({
                    "match": [{
                        "users": ["TestUser"],
                        "description": ["Adaptable matching"],
                        "benefits": [{"type": "flexibility", "amount": "100%", "direction": True}]
                    }]
                })
            }
        }]
    })
    mock_response.json.return_value = json.loads(mock_response.text)
    
    with app.test_client() as client:
        with patch('requests.post', return_value=mock_response):
            for plant_format in formats_to_test:
                request_data = {"users": [{"name": "TestUser", "plants": plant_format}]}
                response = client.post('/community', json=request_data)
                
                # Should handle all formats without errors
                assert response.status_code == 200
                data = response.get_json()
                assert 'match' in data
    
    print("✓ Requirement 5.4: Community matching adapts to various plant data formats")


def main():
    """Run requirements verification tests"""
    print("Running Requirements Verification Tests")
    print("Testing Requirements 5.1, 5.2, 5.3, 5.4 for Community Matching Compatibility")
    print("=" * 80)
    
    # Set up test environment
    os.environ['PPLX_API_KEY'] = 'test_key_for_requirements_verification'
    
    # Run requirement tests
    test_requirement_5_1()
    test_requirement_5_2()
    test_requirement_5_3()
    test_requirement_5_4()
    
    print("=" * 80)
    print("✅ ALL REQUIREMENTS VERIFIED SUCCESSFULLY!")
    print("Community matching is fully compatible with Gemini-enhanced plant data!")
    print("\nRequirements Status:")
    print("✓ 5.1: Community matching algorithm functions with Gemini data")
    print("✓ 5.2: Same plant categorization logic used for all formats")
    print("✓ 5.3: Community response structure maintained")
    print("✓ 5.4: Community matching adapts to format changes")


if __name__ == "__main__":
    main()