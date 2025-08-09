import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import './style/main.css'
import Searchbar from './Searchbar'

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
        <Searchbar />
      </div>
      <div className='mt-4 grid grid-cols-5 gap-4'>
        {authors.map(author => (
          <div key={author.name} className='bg-gray-300 rounded-lg shadow-lg px-1'>
            <span>{author.name}&nbsp;{author.total_maps}&nbsp;{author.total_high_categories}&nbsp;{author.total_high_perms}</span>
          </div>
        ))}
      </div>
    </>
  )
}