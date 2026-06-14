/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './Layout';
import { Dashboard } from './pages/Dashboard';
import { Documents } from './pages/Documents';
import { DocumentDetail } from './pages/DocumentDetail';
import { Providers } from './pages/Providers';
import { ComparisonDetail } from './pages/ComparisonDetail';

const basename = window.location.pathname.startsWith('/static') ? '/static' : '';

export default function App() {
  return (
    <BrowserRouter basename={basename || undefined}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="documents" element={<Documents />} />
          <Route path="documents/:id" element={<DocumentDetail />} />
          <Route path="providers" element={<Providers />} />
          <Route path="documents/:docId/compare" element={<ComparisonDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
