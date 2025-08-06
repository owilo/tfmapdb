import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
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
      className="w-full flex justify-center items-center p-4 bg-neutral-100 rounded-lg shadow-md"
    >
      <input
        value={search}
        onChange={e => setSearch(e.target.value)}
        type="text"
        placeholder="Search maps, authors, categories..."
        className="w-full px-4 py-2 border border-neutral-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        type="submit"
        className="ml-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
      >
        Search
      </button>
    </form>
  );
}