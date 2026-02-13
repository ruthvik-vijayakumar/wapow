# TikTok Clone

A modern TikTok clone built with Vue 3, Vite, Tailwind CSS, Pinia, and persistent storage.

## Features

- **Modern Tech Stack**: Vue 3 with Composition API, TypeScript, Vite
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **State Management**: Pinia for reactive state management
- **Persistent Storage**: LocalStorage for data persistence
- **Masonry Layout**: Pinterest-style grid layout for video tiles
- **Dark Theme**: TikTok-inspired dark theme with accent colors
- **Reusable Components**: Modular component architecture

## Pages & Components

### Home Page
- **Top Bar**: Logo, search, and menu icons
- **Category Navigation**: Horizontal scrollable categories
- **Video Grid**: Masonry layout with video tiles
- **Bottom Navigation**: Fixed navigation with icons

### Components
- `ContentTile.vue`: Individual content tile with thumbnail, title, author, and engagement metrics
- `TopBar.vue`: Header with logo and action buttons
- `CategoryNavigation.vue`: Horizontal category selector
- `BottomNavigation.vue`: Fixed bottom navigation bar

### Store
- `videos.ts`: Pinia store with video data management and localStorage persistence

## Tech Stack

- **Frontend**: Vue 3 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS 4
- **State Management**: Pinia
- **Router**: Vue Router 4
- **Icons**: Heroicons (SVG)

## Getting Started

### Prerequisites
- Node.js 20.19.0 or higher
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd tiktok-clone
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser and navigate to `http://localhost:5173`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run type-check` - Run TypeScript type checking
- `npm run lint` - Run ESLint with auto-fix
- `npm run format` - Format code with Prettier

## Project Structure

```
src/
├── assets/
│   └── main.css          # Global styles and Tailwind directives
├── components/
│   ├── ContentTile.vue     # Individual content tile component
│   ├── TopBar.vue        # Header component
│   ├── CategoryNavigation.vue # Category selector
│   └── BottomNavigation.vue   # Bottom navigation
├── stores/
│   └── videos.ts         # Pinia store for video data
├── views/
│   └── HomeView.vue      # Main home page
├── router/
│   └── index.ts          # Vue Router configuration
└── App.vue               # Root component
```

## Features Implemented

### Video Display
- Masonry grid layout with responsive design
- Video thumbnails with play button overlay
- Duration and view count badges
- Author information with avatars
- Engagement metrics (likes, comments, shares)

### Navigation
- Fixed bottom navigation with active states
- Horizontal category navigation
- Top bar with search and menu functionality

### Data Management
- Pinia store with reactive state
- LocalStorage persistence for video data
- Sample data generation for demonstration

### Styling
- Dark theme matching TikTok's design
- Responsive design for mobile devices
- Smooth transitions and hover effects
- Custom Tailwind configuration

## Future Enhancements

- Video player functionality
- User authentication
- Real-time data fetching
- Comments and likes system
- User profiles
- Video upload functionality
- Search and filtering
- Infinite scroll
- Push notifications

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is for educational purposes only.


<!-- Default Franklin font -->
<div class="font-sans">Default text</div>

<!-- Postoni fonts -->
<div class="font-postoni">Postoni Standard</div>
<div class="font-postoni-display">Postoni Display</div>
<div class="font-postoni-titling">Postoni Titling</div>

<!-- Font weights -->
<div class="font-light">Light text</div>
<div class="font-bold">Bold text</div>