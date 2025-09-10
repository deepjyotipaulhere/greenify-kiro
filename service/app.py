import base64
import json
import os
import re
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from models import Answer1, Answer2, Community
from typing import Any, Dict

load_dotenv()

# Verify Gemini API key is configured
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    print("Warning: GEMINI_API_KEY not found in environment variables")
else:
    print("Gemini API key configured successfully")

# Gemini API configuration is handled by the gemini_client module
# Perplexity configuration for community endpoint (not migrated in this task)
perplexity_url = "https://api.perplexity.ai/chat/completions"
perplexity_headers = {
    "Authorization": f"Bearer {os.getenv('PPLX_API_KEY')}",
    "accept": "application/json",
    "content-type": "application/json",
}


app = Flask(__name__)
CORS(app)


@app.route("/answer", methods=["POST"])
def answer():
    """
    Updated /answer endpoint using single Gemini API call.
    
    Replaces both Perplexity API calls with one comprehensive Gemini 2.0 Flash call
    that provides location analysis and plant recommendations with superimposed images.
    
    Maintains existing response structure for frontend compatibility.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "description": "Invalid request data.",
                "plants": [],
                "error": "No data provided in request."
            }), 400

        print(f"Received request data: {data}")

        # Validate required fields
        if "image" not in data or "location" not in data:
            return jsonify({
                "description": "Missing required fields.",
                "plants": [],
                "error": "Image and location data are required."
            }), 400

        image = data["image"]
        location = data["location"]
        
        # Validate location format
        if not isinstance(location, list) or len(location) < 2:
            return jsonify({
                "description": "Invalid location format.",
                "plants": [],
                "error": "Location must be a list with at least latitude and longitude."
            }), 400

        lat, lng = location[0], location[1]
        alt = location[2] if len(location) > 2 else 0

        print(f"Processing image analysis for location: [{lat}, {lng}, {alt}]")

        # Import Gemini client
        from gemini_client import create_gemini_client, GeminiAPIError

        # Use single Gemini API call for comprehensive analysis and plant recommendations with superimposed images
        try:
            gemini_client = create_gemini_client()
        except GeminiAPIError as client_error:
            print(f"Failed to create Gemini client: {client_error}")
            return jsonify({
                "description": "Plant analysis service is currently unavailable. Please try again later.",
                "plants": [],
                "error": "Service initialization failed. Please try again later."
            }), 503
        
        # Single comprehensive call that replaces both Perplexity API calls
        try:
            comprehensive_response = gemini_client.analyze_image_and_recommend_plants(image, [lat, lng, alt])
            print(f"Gemini comprehensive analysis successful with {len(comprehensive_response.get('plants', []))} plant recommendations")
            return jsonify(comprehensive_response)
            
        except GeminiAPIError as gemini_error:
            print(f"Gemini API error: {gemini_error}")
            # Use the client's comprehensive error handler (Requirement 6.1, 6.2, 6.3, 6.4)
            error_response = gemini_client.handle_api_errors(gemini_error)
            
            # Determine appropriate HTTP status code based on error type
            if hasattr(gemini_error, 'error_type'):
                if gemini_error.error_type == 'auth':
                    status_code = 401
                elif gemini_error.error_type == 'quota':
                    status_code = 429
                elif gemini_error.error_type in ['network', 'api']:
                    status_code = 503
                elif gemini_error.error_type in ['validation', 'image']:
                    status_code = 400
                else:
                    status_code = 500
            else:
                status_code = 500
            
            return jsonify(error_response), status_code
        
    except Exception as e:
        print(f"Unexpected error in /answer endpoint: {e}")
        # Handle unexpected errors
        return jsonify({
            "description": "Unable to analyze location at this time. Please try again.",
            "plants": [],
            "error": "An unexpected error occurred. Please try again."
        }), 500


def extract_plant_names(plants_data):
    """
    Extract plant names from various plant data formats for community matching.
    
    Handles both:
    - Simple string arrays: ["Plant Name 1", "Plant Name 2"]
    - Enhanced Plant objects: [{"name": "Plant Name 1", "superimposed_image": "...", ...}, ...]
    
    Args:
        plants_data: List of plant names (strings) or Plant objects (dicts)
        
    Returns:
        List of plant names as strings
    """
    if not plants_data:
        return []
    
    plant_names = []
    for plant in plants_data:
        if isinstance(plant, str):
            # Simple plant name string
            plant_names.append(plant)
        elif isinstance(plant, dict) and "name" in plant:
            # Enhanced Plant object with name field
            plant_names.append(plant["name"])
        else:
            # Skip invalid plant data
            continue
    
    return plant_names


def normalize_user_data_for_community(users_data):
    """
    Normalize user data to ensure consistent plant name format for community matching.
    
    Converts enhanced Plant objects to simple plant names while preserving
    the original user structure expected by the community matching algorithm.
    
    Args:
        users_data: List of user objects with plants data
        
    Returns:
        List of user objects with normalized plant names
    """
    normalized_users = []
    
    for user in users_data:
        if not isinstance(user, dict) or "plants" not in user:
            # Skip invalid user data
            continue
            
        normalized_user = user.copy()
        normalized_user["plants"] = extract_plant_names(user["plants"])
        normalized_users.append(normalized_user)
    
    return normalized_users


@app.route("/community", methods=["POST"])
def community():
    """
    Community matching endpoint that handles both legacy and Gemini-enhanced plant data.
    
    Supports:
    - Legacy format: users with simple plant name arrays
    - Enhanced format: users with full Plant objects from Gemini API
    
    The algorithm normalizes all plant data to simple names for consistent matching.
    """
    try:
        data = request.get_json()
        if not data or "users" not in data:
            return jsonify({"error": "Invalid request data. 'users' field is required."}), 400
        
        # Normalize user data to handle both legacy and enhanced plant formats
        normalized_users = normalize_user_data_for_community(data["users"])
        
        if not normalized_users:
            return jsonify({"error": "No valid user data provided."}), 400
        
        print(f"Processing community matching for {len(normalized_users)} users")
        
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a community builder of people who want to plant trees to nearby places."
                    "They have been suggested some plants according to their place and weather. Your job is to analyze the plants of the corresponding users "
                    "and create a group of those users and return group of those users whose plants are of similar type and how they can collaborate with themselves",
                },
                {"role": "user", "content": json.dumps(normalized_users)},
            ],
            "stream": False,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"schema": Community.model_json_schema()},
            },
        }

        try:
            response = requests.post(perplexity_url, headers=perplexity_headers, json=payload)
            print(f"Community matching API response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"API request failed with status {response.status_code}: {response.text}")
                return jsonify({"error": "Community matching service temporarily unavailable."}), 503
            
            answer_text = response.text
            text_cleaned = re.sub(
                r"<think>.*?</think>\s*", "", answer_text, flags=re.DOTALL
            )
            json_match = re.search(r"{.*}", text_cleaned, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                try:
                    # Parse the JSON string
                    answer_data = json.loads(json_str)
                    print(f"Successfully processed community matching for {len(normalized_users)} users")
                    return jsonify(
                        json.loads(answer_data["choices"][0]["message"]["content"])
                    )

                except json.JSONDecodeError as e:
                    print(f"JSON decode error in community matching: {e}")
                    try:
                        # Fallback parsing
                        return jsonify(
                            json.loads(response.json()["choices"][0]["message"]["content"])
                        )
                    except (json.JSONDecodeError, KeyError) as fallback_error:
                        print(f"Fallback parsing also failed: {fallback_error}")
                        return jsonify({"error": "Failed to process community matching response."}), 500
            else:
                print("No valid JSON found in community matching response")
                return jsonify({"error": "Invalid response format from community matching service."}), 500

        except requests.exceptions.RequestException as e:
            print(f"Community matching API request failed: {e}")
            return jsonify({"error": "Failed to connect to community matching service."}), 503
        
    except Exception as e:
        print(f"Unexpected error in community matching: {e}")
        return jsonify({"error": "An unexpected error occurred during community matching."}), 500


@app.route("/users")
def users():
    """
    Get sample user data for community matching.
    
    Returns users with plant data in legacy format (simple names) for compatibility.
    The community endpoint can handle both legacy and enhanced formats from Gemini API.
    """
    # Sample users with legacy plant format for demonstration
    # In a real application, this would come from a database and could include
    # enhanced Plant objects with superimposed_image and placement_confidence
    users = [
        {
            "name": "Raj",
            "plants": [
                "Spider Plant",
                "Peace Lily",
                "Snake Plant",
                "Pothos",
                "Rubber Plant",
            ],
        },
        {"name": "Aisha", "plants": ["Guava", "Lemon", "Papaya"]},
        {"name": "John", "plants": ["Oak", "Maple", "Pine", "Cedar"]},
        {"name": "Maria", "plants": ["Rose", "Jasmine", "Hibiscus", "Marigold"]},
        {"name": "Liam", "plants": ["Apple", "Cherry", "Peach"]},
        {"name": "Sophia", "plants": ["Coconut", "Banana", "Areca Palm"]},
        {"name": "Ethan", "plants": ["Teak", "Mahogany", "Sandalwood"]},
        {"name": "Olivia", "plants": ["Lavender", "Thyme", "Basil", "Mint"]},
        {"name": "Noah", "plants": ["Bamboo", "Fern", "Aloe Vera", "Cactus"]},
    ]
    return jsonify(users)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
