import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import './style/main.css'

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
    <div className='grid grid-cols-5 gap-4'>
      {maps.map(map => (
        <Link to={`/map/${map.code}`}>
          <div key={map.code} className='bg-neutral-300 rounded-lg p-2 hover:brightness-110 transition duration-200'>
            <div className='flex justify-between text-lg'>
              <div>@{map.code}</div>
              <div>P{map.category_id}</div>
            </div>
            
            <img src={`/api/map/${map.code}/image.png`} alt="Map" className='w-full rounded-sm' />

            <div className='text-sm text-neutral-800'>by {map.author_name}</div>  
          </div>
        </Link>
      ))}
    </div>
  )
}