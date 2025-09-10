# Technology Stack

## Frontend Framework
- **Expo SDK 53**: Cross-platform React Native development framework
- **React Native 0.79.2**: Core mobile framework with React 19.0.0
- **TypeScript 5.8.3**: Strict typing with path aliases (`@/*` for root imports)
- **Expo Router 5.0**: File-based routing with typed routes enabled

## UI Framework & Design
- **UI Kitten**: Primary component library with Eva Design System
- **Custom Theme**: Green-focused color palette defined in `constants/custom-theme.json`
- **Fonts**: SpaceMono (primary), Borel (headers), Roboto Condensed (body text)
- **Icons**: Expo Vector Icons with custom assets

## Key Libraries
- **Maps**: Mapbox (`@rnmapbox/maps`) and Expo Maps for location services
- **Camera**: Expo Camera with image picker integration
- **Navigation**: React Navigation with bottom tabs
- **Storage**: SQLite (expo-sqlite) and AsyncStorage
- **Animations**: React Native Reanimated 3.17

## Backend Service
- **Flask**: Python web framework for API endpoints
- **Pydantic**: Data validation and serialization models
- **Perplexity AI**: sonar-pro and sonar-deep-research models via REST API
- **CORS**: Enabled for cross-origin requests

## Development Tools
- **ESLint**: Expo configuration with custom rules
- **Metro**: Bundler for web builds
- **EAS**: Expo Application Services for builds and deployment

## Common Commands

### Frontend Development
```bash
# Install dependencies
npm install

# Start development server
npx expo start

# Platform-specific builds
npx expo run:android
npx expo run:ios
npx expo start --web

# Linting
npx expo lint

# Reset project (removes example code)
npm run reset-project
```

### Backend Service
```bash
# Navigate to service directory
cd service

# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
# Create .env file with PPLX_API_KEY=your_api_key

# Run Flask development server
python app.py
```

## Environment Setup
- Requires PPLX_API_KEY environment variable for Perplexity AI integration
- Mapbox token configured in app.json for map functionality
- Location and camera permissions configured for mobile platforms