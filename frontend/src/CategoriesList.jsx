import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import './style/main.css'
import Searchbar from './Searchbar'
import CategoryIcon from './CategoryIcon'
import categories from './assets/categories.json'

export default function CategoriesList() {
  const [categoriesData, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const params = window.location.search;
    fetch(`/api/categories${params}`)
      .then(res => {
        if (!res.ok) throw new Error(`Status ${res.status}`)
        return res.json()
      })
      .then(data => {
        setCategories(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setError('Could not load categories list.')
        setLoading(false)
      })
  }, [])

  if (loading) return <p>Loading...</p>
  if (error) return <p>{error}</p>

  return (
    <>
      <title>Map categories</title>
      <div className="sticky top-0 z-10">
        <Searchbar placeholder='Search categories' />
      </div>
      <div className='mt-3 grid grid-cols-2 gap-3'>
        {categoriesData.map(categoryData => (
          <div 
            key={categoryData.category} 
            className='bg-gray-300 rounded-lg shadow-lg px-1 flex items-center gap-2 truncate border-gray-400 border-2'
          >
            <div className='h-full py-1'>
              <Link
                to={`/category/${categoryData.category}`}
                className="flex items-center justify-center text-3xl w-12 text-gray-800 rounded-sm bg-gray-400 h-full py-1 hover:brightness-110 transition duration-200 cursor-pointer"
              >
                <CategoryIcon category={categoryData.category} />
              </Link>
            </div>

            <div className="flex flex-col">
              <span className='font-semibold'>
                P{categoryData.category} &ndash; {categories[categoryData.category].name}
              </span>
              <span className="text-sm text-gray-800">
                <Link
                  to={`/gallery?s=%23${categoryData.category}`}
                  className='font-semibold'
                >
                  {categoryData.maps_count}
                </Link> maps &ndash; <Link
                  to={`/authors?s=%23${categoryData.category}`}
                  className='font-semibold'
                >
                  {categoryData.authors_count}
                </Link> authors
              </span>
              <span className="text-sm text-gray-600">
                {categories[categoryData.category].description}
              </span>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}