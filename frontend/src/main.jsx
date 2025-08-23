import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './Layout';
import Gallery from './Gallery';
import MapDetail from './MapDetail';
import AuthorList from './AuthorList';
import AuthorProfile from './AuthorProfile';
import CategoriesList from './CategoriesList';
import TagDetail from './TagDetail';
import Leaderboards from './Leaderboards';
import "./i18n";

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/gallery" replace />} />
          <Route path="gallery" element={<Gallery />} />
          <Route path="map/:code" element={<MapDetail />} />
          <Route path="authors" element={<AuthorList />} />
          <Route path="author/:name" element={<AuthorProfile />} />
          <Route path="categories" element={<CategoriesList />} />
          <Route path="category/:id" element={<TagDetail type="category" />} />
          <Route path="tag/:id" element={<TagDetail type="tag" />} />
          <Route path="leaderboards" element={<Leaderboards />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
