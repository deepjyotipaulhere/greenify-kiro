#!/usr/bin/env python3
"""
End-to-end test for community matching with Gemini-enhanced plant data.

Tests the complete flow:
1. Get plant recommendations from /answer endpoint (with Gemini data)
2. Use those recommendations in /community endpoint
3. Verify community matching works with enhanced plant data
"""

import json
import os
from unittest.mock import patch, Mock
from app import app


def create_mock_gemini_response():
    """Create a mock response that simulates Gemini API output with enhanced plant data"""
    return {
        "description": "This location appears to be a sunny garden area with well-draining soil, suitable for various flowering and ornamental plants.",
        "plants": [
            {
                "name": "Rose",
                "image": "https://example.com/rose.jpg",
                "superimposed_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77yQAAAABJRU5ErkJggg==",
                "placement_confidence": 0.85,
                "description": "Beautiful flowering shrub with fragrant blooms",
                "care_instructions": "Water regularly, prune after flowering",
                "care_tips": "Fertilize in spring, mulch around base",
                "AR_model": "https://example.com/rose_ar.glb"
            },
            {
                "name": "Jasmine",
                "image": "https://example.com/jasmine.jpg",
                "superimposed_image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77yQAAAABJRU5ErkJggg==",
                "placement_confidence": 0.92,
                "description": "Fragrant climbing vine with white flowers",
                "care_instructions": "Provide support structure, water moderately",
                "care_tips": "Prune lightly after flowering season",
                "AR_model": "https://example.com/jasmine_ar.glb"
            }
        ]
    }


def create_mock_community_response():
    """Create a mock community matching response"""
    return {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "match": [{
                        "users": ["User1", "User2"],
                        "description": ["Both users prefer flowering plants that attract pollinators"],
                        "benefits": [{
                            "type": "biodiversity",
                            "amount": "25%",
                            "direction": True
                        }]
                    }]
                })
            }
        }]
    }


def test_end_to_end_community_flow():
    """Test complete flow from plant recommendations to community matching"""
    print("Testing end-to-end community flow with Gemini data...")
    
    # Mock Gemini client
    mock_gemini_client = Mock()
    mock_gemini_client.analyze_image_and_recommend_plants.return_value = create_mock_gemini_response()
    
    # Mock community API response
    mock_community_response = Mock()
    mock_community_response.status_code = 200
    mock_community_response.text = json.dumps(create_mock_community_response())
    mock_community_response.json.return_value = create_mock_community_response()
    
    with app.test_client() as client:
        # Step 1: Get plant recommendations from /answer endpoint
        with patch('gemini_client.create_gemini_client', return_value=mock_gemini_client):
            answer_response = client.post('/answer', json={
                'image': 'base64_test_image_data',
                'location': [40.7128, -74.0060, 10]
            })
            
            assert answer_response.status_code == 200
            answer_data = answer_response.get_json()
            assert 'plants' in answer_data
            assert len(answer_data['plants']) == 2
            
            # Verify enhanced plant data structure
            plant1 = answer_data['plants'][0]
            assert 'name' in plant1
            assert 'superimposed_image' in plant1
            assert 'placement_confidence' in plant1
            assert plant1['name'] == 'Rose'
            assert plant1['placement_confidence'] == 0.85
            
            print("PASS: /answer endpoint returns enhanced plant data")
        
        # Step 2: Use plant recommendations in community matching
        community_request = {
            "users": [
                {
                    "name": "User1",
                    "plants": answer_data['plants']  # Use enhanced plant data from /answer
                },
                {
                    "name": "User2",
                    "plants": [
                        {
                            "name": "Lavender",
                            "superimposed_image": "base64_lavender_data",
                            "placement_confidence": 0.88
                        }
                    ]
                }
            ]
        }
        
        with patch('requests.post', return_value=mock_community_response):
            community_response = client.post('/community', json=community_request)
            
            assert community_response.status_code == 200
            community_data = community_response.get_json()
            assert 'match' in community_data
            assert len(community_data['match']) == 1
            
            match = community_data['match'][0]
            assert 'users' in match
            assert 'description' in match
            assert 'benefits' in match
            
            print("PASS: /community endpoint processes enhanced plant data correctly")
            print("PASS: End-to-end flow works with Gemini-enhanced data")


def test_mixed_data_community_matching():
    """Test community matching with mixed legacy and enhanced plant data"""
    print("Testing community matching with mixed data formats...")
    
    mixed_request = {
        "users": [
            {
                "name": "LegacyUser",
                "plants": ["Rose", "Jasmine", "Hibiscus"]  # Legacy format
            },
            {
                "name": "EnhancedUser",
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
                "name": "MixedUser",
                "plants": [  # Mixed format
                    "Pine",  # Legacy
                    {
                        "name": "Cedar",
                        "superimposed_image": "base64_cedar_data",
                        "placement_confidence": 0.79
                    }
                ]
            }
        ]
    }
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = json.dumps({
        "choices": [{
            "message": {
                "content": json.dumps({
                    "match": [{
                        "users": ["LegacyUser", "EnhancedUser", "MixedUser"],
                        "description": ["All users prefer outdoor plants suitable for landscaping"],
                        "benefits": [{
                            "type": "air_quality",
                            "amount": "30%",
                            "direction": True
                        }]
                    }]
                })
            }
        }]
    })
    mock_response.json.return_value = json.loads(mock_response.text)
    
    with app.test_client() as client:
        with patch('requests.post', return_value=mock_response):
            response = client.post('/community', json=mixed_request)
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'match' in data
            assert len(data['match']) == 1
            
            match = data['match'][0]
            assert len(match['users']) == 3
            assert 'LegacyUser' in match['users']
            assert 'EnhancedUser' in match['users']
            assert 'MixedUser' in match['users']
            
            print("PASS: Mixed data format community matching works correctly")


def main():
    """Run end-to-end community tests"""
    print("Running End-to-End Community Tests")
    print("=" * 50)
    
    # Set up test environment
    os.environ['GEMINI_API_KEY'] = 'test_key_for_e2e_testing'
    os.environ['PPLX_API_KEY'] = 'test_key_for_community_testing'
    
    # Run tests
    test_end_to_end_community_flow()
    test_mixed_data_community_matching()
    
    print("=" * 50)
    print("End-to-end community tests completed successfully!")
    print("Community matching is fully compatible with Gemini-enhanced plant data!")


if __name__ == "__main__":
    main()