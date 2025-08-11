import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import './style/main.css'
import Searchbar from './Searchbar'
import CategoryIcon from './CategoryIcon'
import categories from './assets/categories.json'

export default function Gallery() {
  const [maps, setMaps] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const params = window.location.search;
    fetch(`/api/gallery${params}`)
      .then(res => {
        if (!res.ok) throw new Error(`Status ${res.status}`)
        return res.json()
      })
      .then(data => {
        setMaps(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setError('Could not load gallery.')
        setLoading(false)
      })
  }, [])

  if (loading) return <p>Loading...</p>
  if (error) return <p>{error}</p>

  return (
    <>
      <title>Map gallery</title>
      <div className="sticky top-0 z-10">
        <Searchbar placeholder='Search maps' />
      </div>
      <div className='mt-3 grid grid-cols-5 gap-3'>
        {maps.map(map => (
          <div key={map.code} className='bg-gray-300 rounded-lg shadow-lg px-1 truncate border-gray-400 border-2'>
            <div className="flex justify-between items-center">
              <div className="font-semibold text-gray-800">@{map.code}</div>
              <Link
                to={`/category/${map.category}`}
                className="font-semibold text-gray-700 text-xs flex items-center gap-1 bg-gray-400 rounded-sm px-1 hover:brightness-110 transition duration-200 cursor-pointer"
                title={categories[map.category]?.name || 'Unknown Category'}
              >
                <CategoryIcon category={map.category} />
                <span>P{map.category}</span>
              </Link>
            </div>
            <Link to={`/map/${map.code}`}>
              <img src={`/api/map/${map.code}/image.png`} alt="Map" className='w-full rounded-sm hover:brightness-110 transition duration-200' loading="lazy" />
            </Link>

            <div className='text-sm text-gray-600'>by <Link to={`/author/${encodeURIComponent(map.author_name)}`} className='font-semibold text-sky-800 hover:text-sky-700 transition duration-200'>{map.author_name}</Link></div>  
          </div>
        ))}
      </div>
    </>
  )
}