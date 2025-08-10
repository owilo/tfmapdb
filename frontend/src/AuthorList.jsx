import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import './style/main.css'
import Searchbar from './Searchbar'
import CategoryIcon from './CategoryIcon'
import categories from './assets/categories.json'

export default function AuthorList() {
  const [authors, setAuthors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const params = window.location.search;
    fetch(`/api/authors${params}`)
      .then(res => {
        if (!res.ok) throw new Error(`Status ${res.status}`)
        return res.json()
      })
      .then(data => {
        setAuthors(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setError('Could not load authors list.')
        setLoading(false)
      })
  }, [])

  if (loading) return <p>Loading...</p>
  if (error) return <p>{error}</p>

  return (
    <>
      <title>Map authors</title>
      <div className="sticky top-0 z-10">
        <Searchbar placeholder='Search authors' />
      </div>
      <div className='mt-4 grid grid-cols-4 gap-4'>
        {authors.map(author => (
          <div key={author.name} className='bg-gray-300 rounded-lg shadow-lg px-1'>
            <div className='font-semibold text-sky-800 hover:text-sky-700 transition duration-200'>
              <Link to={`/author/${encodeURIComponent(author.name)}`}>{author.name}</Link>
            </div>
            <div className='text-sm text-gray-600'>Maps:&nbsp;
              <Link to={`/gallery?s=${encodeURIComponent(author.name)}`}><span className='font-semibold'>{author.total_maps}</span></Link>
            </div>
            <div className='text-sm text-gray-600'>High perms:&nbsp;
              <Link to={`/gallery?s=${encodeURIComponent(`${author.name} #h`)}`}><span className='font-semibold'>{author.total_high_perms}</span></Link>
            </div>
            <div className='flex flex-wrap gap-1 my-1 text-sm text-gray-600'>
              {author.high_categories.map(category => (
                <Link
                  key={category}
                  to={`/category/${category}`}
                  className="font-semibold text-gray-700 text-xs flex items-center gap-1 bg-gray-400 rounded-sm px-1 hover:brightness-110 transition duration-200 cursor-pointer"
                  title={categories[category]?.name || 'Unknown Category'}
                >
                  <CategoryIcon category={category} />
                  <span>P{category}</span>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  )
}