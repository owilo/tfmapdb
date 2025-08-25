import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Funnel, Tag, Puzzle, ChevronDown, Search } from 'lucide-react';
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "./components/ui/collapsible";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "./components/ui/dropdown-menu";
import categories from './assets/categories.json';
//import tags from './assets/tags.json';
import CategoryIcon from './CategoryIcon';
//import TagIcon from './TagIcon';
import './style/main.css';
import { t } from 'i18next';

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

  const categoriesToDisplay = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 17, 18, 19, 20, 21, 22, 23, 24, 32, 34, 38, 41, 42, 44, 66
  ];

  const tagsToDisplay = [
    "hc", "div"
  ];

  // TODO Complete
  return (
    <div className='w-full'>
      <form
        onSubmit={handleSubmit}
      >
        <Collapsible>
          <div className='flex justify-center items-stretch shadow-md border-3 border-gray-400 rounded-xs'>
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              type="search"
              placeholder={placeholder}
              className="flex-1 px-4 py-1 bg-white focus:outline-none focus:shadow-[inset_0_-2px_0_0_theme(colors.emerald.500)] transition duration-200 rounded-l-xs"
            />
            <CollapsibleTrigger
              className="px-3 py-1 bg-emerald-500 text-white flex items-center cursor-pointer hover:brightness-110 data-[state=open]:brightness-120 data-[state=open]:hover:brightness-110 transition duration-200"
              title={t("search.advanced")}
            >
              <Funnel size="1.25em" />
            </CollapsibleTrigger>
            <button
              type="submit"
              className="px-3 py-1 bg-[#4667cf] text-white flex items-center cursor-pointer hover:brightness-110 transition duration-200 rounded-r-xs"
              title={t("search.search")}
            >
              <Search size="1.25em" />
            </button>
          </div>
          <CollapsibleContent className="overflow-hidden mx-1 p-1 shadow-md border-3 border-gray-400 rounded-xs space-y-1.5 bg-gray-300 data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down">
            <div className='flex items-stretch'>
              <span className='px-1 font-semibold text-gray-800'>Sort by:&nbsp;</span>
              <select className="px-1 bg-white focus:outline-none focus:shadow-[inset_0_-2px_0_0_theme(colors.emerald.500)] transition duration-200 rounded-xs shadow-md">
                <option value="code-asc">Map code (ascending)</option>
                <option value="code-asc">Map code (descending)</option>
                <option value="author-asc">Author (ascending)</option>
                <option value="author-desc">Author (descending)</option>
                <option value="category-asc">Category (ascending)</option>
                <option value="category-desc">Category (descending)</option>
              </select>
            </div>
            <div className='flex items-stretch'>
              <span className='px-1 font-semibold text-gray-800'>Code ranges:&nbsp;</span>
              <div className='flex items-stretch shadow-md'>
                <span className='font-bold bg-gray-400 rounded-l-xs text-gray-700 px-1 select-none'>@</span>
                <input
                  type="number"
                  placeholder="Start"
                  size="8"
                  min="0"
                  max="100000000"
                  className="px-1 bg-white focus:outline-none focus:shadow-[inset_0_-2px_0_0_theme(colors.emerald.500)] transition duration-200 rounded-r-xs"
                />
              </div>
              <span>&nbsp;-&nbsp;</span>
              <div className='flex items-stretch shadow-md'>
                <span className='font-bold bg-gray-400 rounded-l-xs text-gray-700 px-1 select-none'>@</span>
                <input
                  type="number"
                  placeholder="End"
                  size="8"
                  min="0"
                  max="100000000"
                  className="px-1 bg-white focus:outline-none focus:shadow-[inset_0_-2px_0_0_theme(colors.emerald.500)] transition duration-200 rounded-r-xs"
                />
              </div>
            </div>
            <div className='flex items-stretch'>
              <span className='px-1 font-semibold text-gray-800'>Authors:&nbsp;</span>
              <input
                  type="text"
                  placeholder="Author name"
                  maxLength="32"
                  className="px-1 bg-white focus:outline-none focus:shadow-[inset_0_-2px_0_0_theme(colors.emerald.500)] transition duration-200 rounded-xs"
                />
            </div>
            <div className='flex items-stretch'>
              <span className='px-1 font-semibold text-gray-800'>Categories:&nbsp;</span>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className='bg-gray-100 rounded-sm px-1 hover:bg-gray-400 transition duration-200 flex items-center gap-1'>
                    <Tag size="1em" className='inline' />
                    <span className='relative -top-px'>Categories</span>
                    <ChevronDown size="1.25em" className="inline" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-64" align="start">
                  {categoriesToDisplay.map(category => (
                    <DropdownMenuItem>
                      <CategoryIcon category={category} />
                      {categories[category]?.name}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
            <div className='flex items-stretch'>
              <span className='px-1 font-semibold text-gray-800'>Tags:&nbsp;</span>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className='bg-gray-100 rounded-sm px-1 hover:bg-gray-400 transition duration-200 flex items-center gap-1'>
                    <Puzzle size="1em" className='inline' />
                    <span className='relative -top-px'>Tags</span>
                    <ChevronDown size="1.25em" className="inline" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-64" align="start">
                  {tagsToDisplay.map(tag => (
                    <DropdownMenuItem>
                      <CategoryIcon category={tag} />
                      {categories[tag]?.name}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </form>
      {/*<div className="mt-2 mx-2 flex items-center justify-center gap-4 text-gray-800 text-sm">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className='bg-gray-100 rounded-sm px-1 hover:bg-gray-400 transition duration-200 flex items-center gap-1'>
              <Funnel size="1em" className='inline' />
              <span className='relative -top-px'>Sort</span>
              <ChevronDown size="1.25em" className="inline" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-64" align="start">
            <DropdownMenuItem>
              Asc
            </DropdownMenuItem>
            <DropdownMenuItem>
              Desc
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>*/}
    </div>
  );
}
