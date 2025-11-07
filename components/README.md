# CarGlobe React Component

A 3D interactive globe component for displaying car listings around the world using React Three Fiber and Three.js.

## Features

- 🌍 **3D Rotating Globe** - Beautiful 3D globe with smooth rotation
- 📍 **Interactive Markers** - Car markers plotted by latitude/longitude
- 🖱️ **Drag & Zoom** - Manual rotation by dragging, zoom with mouse wheel
- 💬 **Hover Tooltips** - Show car name and price on hover
- 📱 **Click Popups** - Detailed car information with image and "View Listing" button
- ⚡ **Performance Optimized** - Handles up to 500 markers smoothly
- 📱 **Responsive Design** - Works on desktop browsers

## Installation

### 1. Install Dependencies

```bash
npm install react react-dom @react-three/fiber @react-three/drei three
```

Or with yarn:

```bash
yarn add react react-dom @react-three/fiber @react-three/drei three
```

### 2. Install React Build Tools

You'll need a React build setup. Options:

**Option A: Create React App (Recommended for beginners)**
```bash
npx create-react-app intelliwheels-globe
cd intelliwheels-globe
npm install @react-three/fiber @react-three/drei three
```

**Option B: Vite (Faster, recommended)**
```bash
npm create vite@latest intelliwheels-globe -- --template react
cd intelliwheels-globe
npm install
npm install @react-three/fiber @react-three/drei three
```

**Option C: Integrate into existing project**
If you want to add React to your existing vanilla JS project, you can use:
```bash
npm install react react-dom @react-three/fiber @react-three/drei three
npm install --save-dev @vitejs/plugin-react vite
```

## Usage

### Basic Example

```jsx
import CarGlobe from './components/CarGlobe';

function App() {
    const cars = [
        {
            id: 1,
            name: 'BMW 3 Series',
            price: 45000,
            currency: 'USD',
            image: 'https://example.com/car.jpg',
            latitude: 40.7128,  // New York
            longitude: -74.0060,
        },
        // ... more cars
    ];
    
    return (
        <div style={{ width: '100%', height: '600px' }}>
            <CarGlobe cars={cars} />
        </div>
    );
}
```

### With Callback

```jsx
function App() {
    const handleCarClick = (car) => {
        console.log('Car clicked:', car);
        // Do something with the car data
    };
    
    return (
        <CarGlobe 
            cars={cars} 
            onCarClick={handleCarClick}
        />
    );
}
```

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `cars` | `Array<Car>` | Yes | Array of car objects |
| `onCarClick` | `Function` | No | Callback when a car marker is clicked |

### Car Object Structure

```typescript
interface Car {
    id: number | string;           // Unique identifier
    name: string;                  // Car name (e.g., "BMW 3 Series")
    price: number;                 // Price in specified currency
    currency?: string;              // Currency code (default: "USD")
    image?: string;                 // Image URL
    latitude: number;              // Latitude (-90 to 90)
    longitude: number;             // Longitude (-180 to 180)
}
```

## Integration with Existing Project

### Option 1: Standalone React App

Create a separate React app for the globe feature and embed it via iframe or link to it.

### Option 2: Add React to Existing Project

1. **Install dependencies:**
```bash
npm init -y
npm install react react-dom @react-three/fiber @react-three/drei three
npm install --save-dev @vitejs/plugin-react vite
```

2. **Create `vite.config.js`:**
```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    server: {
        port: 3000,
    },
});
```

3. **Create `index.html` in root:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>IntelliWheels Globe</title>
</head>
<body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
</body>
</html>
```

4. **Create `src/main.jsx`:**
```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import CarGlobeDemo from './components/CarGlobeDemo';

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <CarGlobeDemo />
    </React.StrictMode>
);
```

5. **Run development server:**
```bash
npm run dev
```

## Performance Optimization

The component is optimized for performance:

- **Memoization**: Markers are memoized to prevent unnecessary re-renders
- **Instanced Rendering**: For 500+ markers, consider using `InstancedMesh` from Three.js
- **LOD (Level of Detail)**: Markers fade out at distance (can be added)
- **Frustum Culling**: Only visible markers are rendered

## Customization

### Change Globe Appearance

Edit the `Globe` component in `CarGlobe.jsx`:

```jsx
<meshStandardMaterial
    color="#your-color"
    metalness={0.1}
    roughness={0.7}
    emissive="#your-emissive-color"
    emissiveIntensity={0.2}
/>
```

### Change Marker Colors

Edit the `CarMarker` component:

```jsx
<meshStandardMaterial
    color={hovered ? "#your-hover-color" : "#your-default-color"}
    emissive={hovered ? "#your-hover-color" : "#your-default-color"}
/>
```

### Adjust Rotation Speed

Change the rotation speed in the `Globe` component:

```jsx
meshRef.current.rotation.y += delta * 0.1; // Adjust 0.1 to change speed
```

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support (may need WebGL enabled)
- Mobile browsers: ⚠️ Limited (desktop optimized)

## Troubleshooting

### Globe not rendering
- Check browser console for WebGL errors
- Ensure WebGL is enabled in browser settings
- Try updating graphics drivers

### Markers not appearing
- Verify latitude/longitude values are valid (-90 to 90 for lat, -180 to 180 for lon)
- Check that `cars` array is not empty
- Verify React Three Fiber is properly installed

### Performance issues
- Reduce number of markers (use pagination or filtering)
- Enable `frustumCulled` on markers
- Use `InstancedMesh` for large datasets

## License

MIT License - Feel free to use in your projects!

