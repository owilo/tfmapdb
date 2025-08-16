import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Tag, Puzzle, ChevronDown, Search } from 'lucide-react';
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
import tags from './assets/tags.json';
import CategoryIcon from './CategoryIcon';
import TagIcon from './TagIcon';
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

  const categoriesToDisplay = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 17, 18, 19, 20, 21, 22, 23, 24, 32, 34, 38, 41, 42, 44, 66
  ];

  const tagsToDisplay = [
    "hc", "div"
  ];

  return (
    <div className='w-full'>
      <form
        onSubmit={handleSubmit}
        className="flex justify-center items-center p-2 bg-gray-700 rounded-xl shadow-md"
      >
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          type="search"
          placeholder={placeholder}
          className="flex-1 px-4 py-1 border bg-white border-gray-400 rounded-lg rounded-r-none focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          className="px-3 py-1 bg-[#4667cf] text-white rounded-lg rounded-l-none flex items-center cursor-pointer hover:brightness-110 transition duration-200"
        >
          <Search size="1.5em" />
        </button>
      </form>
      {/*<div className="mx-2 flex items-center justify-center gap-10 text-gray-800 text-sm">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className='bg-gray-300 rounded-md px-2 py-1 hover:bg-gray-400 transition duration-200 flex items-center gap-1'>
              <Tag size="1.15em" className='inline' />
              <span className='relative -top-px'>Categories</span>
              <ChevronDown size="1.25em" className="inline" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-64" align="start">
            {categoriesToDisplay.map(category => (
              <DropdownMenuItem title={categories[category]?.description}>
                <CategoryIcon category={category} />
                {categories[category]?.name}
              </DropdownMenuItem>
            ))}*/}
            {/*<DropdownMenuLabel className="font-semibold">My Account</DropdownMenuLabel>
            <DropdownMenuGroup>
              <DropdownMenuItem>
                Profile
                <DropdownMenuShortcut>⇧⌘P</DropdownMenuShortcut>
              </DropdownMenuItem>
              <DropdownMenuItem>
                Billing
                <DropdownMenuShortcut>⌘B</DropdownMenuShortcut>
              </DropdownMenuItem>
              <DropdownMenuItem>
                Settings
                <DropdownMenuShortcut>⌘S</DropdownMenuShortcut>
              </DropdownMenuItem>
              <DropdownMenuItem>
                Keyboard shortcuts
                <DropdownMenuShortcut>⌘K</DropdownMenuShortcut>
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem>Team</DropdownMenuItem>
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>Invite users</DropdownMenuSubTrigger>
                <DropdownMenuPortal>
                  <DropdownMenuSubContent>
                    <DropdownMenuItem>Email</DropdownMenuItem>
                    <DropdownMenuItem>Message</DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem>More...</DropdownMenuItem>
                  </DropdownMenuSubContent>
                </DropdownMenuPortal>
              </DropdownMenuSub>
              <DropdownMenuItem>
                New Team
                <DropdownMenuShortcut>⌘+T</DropdownMenuShortcut>
              </DropdownMenuItem>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuItem>GitHub</DropdownMenuItem>
            <DropdownMenuItem>Support</DropdownMenuItem>
            <DropdownMenuItem disabled>API</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              Log out
              <DropdownMenuShortcut>⇧⌘Q</DropdownMenuShortcut>
            </DropdownMenuItem>*/}
          {/*</DropdownMenuContent>
        </DropdownMenu>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className='bg-gray-300 rounded-md px-2 py-1 hover:bg-gray-400 transition duration-200 flex items-center gap-1'>
              <Puzzle size="1.15em" className='inline' />
              <span className='relative -top-px'>Tags</span>
              <ChevronDown size="1.25em" className="inline" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-64" align="start">
            {tagsToDisplay.map(tag => (
              <DropdownMenuItem title={tags[tag]?.description}>
                <TagIcon tag={tag} />
                {tags[tag]?.name}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>*/}
    </div>
  );
}
