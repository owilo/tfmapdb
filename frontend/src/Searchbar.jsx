import './style/main.css';

export default function Searchbar() {
  return <div className='w-full flex justify-center items-center p-4 bg-neutral-100 rounded-lg shadow-md'>
    <input
      type="text"
      placeholder="Search maps..."
      className="w-full px-4 py-2 border border-neutral-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
    />
    <button className="ml-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors">
      Search
    </button>
  </div>
}
