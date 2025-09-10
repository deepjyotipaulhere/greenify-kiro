# Project Structure

## Root Directory Organization

```
greenify/
├── app/                    # Expo Router file-based routing
│   ├── (tabs)/            # Tab navigation screens
│   ├── _layout.tsx        # Root layout with theme providers
│   └── +not-found.tsx     # 404 error page
├── assets/                # Static assets
│   ├── fonts/             # Custom fonts (SpaceMono, Borel, Roboto)
│   └── images/            # App icons, splash screens, gallery images
├── components/            # Reusable UI components
│   ├── ui/                # Base UI components
│   └── *.tsx              # Themed components (ThemedText, ThemedView, etc.)
├── constants/             # App-wide constants
│   ├── Colors.ts          # Light/dark theme colors
│   └── custom-theme.json  # UI Kitten theme configuration
├── hooks/                 # Custom React hooks
├── service/               # Backend Flask API
│   ├── app.py             # Main Flask application
│   ├── models.py          # Pydantic data models
│   ├── requirements.txt   # Python dependencies
│   └── __pycache__/       # Python bytecode cache
└── scripts/               # Utility scripts
```

## Architecture Patterns

### Frontend Structure
- **File-based Routing**: Screens organized in `app/` directory following Expo Router conventions
- **Component Hierarchy**: Reusable components in `components/`, themed variants for consistency
- **Hook Pattern**: Custom hooks in `hooks/` for shared logic (color scheme, theme colors)
- **Constants Organization**: Centralized styling and configuration in `constants/`

### Backend Structure
- **API Endpoints**: RESTful endpoints in `app.py` (`/answer`, `/community`, `/users`)
- **Data Models**: Pydantic models in `models.py` for request/response validation
- **Environment Configuration**: `.env` file for sensitive API keys

## Naming Conventions

### Files & Directories
- **Components**: PascalCase (e.g., `ThemedText.tsx`, `ParallaxScrollView.tsx`)
- **Hooks**: camelCase with `use` prefix (e.g., `useColorScheme.ts`)
- **Constants**: PascalCase for files, UPPER_CASE for exports
- **Routes**: Expo Router conventions with parentheses for groups `(tabs)`

### Code Style
- **TypeScript**: Strict mode enabled with path aliases (`@/*`)
- **React Native**: Functional components with hooks
- **Styling**: StyleSheet.create() for component styles, themed colors via hooks
- **Props**: TypeScript interfaces with descriptive names

## Import Patterns
- **Absolute Imports**: Use `@/` alias for root-level imports
- **Relative Imports**: For same-directory or nearby files
- **Asset Imports**: Direct require() for fonts and images in Expo

## Configuration Files
- **app.json**: Expo configuration with plugins and permissions
- **tsconfig.json**: TypeScript configuration with strict mode
- **package.json**: Dependencies and npm scripts
- **eslint.config.js**: Linting rules following Expo standards