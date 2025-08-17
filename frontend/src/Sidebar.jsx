import { Link } from 'react-router-dom';
import { Map, Users, Tag, Puzzle, List, History } from 'lucide-react'
import { useTranslation } from 'react-i18next';

export default function Sidebar() {
  const { t, i18n } = useTranslation();

  return (
    <aside className="w-48 h-screen bg-gray-800 text-white p-4">
      <nav className="space-y-2">
        <Link to="/gallery" className="flex items-center space-x-2 px-3 py-2 rounded hover:bg-gray-700">
          <Map size='1em' />
          <span className="relative -top-px">{t("navigation.gallery")}</span>
        </Link>
        <Link to="/authors" className="flex items-center space-x-2 px-3 py-2 rounded hover:bg-gray-700">
          <Users size='1em' />
          <span className="relative -top-px">{t("navigation.authors")}</span>
        </Link>
        <Link to="/categories" className="flex items-center space-x-2 px-3 py-2 rounded hover:bg-gray-700">
          <Tag size='1em' />
          <span className="relative -top-px">{t("navigation.categories")}</span>
        </Link>
        <Link to="/modules" className="flex items-center space-x-2 px-3 py-2 rounded hover:bg-gray-700">
          <Puzzle size='1em' />
          <span className="relative -top-px">{t("navigation.modules")}</span>
        </Link>
        <Link to="/leaderboards" className="flex items-center space-x-2 px-3 py-2 rounded hover:bg-gray-700">
          <List size='1em' />
          <span className="relative -top-px">{t("navigation.leaderboards")}</span>
        </Link>
        <Link to="/contests" className="flex items-center space-x-2 px-3 py-2 rounded hover:bg-gray-700">
          <History size='1em' />
          <span className="relative -top-px">{t("navigation.contest_history")}</span>
        </Link>
      </nav>
    </aside>
  );
}