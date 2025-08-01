import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Gallery from './Gallery'
import MapDetail from './MapDetail'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/gallery" replace />} />
        <Route path="gallery/" element={<Gallery />} />
        <Route path="map/:code" element={<MapDetail />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)