# Design Document

## Overview

This design outlines the migration from Perplexity API to Google's Gemini 2.0 Flash model for plant recommendation functionality. The key enhancement is adding image superimposition capabilities where Gemini generates visual representations of suggested plants placed within the user's original photo. The design maintains backward compatibility while extending the current data models to support superimposed images.

## Architecture

### Current Architecture
- Flask backend with `/answer` endpoint receiving image and location data
- Two-step process: image analysis followed by plant recommendation
- Pydantic models for structured responses
- Community matching based on plant suggestions

### New Architecture with Gemini 2.0 Flash
- Replace Perplexity API calls with Gemini 2.0 Flash API
- Single API call for both image analysis and plant recommendations with superimposition
- Enhanced Pydantic models to include superimposed image data
- Maintain existing endpoint structure for frontend compatibility

### API Flow Comparison

**Current Flow:**
1. User uploads image + location → Flask `/answer` endpoint
2. Flask → Perplexity API (sonar-pro) for image analysis
3. Flask → Perplexity API (sonar-deep-research) for plant recommendations
4. Return combined response to frontend

**New Flow:**
1. User uploads image + location → Flask `/answer` endpoint
2. Flask → Gemini 2.0 Flash API for comprehensive analysis and recommendations
3. Gemini generates plant suggestions with superimposed images
4. Return enhanced response with superimposed images to frontend

## Components and Interfaces

### 1. Gemini API Client
**Purpose:** Handle authentication and communication with Gemini 2.0 Flash API

**Libraries:**
```python
from google import genai
from google.genai import types
```

**Key Methods:**
- `authenticate()`: Validate API credentials using genai.configure()
- `analyze_image_and_recommend_plants()`: Main analysis method using genai client
- `handle_api_errors()`: Error handling and retry logic

**Configuration:**
- Model: `gemini-2.0-flash-exp`
- Authentication: API key via environment variable `GEMINI_API_KEY`
- Client initialization: `genai.configure(api_key=api_key)`
- Reference: Follow patterns from https://ai.google.dev/gemini-api/docs

### 2. Enhanced Data Models
**Updated Plant Model:**
```python
class Plant(BaseModel):
    name: str
    image: str = Field(description="Original plant reference image URL")
    superimposed_image: str = Field(description="Base64 encoded superimposed image")
    description: str = Field(description="Description of the plant")
    care_instructions: str = Field(description="Care instructions for the plant")
    care_tips: str = Field(description="Care tips for the plant")
    AR_model: str = Field(description="AR model URL for the plant")
    placement_confidence: float = Field(description="Confidence score for image placement")
```

**Response Models remain compatible:**
- `Answer1`: Location analysis (now from Gemini)
- `Answer2`: Plant recommendations with enhanced data

### 3. Image Processing Pipeline
**Superimposition Workflow:**
1. Gemini receives original image and location context
2. Analyzes suitable planting locations within the image
3. Generates plant suggestions based on environmental factors
4. Creates superimposed images showing plants in realistic positions
5. Returns base64-encoded superimposed images with metadata

### 4. Prompt Engineering
**Structured Prompt for Gemini 2.0 Flash:**
```
Analyze this image taken at coordinates [lat, lng, alt] and:
1. Describe the location's suitability for plant growth
2. Suggest up to 5 suitable plants for this environment
3. For each plant, generate a superimposed image showing how it would look when planted in this location
4. Ensure realistic placement, scale, and lighting in superimposed images
5. Return structured JSON with plant details and base64-encoded superimposed images
```

## Data Models

### Request Structure
```python
{
    "image": "base64_encoded_image_string",
    "location": [latitude, longitude, altitude]
}
```

### Enhanced Response Structure
```python
{
    "description": "Location analysis description",
    "plants": [
        {
            "name": "Plant Name",
            "image": "reference_image_url",
            "superimposed_image": "base64_encoded_superimposed_image",
            "description": "Plant description",
            "care_instructions": "Care instructions",
            "care_tips": "Care tips",
            "AR_model": "ar_model_url",
            "placement_confidence": 0.85
        }
    ]
}
```

### Environment Configuration
```python
# .env file additions
GEMINI_API_KEY=your_gemini_api_key_here
# Remove PPLX_API_KEY (deprecated)
```

## Error Handling

### API Error Scenarios
1. **Invalid API Key**: Return 401 with clear message
2. **Rate Limiting**: Implement exponential backoff
3. **Image Processing Failure**: Return plant suggestions without superimposed images
4. **Malformed Response**: Parse available data and log errors
5. **Network Timeout**: Retry with shorter timeout, fallback gracefully

### Fallback Strategy
- If superimposition fails: Return standard plant recommendations
- If Gemini API is unavailable: Return appropriate error message
- Maintain response structure for frontend compatibility

## Testing Strategy

### Unit Testing Focus Areas
1. **API Client**: Mock Gemini API responses
2. **Data Models**: Validate enhanced Pydantic schemas
3. **Error Handling**: Test various failure scenarios
4. **Response Formatting**: Ensure backward compatibility

### Integration Testing
1. **End-to-End Flow**: Image upload to superimposed response
2. **Community Matching**: Verify compatibility with new plant data
3. **Frontend Integration**: Ensure existing UI components work

### Manual Testing
1. **Image Quality**: Verify superimposed images look realistic
2. **Plant Accuracy**: Validate plant suggestions for different environments
3. **Performance**: Monitor response times compared to Perplexity

## Migration Strategy

### Phase 1: API Client Setup
- Install Google GenAI SDK: `pip install google-genai`
- Configure Gemini API authentication using `genai.configure()`
- Create basic API client with error handling using `google.genai` and `google.genai.types`
- Follow implementation patterns from https://ai.google.dev/gemini-api/docs

### Phase 2: Model Enhancement
- Update Pydantic models for superimposed images
- Modify response formatting logic
- Ensure backward compatibility

### Phase 3: Endpoint Migration
- Replace Perplexity calls with Gemini calls
- Update prompt engineering for optimal results
- Test superimposition quality

### Phase 4: Community Feature Compatibility
- Verify community matching works with new data
- Update any plant categorization logic if needed
- Test group formation algorithms

## Performance Considerations

### Response Time Optimization
- Single API call instead of two separate calls
- Efficient base64 encoding for images
- Appropriate image compression for superimposed results

### Resource Management
- Monitor API quota usage
- Implement request caching where appropriate
- Optimize image processing pipeline

### Scalability
- Design for horizontal scaling
- Consider async processing for heavy image operations
- Plan for increased payload sizes with superimposed images