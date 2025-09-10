"""
Gemini API client module for plant recommendation and image analysis.

This module provides authentication and communication with Google's Gemini 2.0 Flash API
for analyzing images and generating plant recommendations with superimposed images.
"""

import os
import logging
from typing import Dict, List, Optional, Any
import google.generativeai as genai
import base64
from io import BytesIO
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiAPIError(Exception):
    """Custom exception for Gemini API related errors."""
    
    def __init__(self, message: str, error_type: str = "general", original_error: Exception = None):
        """
        Initialize GeminiAPIError with detailed error information.
        
        Args:
            message: Human-readable error message
            error_type: Type of error (auth, quota, network, malformed, etc.)
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.error_type = error_type
        self.original_error = original_error


class GeminiClient:
    """
    Client for interacting with Google's Gemini 2.0 Flash API.
    
    Handles authentication, image analysis, and plant recommendation generation
    with superimposed image capabilities.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini client with API authentication.
        
        Args:
            api_key: Optional API key. If not provided, will use GEMINI_API_KEY env var.
        
        Raises:
            GeminiAPIError: If API key is not provided or invalid.
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise GeminiAPIError("GEMINI_API_KEY environment variable is required")
        
        self.model_name = "gemini-2.5-flash-image-preview"
        self.model = None
        self._authenticate()
    
    def _authenticate(self) -> None:
        """
        Authenticate with the Gemini API using the provided API key.
        
        Raises:
            GeminiAPIError: If authentication fails.
        """
        try:
            # Configure the genai client with API key
            genai.configure(api_key=self.api_key)
            
            # Initialize the model
            self.model = genai.GenerativeModel(self.model_name)
            
            logger.info("Successfully authenticated with Gemini API")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Gemini API: {str(e)}")
            raise GeminiAPIError(f"Authentication failed: {str(e)}")
    
    def validate_connection(self) -> bool:
        """
        Validate the connection to Gemini API.
        
        Returns:
            bool: True if connection is valid, False otherwise.
        """
        try:
            if not self.model:
                return False
            
            # Test connection with a simple request
            models = genai.list_models()
            logger.info("Gemini API connection validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Connection validation failed: {str(e)}")
            return False
    
    def handle_api_errors(self, error: Exception) -> Dict[str, Any]:
        """
        Handle Gemini API errors and provide appropriate fallback responses.
        
        This method implements comprehensive error handling as specified in Requirement 6:
        - API call failures (6.1)
        - Malformed responses (6.2) 
        - Network issues (6.3)
        - API quota exceeded (6.4)
        
        Args:
            error: The exception that occurred during API interaction
            
        Returns:
            Dict: Fallback response with user-friendly error messages
        """
        try:
            error_message = str(error)
            error_lower = error_message.lower()
            
            # Handle authentication errors (Requirement 6.1)
            if any(auth_term in error_lower for auth_term in ['auth', 'credential', 'api key', 'permission']):
                logger.error(f"Authentication error: {error_message}")
                return {
                    "description": "Unable to authenticate with plant analysis service. Please try again later.",
                    "plants": [],
                    "error": "Authentication failed. Please contact support if this persists."
                }
            
            # Handle quota/rate limiting errors (Requirement 6.4)
            if any(quota_term in error_lower for quota_term in ['quota', 'rate limit', 'too many requests', 'limit exceeded']):
                logger.error(f"API quota exceeded: {error_message}")
                return {
                    "description": "Plant analysis service is currently experiencing high demand. Please try again in a few minutes.",
                    "plants": self._get_fallback_plants(),
                    "error": "Service temporarily unavailable due to high demand. Please try again shortly."
                }
            
            # Handle network/connectivity errors (Requirement 6.3)
            if any(network_term in error_lower for network_term in ['network', 'connection', 'timeout', 'unreachable', 'dns']):
                logger.error(f"Network error: {error_message}")
                return {
                    "description": "Unable to connect to plant analysis service. Please check your internet connection and try again.",
                    "plants": self._get_fallback_plants(),
                    "error": "Network connection issue. Please check your internet connection and try again."
                }
            
            # Handle malformed response errors (Requirement 6.2)
            if any(format_term in error_lower for format_term in ['json', 'parse', 'format', 'decode', 'malformed']):
                logger.error(f"Response format error: {error_message}")
                return {
                    "description": "Plant analysis completed, but response formatting failed. Basic recommendations provided.",
                    "plants": self._get_fallback_plants(),
                    "error": "Response processing issue. Basic plant suggestions provided."
                }
            
            # Handle image processing errors
            if any(image_term in error_lower for image_term in ['image', 'invalid format', 'decode', 'corrupt']):
                logger.error(f"Image processing error: {error_message}")
                return {
                    "description": "Unable to process the uploaded image. Please try with a different image.",
                    "plants": [],
                    "error": "Image processing failed. Please try uploading a different image."
                }
            
            # Handle model/API unavailability
            if any(unavail_term in error_lower for unavail_term in ['unavailable', 'not found', '404', '503', 'service']):
                logger.error(f"Service unavailable: {error_message}")
                return {
                    "description": "Plant analysis service is temporarily unavailable. Basic recommendations provided.",
                    "plants": self._get_fallback_plants(),
                    "error": "Analysis service temporarily unavailable. Please try again later."
                }
            
            # Generic error fallback (Requirement 6.1)
            logger.error(f"Unhandled API error: {error_message}")
            return {
                "description": "Plant analysis encountered an issue, but basic recommendations are available.",
                "plants": self._get_fallback_plants(),
                "error": "Analysis service encountered an issue. Basic plant suggestions provided."
            }
            
        except Exception as fallback_error:
            # Last resort fallback if error handling itself fails
            logger.error(f"Error handling failed: {str(fallback_error)}")
            return {
                "description": "Unable to analyze location at this time. Please try again.",
                "plants": [],
                "error": "Service temporarily unavailable. Please try again later."
            }
    
    def _get_fallback_plants(self) -> List[Dict[str, Any]]:
        """
        Provide fallback plant recommendations when API fails.
        
        This ensures users still get basic plant suggestions even when 
        superimposed image generation fails (Requirement 2.4).
        
        Returns:
            List: Basic plant recommendations without superimposed images
        """
        return [
            {
                "name": "Spider Plant",
                "image": "",
                "superimposed_image": "",
                "description": "Hardy indoor plant that adapts well to various lighting conditions and is easy to care for.",
                "care_instructions": "Water when soil feels dry, prefers bright indirect light, well-draining soil.",
                "care_tips": "Remove brown tips, propagate plantlets for new plants, rotate occasionally for even growth.",
                "AR_model": "",
                "placement_confidence": 0.7
            },
            {
                "name": "Pothos",
                "image": "",
                "superimposed_image": "",
                "description": "Versatile trailing plant that thrives in low to medium light and is very forgiving.",
                "care_instructions": "Water when top inch of soil is dry, tolerates low light, standard potting mix.",
                "care_tips": "Trim to encourage bushier growth, can grow in water or soil, wipe leaves occasionally.",
                "AR_model": "",
                "placement_confidence": 0.8
            },
            {
                "name": "Snake Plant",
                "image": "",
                "superimposed_image": "",
                "description": "Low-maintenance succulent that tolerates neglect and various lighting conditions.",
                "care_instructions": "Water sparingly, allow soil to dry completely between waterings, tolerates low light.",
                "care_tips": "Avoid overwatering, clean leaves with damp cloth, divide to propagate new plants.",
                "AR_model": "",
                "placement_confidence": 0.6
            }
        ]
    
    def _prepare_image_for_api(self, image_data: str) -> bytes:
        """
        Prepare base64 image data for API consumption.
        
        Args:
            image_data: Base64 encoded image string.
            
        Returns:
            bytes: Processed image data.
            
        Raises:
            GeminiAPIError: If image processing fails.
        """
        try:
            # Validate input
            if not image_data or not isinstance(image_data, str):
                raise GeminiAPIError("Invalid image data provided", "image")
            
            # Remove data URL prefix if present
            if image_data.startswith('data:image'):
                try:
                    image_data = image_data.split(',')[1]
                except IndexError:
                    raise GeminiAPIError("Malformed data URL format", "image")
            
            # Decode base64 image
            try:
                image_bytes = base64.b64decode(image_data)
            except Exception as decode_error:
                raise GeminiAPIError(f"Invalid base64 encoding: {str(decode_error)}", "image", decode_error)
            
            # Validate image format and size
            try:
                img = Image.open(BytesIO(image_bytes))
                img.verify()
                
                # Check image size (prevent extremely large images)
                if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
                    raise GeminiAPIError("Image file too large (max 10MB)", "image")
                    
            except Exception as img_error:
                if "too large" in str(img_error):
                    raise  # Re-raise size error as-is
                raise GeminiAPIError(f"Invalid or corrupted image format: {str(img_error)}", "image", img_error)
            
            return image_bytes
            
        except GeminiAPIError:
            # Re-raise GeminiAPIError as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error in image preparation: {str(e)}")
            raise GeminiAPIError(f"Failed to prepare image: {str(e)}", "image", e)
    
    def analyze_location_and_plants(
        self, 
        image_data: str, 
        location: List[float]
    ) -> Dict[str, Any]:
        """
        Analyze location suitability for plant growth using Gemini 2.0 Flash.
        
        This function replaces the first Perplexity API call in the /answer endpoint.
        It focuses on analyzing the image and location to determine suitability for plant growth.
        
        Args:
            image_data: Base64 encoded image string.
            location: List containing [latitude, longitude, altitude].
            
        Returns:
            Dict containing location analysis description.
            
        Raises:
            GeminiAPIError: If API call fails or returns invalid data.
        """
        try:
            if not self.model:
                raise GeminiAPIError("Model not authenticated")
            
            # Prepare image data
            processed_image = self._prepare_image_for_api(image_data)
            
            # Extract location coordinates
            latitude, longitude = location[0], location[1]
            altitude = location[2] if len(location) > 2 else 0
            
            # Construct the prompt for location analysis only
            prompt = self._build_location_analysis_prompt(latitude, longitude, altitude)
            
            # Create PIL Image object for the API
            image = Image.open(BytesIO(processed_image))
            
            # Generate content with image and prompt
            response = self.model.generate_content([prompt, image])
            
            # Process and validate response for location analysis
            return self._process_location_analysis_response(response)
            
        except Exception as e:
            logger.error(f"Location analysis failed: {str(e)}")
            raise GeminiAPIError(f"Location analysis failed: {str(e)}")

    def analyze_image_and_recommend_plants(
        self, 
        image_data: str, 
        location: List[float]
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis: location suitability + plant recommendations with superimposed images.
        
        This single method replaces both Perplexity API calls in the /answer endpoint.
        It provides location analysis and plant recommendations with superimposed images in one call.
        
        Implements comprehensive error handling as per Requirement 6.
        
        Args:
            image_data: Base64 encoded image string.
            location: List containing [latitude, longitude, altitude].
            
        Returns:
            Dict containing location analysis and plant recommendations with superimposed images.
            
        Raises:
            GeminiAPIError: If API call fails or returns invalid data.
        """
        try:
            # Validate authentication first
            if not self.model:
                raise GeminiAPIError("Model not authenticated", "auth")
            
            # Validate input parameters
            if not image_data or not location:
                raise GeminiAPIError("Missing required image or location data", "validation")
            
            if not isinstance(location, list) or len(location) < 2:
                raise GeminiAPIError("Invalid location format", "validation")
            
            # Prepare image data with error handling
            try:
                processed_image = self._prepare_image_for_api(image_data)
            except Exception as img_error:
                raise GeminiAPIError(f"Image processing failed: {str(img_error)}", "image", img_error)
            
            # Extract location coordinates
            latitude, longitude = location[0], location[1]
            altitude = location[2] if len(location) > 2 else 0
            
            # Construct the comprehensive prompt for both analysis and recommendations
            prompt = self._build_comprehensive_analysis_prompt(latitude, longitude, altitude)
            
            # Create PIL Image object for the API
            try:
                image = Image.open(BytesIO(processed_image))
            except Exception as pil_error:
                raise GeminiAPIError(f"Invalid image format: {str(pil_error)}", "image", pil_error)
            
            # Generate content with image and prompt - main API call
            try:
                response = self.model.generate_content([prompt, image])
            except Exception as api_error:
                # Categorize API errors for better handling
                error_msg = str(api_error).lower()
                if 'quota' in error_msg or 'rate limit' in error_msg:
                    raise GeminiAPIError(f"API quota exceeded: {str(api_error)}", "quota", api_error)
                elif 'network' in error_msg or 'connection' in error_msg:
                    raise GeminiAPIError(f"Network error: {str(api_error)}", "network", api_error)
                elif 'auth' in error_msg or 'permission' in error_msg:
                    raise GeminiAPIError(f"Authentication error: {str(api_error)}", "auth", api_error)
                else:
                    raise GeminiAPIError(f"API call failed: {str(api_error)}", "api", api_error)
            
            # Process and validate comprehensive response
            try:
                return self._process_comprehensive_response(response)
            except Exception as process_error:
                raise GeminiAPIError(f"Response processing failed: {str(process_error)}", "malformed", process_error)
            
        except GeminiAPIError:
            # Re-raise GeminiAPIError as-is
            raise
        except Exception as e:
            # Catch any unexpected errors
            logger.error(f"Unexpected error in comprehensive plant analysis: {str(e)}")
            raise GeminiAPIError(f"Unexpected analysis error: {str(e)}", "general", e)
    
    def _build_location_analysis_prompt(self, latitude: float, longitude: float, altitude: float) -> str:
        """
        Build the prompt for location analysis only (replaces first Perplexity call).
        
        Args:
            latitude: Location latitude.
            longitude: Location longitude.
            altitude: Location altitude.
            
        Returns:
            str: Formatted prompt for location analysis.
        """
        return f"""
        Analyze this image taken at coordinates [{latitude}, {longitude}, {altitude}] and provide a short description of the place with respect to suitability of plant growth.

        Focus on:
        - Environmental conditions (lighting, space, shelter)
        - Soil quality and drainage (if visible)
        - Climate considerations based on location
        - Overall suitability for plant cultivation
        - Any potential challenges or advantages for growing plants

        Return the response in this exact JSON format:
        {{
            "description": "Short description of the place's suitability for plant growth"
        }}
        """

    def _build_comprehensive_analysis_prompt(self, latitude: float, longitude: float, altitude: float) -> str:
        """
        Build the comprehensive prompt for Gemini 2.0 Flash analysis (replaces both Perplexity calls).
        
        Args:
            latitude: Location latitude.
            longitude: Location longitude.
            altitude: Location altitude.
            
        Returns:
            str: Formatted comprehensive prompt for the API.
        """
        return f"""
        You are a plant growth expert. Analyze this image taken at coordinates [{latitude}, {longitude}, {altitude}] and provide comprehensive analysis with visual enhancements.

        TASK 1 - Location Analysis:
        - Analyze the environment's suitability for plant growth
        - Describe lighting conditions, space availability, and environmental factors
        - Assess soil conditions and drainage if visible
        - Consider climate based on coordinates
        - Provide a short description of the place's suitability for plant growth

        TASK 2 - Plant Recommendations with Visual Superimposition:
        - Suggest up to 5 plants suitable for this specific environment and climate zone
        - For each plant, generate a superimposed image showing how it would look when placed in this location
        - Ensure realistic proportions, positioning, and lighting in superimposed images
        - Each plant should have unique placement to avoid overlap
        - Maintain natural appearance and environmental harmony

        For each recommended plant, provide:
        - Name of the plant
        - Reference image URL (use placeholder if needed)
        - Superimposed image (base64 encoded) showing the plant placed in the original photo
        - Description (2-3 sentences about the plant and why it suits this location)
        - Care instructions (watering, sunlight, soil requirements)
        - Care tips (seasonal advice, common issues, maintenance)
        - AR model URL (use placeholder)
        - Placement confidence score (0.0-1.0 based on how well the plant fits the environment)

        CRITICAL REQUIREMENTS:
        1. The superimposed_image field must contain a base64-encoded image showing the plant realistically placed in the user's original photograph
        2. Each plant must have a unique placement position within the image
        3. Consider realistic scale, lighting, and environmental integration
        4. Maintain frontend compatibility with existing response structure

        Return the response in this exact JSON format:
        {{
            "description": "Short description of the place's suitability for plant growth",
            "plants": [
                {{
                    "name": "Plant Name",
                    "image": "https://example.com/plant-reference.jpg",
                    "superimposed_image": "base64_encoded_superimposed_image_showing_plant_in_original_photo",
                    "description": "Detailed description of the plant and why it suits this location",
                    "care_instructions": "Specific care instructions including watering, sunlight, and soil requirements",
                    "care_tips": "Seasonal advice and common care tips for optimal growth",
                    "AR_model": "https://example.com/ar-model.glb",
                    "placement_confidence": 0.85
                }}
            ]
        }}
        """

    def _build_analysis_prompt(self, latitude: float, longitude: float, altitude: float) -> str:
        """
        Build the structured prompt for Gemini 2.0 Flash analysis.
        
        Args:
            latitude: Location latitude.
            longitude: Location longitude.
            altitude: Location altitude.
            
        Returns:
            str: Formatted prompt for the API.
        """
        return f"""
        Analyze this image taken at coordinates [{latitude}, {longitude}, {altitude}] and provide:

        1. Location Analysis:
           - Describe the environment's suitability for plant growth
           - Identify lighting conditions, space availability, and environmental factors
           - Assess soil conditions if visible

        2. Plant Recommendations:
           - Suggest up to 5 suitable plants for this specific environment
           - For each plant, provide:
             * Name
             * Description (2-3 sentences)
             * Care instructions (watering, sunlight, soil requirements)
             * Care tips (seasonal advice, common issues)
             * Placement confidence score (0.0-1.0)

        3. Visual Enhancement:
           - For each recommended plant, generate a superimposed image showing how it would look when placed in this location
           - Ensure realistic proportions, positioning, and lighting
           - Maintain natural appearance and environmental harmony

        Return the response in this exact JSON format:
        {{
            "description": "Location analysis description",
            "plants": [
                {{
                    "name": "Plant Name",
                    "image": "https://example.com/plant-reference.jpg",
                    "superimposed_image": "base64_encoded_superimposed_image",
                    "description": "Plant description",
                    "care_instructions": "Care instructions",
                    "care_tips": "Care tips",
                    "AR_model": "https://example.com/ar-model.glb",
                    "placement_confidence": 0.85
                }}
            ]
        }}
        """
    
    def _process_location_analysis_response(self, response) -> Dict[str, Any]:
        """
        Process and validate the location analysis API response.
        
        Args:
            response: Raw API response from Gemini for location analysis.
            
        Returns:
            Dict: Processed location analysis data.
            
        Raises:
            GeminiAPIError: If response processing fails.
        """
        try:
            # Extract text content from response
            if not response.candidates or not response.candidates[0].content.parts:
                raise GeminiAPIError("Empty response from Gemini API")
            
            response_text = response.candidates[0].content.parts[0].text
            
            # Parse JSON response
            import json
            try:
                parsed_response = json.loads(response_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, create a fallback response
                logger.warning("Failed to parse JSON response for location analysis, creating fallback")
                return {"description": "Location analysis completed, but detailed parsing failed. The area appears suitable for plant growth."}
            
            # Validate response structure
            if not isinstance(parsed_response, dict):
                raise GeminiAPIError("Invalid response format")
            
            if 'description' not in parsed_response:
                raise GeminiAPIError("Missing description field in location analysis response")
            
            logger.info("Successfully processed location analysis response")
            return parsed_response
            
        except Exception as e:
            logger.error(f"Location analysis response processing failed: {str(e)}")
            raise GeminiAPIError(f"Failed to process location analysis response: {str(e)}")

    def _process_comprehensive_response(self, response) -> Dict[str, Any]:
        """
        Process and validate the comprehensive API response (location + plants + superimposed images).
        
        Implements graceful handling of malformed responses as per Requirement 6.2.
        
        Args:
            response: Raw API response from Gemini for comprehensive analysis.
            
        Returns:
            Dict: Processed and validated comprehensive response data.
            
        Raises:
            GeminiAPIError: If response processing fails completely.
        """
        try:
            # Validate response structure
            if not response:
                logger.warning("Received null response from Gemini API")
                return self._create_comprehensive_fallback_response("No response received")
            
            if not hasattr(response, 'candidates') or not response.candidates:
                logger.warning("Response missing candidates field")
                return self._create_comprehensive_fallback_response("Invalid response structure")
            
            if not response.candidates[0].content or not response.candidates[0].content.parts:
                logger.warning("Response missing content parts")
                return self._create_comprehensive_fallback_response("Empty response content")
            
            # Extract text content from response
            try:
                response_text = response.candidates[0].content.parts[0].text
                if not response_text or not response_text.strip():
                    logger.warning("Empty response text from Gemini API")
                    return self._create_comprehensive_fallback_response("Empty response text")
            except (AttributeError, IndexError) as extract_error:
                logger.warning(f"Failed to extract response text: {str(extract_error)}")
                return self._create_comprehensive_fallback_response("Failed to extract response")
            
            # Parse JSON response with comprehensive error handling
            import json
            try:
                parsed_response = json.loads(response_text)
            except json.JSONDecodeError as json_error:
                # If JSON parsing fails, create a comprehensive fallback response (Requirement 6.2)
                logger.warning(f"Failed to parse JSON response: {str(json_error)}")
                logger.info("Creating fallback response due to malformed JSON")
                return self._create_comprehensive_fallback_response(response_text)
            except Exception as parse_error:
                logger.warning(f"Unexpected parsing error: {str(parse_error)}")
                return self._create_comprehensive_fallback_response(response_text)
            
            # Validate response structure
            if not isinstance(parsed_response, dict):
                logger.warning("Response is not a valid dictionary")
                return self._create_comprehensive_fallback_response("Invalid response format")
            
            # Check for required fields with fallback handling
            if 'description' not in parsed_response:
                logger.warning("Missing description field, adding default")
                parsed_response['description'] = "Location analysis completed with limited details available."
            
            if 'plants' not in parsed_response:
                logger.warning("Missing plants field, adding fallback plants")
                parsed_response['plants'] = self._get_fallback_plants()
            
            # Validate and clean plants data
            plants = parsed_response.get('plants', [])
            if not isinstance(plants, list):
                logger.warning("Plants field is not a list, using fallback")
                parsed_response['plants'] = self._get_fallback_plants()
            else:
                # Validate each plant and fix issues where possible
                validated_plants = []
                for i, plant in enumerate(plants):
                    try:
                        self._validate_comprehensive_plant_data(plant)
                        validated_plants.append(plant)
                    except Exception as plant_error:
                        logger.warning(f"Plant {i} validation failed: {str(plant_error)}, skipping")
                        continue
                
                # If no plants passed validation, use fallback
                if not validated_plants:
                    logger.warning("No plants passed validation, using fallback plants")
                    parsed_response['plants'] = self._get_fallback_plants()
                else:
                    parsed_response['plants'] = validated_plants
            
            final_plant_count = len(parsed_response.get('plants', []))
            logger.info(f"Successfully processed comprehensive response with {final_plant_count} plant recommendations")
            return parsed_response
            
        except Exception as e:
            logger.error(f"Critical error in comprehensive response processing: {str(e)}")
            # Last resort fallback
            return self._create_comprehensive_fallback_response(f"Processing error: {str(e)}")

    def _process_api_response(self, response) -> Dict[str, Any]:
        """
        Process and validate the API response.
        
        Args:
            response: Raw API response from Gemini.
            
        Returns:
            Dict: Processed and validated response data.
            
        Raises:
            GeminiAPIError: If response processing fails.
        """
        try:
            # Extract text content from response
            if not response.candidates or not response.candidates[0].content.parts:
                raise GeminiAPIError("Empty response from Gemini API")
            
            response_text = response.candidates[0].content.parts[0].text
            
            # Parse JSON response
            import json
            try:
                parsed_response = json.loads(response_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, create a fallback response
                logger.warning("Failed to parse JSON response, creating fallback")
                return self._create_fallback_response(response_text)
            
            # Validate response structure
            if not isinstance(parsed_response, dict):
                raise GeminiAPIError("Invalid response format")
            
            if 'description' not in parsed_response or 'plants' not in parsed_response:
                raise GeminiAPIError("Missing required fields in response")
            
            # Validate plants data
            plants = parsed_response.get('plants', [])
            if not isinstance(plants, list):
                raise GeminiAPIError("Plants field must be a list")
            
            # Ensure each plant has required fields
            for plant in plants:
                self._validate_plant_data(plant)
            
            logger.info(f"Successfully processed response with {len(plants)} plant recommendations")
            return parsed_response
            
        except Exception as e:
            logger.error(f"Response processing failed: {str(e)}")
            raise GeminiAPIError(f"Failed to process response: {str(e)}")
    
    def _validate_comprehensive_plant_data(self, plant: Dict[str, Any]) -> None:
        """
        Validate individual plant data structure for comprehensive response with superimposed images.
        
        Implements graceful validation with fallbacks as per Requirement 6.2.
        
        Args:
            plant: Plant data dictionary.
            
        Raises:
            GeminiAPIError: If plant data is critically invalid and cannot be fixed.
        """
        if not isinstance(plant, dict):
            raise GeminiAPIError("Plant data must be a dictionary")
        
        # Required fields with fallback values
        required_fields = {
            'name': 'Unknown Plant',
            'description': 'Plant information not available.',
            'care_instructions': 'Follow general plant care guidelines.',
            'care_tips': 'Monitor plant health and adjust care as needed.'
        }
        
        # Validate and fix required fields
        for field, default_value in required_fields.items():
            if field not in plant or not plant[field] or not isinstance(plant[field], str):
                logger.warning(f"Missing or invalid '{field}' for plant, using default")
                plant[field] = default_value
        
        # Set default values for optional fields
        plant.setdefault('image', '')
        plant.setdefault('AR_model', '')
        
        # Validate superimposed image field (important for this comprehensive response)
        # Per Requirement 2.4: system should still return plants without superimposed images if generation fails
        if 'superimposed_image' not in plant or not isinstance(plant['superimposed_image'], str):
            logger.warning(f"Missing or invalid superimposed_image for plant {plant.get('name', 'unknown')}")
            plant['superimposed_image'] = ''
        
        # Ensure placement_confidence is within valid range
        if 'placement_confidence' not in plant:
            plant['placement_confidence'] = 0.5  # Default confidence
        else:
            confidence = plant['placement_confidence']
            try:
                confidence = float(confidence)
                if confidence < 0.0 or confidence > 1.0:
                    raise ValueError("Confidence out of range")
                plant['placement_confidence'] = confidence
            except (ValueError, TypeError):
                logger.warning(f"Invalid placement_confidence {confidence} for plant {plant.get('name', 'unknown')}, setting to 0.5")
                plant['placement_confidence'] = 0.5
        
        # Validate string fields are not empty after cleaning
        for field in ['name', 'description', 'care_instructions', 'care_tips']:
            if not plant[field].strip():
                plant[field] = required_fields[field]

    def _validate_plant_data(self, plant: Dict[str, Any]) -> None:
        """
        Validate individual plant data structure.
        
        Args:
            plant: Plant data dictionary.
            
        Raises:
            GeminiAPIError: If plant data is invalid.
        """
        required_fields = ['name', 'description', 'care_instructions', 'care_tips']
        
        for field in required_fields:
            if field not in plant:
                raise GeminiAPIError(f"Missing required field '{field}' in plant data")
        
        # Set default values for optional fields
        plant.setdefault('image', '')
        plant.setdefault('superimposed_image', '')
        plant.setdefault('AR_model', '')
        plant.setdefault('placement_confidence', 0.0)
    
    def _create_comprehensive_fallback_response(self, response_text: str) -> Dict[str, Any]:
        """
        Create a comprehensive fallback response when JSON parsing fails.
        
        Implements fallback logic as per Requirement 2.4: system should still return 
        plant suggestions without superimposed images when generation fails.
        
        Args:
            response_text: Raw response text from API.
            
        Returns:
            Dict: Comprehensive fallback response structure with location and plants.
        """
        # Try to extract any useful information from the raw response text
        description = "Location analysis completed, but detailed parsing failed. The area appears suitable for plant growth based on available information."
        
        # Attempt to extract some meaningful content if possible
        if response_text and len(response_text.strip()) > 0:
            # Look for any plant names or useful information in the raw text
            response_lower = response_text.lower()
            if any(plant_word in response_lower for plant_word in ['plant', 'grow', 'suitable', 'recommend']):
                description = "Location analysis completed with some details available. Basic plant recommendations provided."
        
        return {
            "description": description,
            "plants": self._get_fallback_plants()
        }

    def _create_fallback_response(self, response_text: str) -> Dict[str, Any]:
        """
        Create a fallback response when JSON parsing fails.
        
        Args:
            response_text: Raw response text from API.
            
        Returns:
            Dict: Fallback response structure.
        """
        return {
            "description": "Analysis completed, but detailed parsing failed. Please try again.",
            "plants": [
                {
                    "name": "General Plant Recommendation",
                    "image": "",
                    "superimposed_image": "",
                    "description": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                    "care_instructions": "Please consult gardening resources for specific care instructions.",
                    "care_tips": "Monitor plant health and adjust care based on environmental conditions.",
                    "AR_model": "",
                    "placement_confidence": 0.5
                }
            ]
        }
    
    def get_plant_recommendations_with_images(
        self, 
        image_data: str, 
        location: List[float], 
        location_description: str
    ) -> Dict[str, Any]:
        """
        Generate plant recommendations with superimposed images using Gemini 2.0 Flash.
        
        This function replaces the second Perplexity API call in the /answer endpoint.
        It takes the location analysis and generates plant recommendations with superimposed images.
        
        Args:
            image_data: Base64 encoded image string.
            location: List containing [latitude, longitude, altitude].
            location_description: Description of the location from previous analysis.
            
        Returns:
            Dict containing plant recommendations with superimposed images.
            
        Raises:
            GeminiAPIError: If API call fails or returns invalid data.
        """
        try:
            if not self.model:
                raise GeminiAPIError("Model not authenticated")
            
            # Prepare image data
            processed_image = self._prepare_image_for_api(image_data)
            
            # Extract location coordinates
            latitude, longitude = location[0], location[1]
            altitude = location[2] if len(location) > 2 else 0
            
            # Construct the prompt for plant recommendations with superimposition
            prompt = self._build_plant_recommendation_prompt(
                latitude, longitude, altitude, location_description
            )
            
            # Create PIL Image object for the API
            image = Image.open(BytesIO(processed_image))
            
            # Generate content with image and prompt
            response = self.model.generate_content([prompt, image])
            
            # Process and validate response for plant recommendations
            return self._process_plant_recommendation_response(response)
            
        except Exception as e:
            logger.error(f"Plant recommendation with superimposition failed: {str(e)}")
            raise GeminiAPIError(f"Plant recommendation failed: {str(e)}")

    def _build_plant_recommendation_prompt(
        self, 
        latitude: float, 
        longitude: float, 
        altitude: float, 
        location_description: str
    ) -> str:
        """
        Build the prompt for plant recommendations with superimposed images.
        
        Args:
            latitude: Location latitude.
            longitude: Location longitude.
            altitude: Location altitude.
            location_description: Previous analysis of the location.
            
        Returns:
            str: Formatted prompt for plant recommendations.
        """
        return f"""
        You are a plant growth expert. Based on the image and location analysis, suggest suitable plants with visual superimposition.

        Location Details:
        - Coordinates: [{latitude}, {longitude}, {altitude}]
        - Location Analysis: {location_description}

        Your task:
        1. Suggest at most 5 plants that can be grown in this specific location
        2. For each plant, generate a superimposed image showing how it would look when placed in the original photo
        3. Ensure realistic proportions, positioning, and lighting in superimposed images
        4. Each plant should have its own unique placement and superimposed image
        5. Maintain realistic environmental harmony and natural appearance

        Requirements for superimposed images:
        - Show realistic plant placement within the existing environment
        - Maintain proper scale and proportions relative to surroundings
        - Consider lighting conditions and shadows from the original image
        - Position plants in suitable locations within the frame
        - Each plant should have a unique placement to avoid overlap

        Return the response in this exact JSON format:
        {{
            "plants": [
                {{
                    "name": "Plant Name",
                    "image": "https://example.com/plant-reference.jpg",
                    "superimposed_image": "base64_encoded_superimposed_image_showing_plant_in_original_photo",
                    "description": "Detailed description of the plant and why it suits this location",
                    "care_instructions": "Specific care instructions including watering, sunlight, and soil requirements",
                    "care_tips": "Seasonal advice and common care tips for optimal growth",
                    "AR_model": "https://example.com/ar-model.glb",
                    "placement_confidence": 0.85
                }}
            ]
        }}

        Important: The superimposed_image field must contain a base64-encoded image that shows the recommended plant realistically placed within the user's original photograph. Each plant should have a unique placement position.
        """

    def _process_plant_recommendation_response(self, response) -> Dict[str, Any]:
        """
        Process and validate the plant recommendation API response.
        
        Args:
            response: Raw API response from Gemini for plant recommendations.
            
        Returns:
            Dict: Processed plant recommendation data.
            
        Raises:
            GeminiAPIError: If response processing fails.
        """
        try:
            # Extract text content from response
            if not response.candidates or not response.candidates[0].content.parts:
                raise GeminiAPIError("Empty response from Gemini API")
            
            response_text = response.candidates[0].content.parts[0].text
            
            # Parse JSON response
            import json
            try:
                parsed_response = json.loads(response_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, create a fallback response
                logger.warning("Failed to parse JSON response for plant recommendations, creating fallback")
                return self._create_plant_recommendation_fallback()
            
            # Validate response structure
            if not isinstance(parsed_response, dict):
                raise GeminiAPIError("Invalid response format")
            
            if 'plants' not in parsed_response:
                raise GeminiAPIError("Missing plants field in response")
            
            # Validate plants data
            plants = parsed_response.get('plants', [])
            if not isinstance(plants, list):
                raise GeminiAPIError("Plants field must be a list")
            
            # Ensure each plant has required fields and validate superimposed images
            for plant in plants:
                self._validate_plant_recommendation_data(plant)
            
            logger.info(f"Successfully processed plant recommendations with {len(plants)} plants with superimposed images")
            return parsed_response
            
        except Exception as e:
            logger.error(f"Plant recommendation response processing failed: {str(e)}")
            raise GeminiAPIError(f"Failed to process plant recommendation response: {str(e)}")

    def _validate_plant_recommendation_data(self, plant: Dict[str, Any]) -> None:
        """
        Validate individual plant recommendation data structure with superimposed images.
        
        Args:
            plant: Plant data dictionary.
            
        Raises:
            GeminiAPIError: If plant data is invalid.
        """
        required_fields = ['name', 'description', 'care_instructions', 'care_tips']
        
        for field in required_fields:
            if field not in plant:
                raise GeminiAPIError(f"Missing required field '{field}' in plant data")
        
        # Set default values for optional fields
        plant.setdefault('image', '')
        plant.setdefault('AR_model', '')
        plant.setdefault('placement_confidence', 0.0)
        
        # Validate superimposed image field (required for this task)
        if 'superimposed_image' not in plant:
            logger.warning(f"Missing superimposed_image for plant {plant.get('name', 'unknown')}")
            plant['superimposed_image'] = ''
        
        # Ensure placement_confidence is within valid range
        if 'placement_confidence' in plant:
            confidence = plant['placement_confidence']
            if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
                logger.warning(f"Invalid placement_confidence {confidence} for plant {plant.get('name', 'unknown')}, setting to 0.5")
                plant['placement_confidence'] = 0.5

    def _create_plant_recommendation_fallback(self) -> Dict[str, Any]:
        """
        Create a fallback response for plant recommendations when JSON parsing fails.
        
        Returns:
            Dict: Fallback response structure for plant recommendations.
        """
        return {
            "plants": [
                {
                    "name": "General Plant Recommendation",
                    "image": "",
                    "superimposed_image": "",
                    "description": "Unable to generate specific plant recommendations at this time. Please consult local gardening resources.",
                    "care_instructions": "Follow general plant care guidelines for your climate zone.",
                    "care_tips": "Monitor plant health and adjust care based on environmental conditions.",
                    "AR_model": "",
                    "placement_confidence": 0.5
                }
            ]
        }




# Convenience function for easy import and usage
def create_gemini_client(api_key: Optional[str] = None) -> GeminiClient:
    """
    Create and return a configured Gemini client instance.
    
    Args:
        api_key: Optional API key. If not provided, uses environment variable.
        
    Returns:
        GeminiClient: Configured client instance.
    """
    return GeminiClient(api_key=api_key)