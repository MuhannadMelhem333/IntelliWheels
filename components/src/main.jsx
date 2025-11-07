/**
 * Main Entry Point for CarGlobe Demo
 * Run with: npm run dev
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import CarGlobeDemo from './CarGlobeDemo';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <CarGlobeDemo />
    </React.StrictMode>
);

