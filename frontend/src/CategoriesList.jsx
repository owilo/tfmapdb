import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import './style/main.css'
import Searchbar from './Searchbar'

export default function CategoriesList() {
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
            <div className='text-sm text-gray-600'>High categories:&nbsp;
              <span className='font-semibold'>{author.total_high_categories}</span>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}