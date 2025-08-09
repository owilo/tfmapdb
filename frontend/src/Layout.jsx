import Sidebar from './Sidebar';
import { Outlet } from 'react-router-dom';

export default function Layout() {
  return (
    <div className="flex flex-col h-screen">
      <header className="bg-gray-900 text-white py-1 px-6 shadow">
        <h1 className="text-lg font-semibold">tfmapdb</h1>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 p-3 overflow-auto bg-zinc-100">
          <Outlet />
        </main>
      </div>
    </div>
  );
}