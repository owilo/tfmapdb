import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './Layout';
import Gallery from './Gallery';
import MapDetail from './MapDetail';
import AuthorList from './AuthorList';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/gallery" replace />} />
          <Route path="gallery" element={<Gallery />} />
          <Route path="map/:code" element={<MapDetail />} />
          <Route path="authors" element={<AuthorList />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
