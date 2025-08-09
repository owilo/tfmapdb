import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ChevronDown, Search } from 'lucide-react';
import './style/main.css';

const xmlPresencePattern = /<.*?>/;
const mapCodePattern = /^(?=.*\d)!?@?\d*(?:-\@?\d*)?$/;
const authorsPattern = /^!?\+?[A-Za-z]\w*(#\d{4})?$/;
const categoryPattern = /^!?(?:[Pp#]?\d+|[Pp#]?\d+-\d+|[Pp#]?\d+-|-[Pp#]?\d+)$/; // TODO Maybe can do similarly to mapCodePattern

function parseSearchParameters(search) {
  const items = search.trim().split(/\s+/);
  const codes = [];
  const authors = [];
  const categories = [];

  // Parse search terms and reduce URL length
  items.forEach(item => {
    if (mapCodePattern.test(item)) {
      codes.push(item.replace(/@/g, ''));
    }
    else if (categoryPattern.test(item)) { // Category before author to avoid indexing for PXX#0000
      categories.push(item.replace(/[Pp#]/g, ''));
    }
    else if (authorsPattern.test(item)) {
      if (item.endsWith('#0000')) {
        item = item.slice(0, -5);
      }
      authors.push(item);
    }
  });

  const params = new URLSearchParams();

  if (codes.length) {
    params.set('code', codes.join(','));
  }
  if (authors.length) {
    params.set('author', authors.join(','));
  }
  if (categories.length) {
    params.set('category', categories.join(','));
  }

  return params.toString();
}

export default function Searchbar() {
  const [search, setSearch] = useState('');
  //const navigate = useNavigate();
  const location = useLocation();

  const handleSubmit = (e) => {
    e.preventDefault();
    const qs = parseSearchParameters(search);

    /*navigate({
      pathname: location.pathname,
      search: qs,
    });*/
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
        type="text"
        placeholder="Search maps, authors, categories..."
        className="flex-1 px-4 py-1 border bg-white border-gray-400 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        type="button"
        className="ml-2 px-2 py-1 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors flex items-center cursor-pointer"
      >
        <ChevronDown size="1.5em" className="mr-1" /> Options
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