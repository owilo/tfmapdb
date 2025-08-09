import { Link } from 'react-router-dom';
import { Map, Users, Tag, List, History } from 'lucide-react'

export default function Sidebar() {
  return (
    <aside className="w-48 h-screen bg-gray-800 text-white p-4">
      <nav className="space-y-2">
        <Link to="/gallery" className="flex items-center space-x-2 px-3 py-2 rounded hover:bg-gray-700">
          <Map size='1em' />
          <span>Gallery</span>
        </Link>
        <Link to="/authors" className="flex items-center space-x-2 px-3 py-2 rounded hover:bg-gray-700">
          <Users size='1em' />
          <span>Authors</span>
        </Link>
        <Link to="/categories" className="flex items-center space-x-2 px-3 py-2 rounded hover:bg-gray-700">
          <Tag size='1em' />
          <span>Categories</span>
        </Link>
        <Link to="/leaderboards" className="flex items-center space-x-2 px-3 py-2 rounded hover:bg-gray-700">
          <List size='1em' />
          <span>Leaderboards</span>
        </Link>
        <Link to="/contests" className="flex items-center space-x-2 px-3 py-2 rounded hover:bg-gray-700">
          <History size='1em' />
          <span>Contest history</span>
        </Link>
      </nav>
    </aside>
  );
}