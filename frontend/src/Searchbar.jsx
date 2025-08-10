import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { ChevronDown, Search } from 'lucide-react';
import './style/main.css';

export default function Searchbar({ placeholder = "" }) {
  const location = useLocation();

  const getInitialFromUrl = () => {
    try {
      const p = new URLSearchParams(location.search).get('s');
      return p ? p : '';
    } catch (err) {
      return '';
    }
  };

  const [search, setSearch] = useState(getInitialFromUrl);

  // Keep input in sync if user navigates or url changes externally
  useEffect(() => {
    const val = new URLSearchParams(location.search).get('s') || '';
    setSearch(val);
  }, [location.search]);

  const buildQs = (rawSearch) => {
    const trimmed = rawSearch.trim();
    const params = new URLSearchParams();
    if (trimmed) {
      params.set('s', trimmed);
    }
    // Preserve sort param
    const currentSort = new URLSearchParams(location.search).get('sort');
    if (currentSort) {
      params.set('sort', currentSort);
    }
    return params.toString();
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const qs = buildQs(search);
    window.location.href = `${location.pathname}${qs ? `?${qs}` : ''}`;
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full flex justify-center items-center p-3 bg-gray-700 rounded-md shadow-md"
    >
      <input
        value={search}
        onChange={e => setSearch(e.target.value)}
        type="search"
        placeholder={placeholder}
        className="flex-1 px-4 py-1 border bg-white border-gray-400 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        type="button"
        className="ml-2 px-2 py-1 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors flex items-center cursor-pointer"
      >
        <ChevronDown size="1.5em" className="mr-1" /><span className="relative -top-px mr-1">Options</span>
      </button>
      <button
        type="submit"
        className="ml-2 px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors flex items-center cursor-pointer"
      >
        <Search size="1.5em" />
      </button>
    </form>
  );
}
