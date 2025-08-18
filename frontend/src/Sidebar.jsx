import { Link } from 'react-router-dom';
import { Map, Users, Tag, Puzzle, List, History } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function Sidebar() {
  const { t } = useTranslation();

  return (
    <aside className="bg-gray-800 text-white h-screen sm:p-2 py-2 sm:w-48 w-12 transition-all duration-300">
      <nav className="space-y-2">
        <Link
          to="/gallery"
          className="flex items-center justify-center sm:justify-start space-x-0 sm:space-x-2 px-3 py-2 rounded hover:bg-gray-700"
        >
          <Map size="1em" />
          <span className="hidden sm:inline">{t("navigation.gallery")}</span>
        </Link>

        <Link
          to="/authors"
          className="flex items-center justify-center sm:justify-start space-x-0 sm:space-x-2 px-3 py-2 rounded hover:bg-gray-700"
        >
          <Users size="1em" />
          <span className="hidden sm:inline">{t("navigation.authors")}</span>
        </Link>

        <Link
          to="/categories"
          className="flex items-center justify-center sm:justify-start space-x-0 sm:space-x-2 px-3 py-2 rounded hover:bg-gray-700"
        >
          <Tag size="1em" />
          <span className="hidden sm:inline">{t("navigation.categories")}</span>
        </Link>

        <Link
          to="/modules"
          className="flex items-center justify-center sm:justify-start space-x-0 sm:space-x-2 px-3 py-2 rounded hover:bg-gray-700"
        >
          <Puzzle size="1em" />
          <span className="hidden sm:inline">{t("navigation.modules")}</span>
        </Link>

        <Link
          to="/leaderboards"
          className="flex items-center justify-center sm:justify-start space-x-0 sm:space-x-2 px-3 py-2 rounded hover:bg-gray-700"
        >
          <List size="1em" />
          <span className="hidden sm:inline">{t("navigation.leaderboards")}</span>
        </Link>

        <Link
          to="/contests"
          className="flex items-center justify-center sm:justify-start space-x-0 sm:space-x-2 px-3 py-2 rounded hover:bg-gray-700"
        >
          <History size="1em" />
          <span className="hidden sm:inline">{t("navigation.contest_history")}</span>
        </Link>
      </nav>
    </aside>
  );
}