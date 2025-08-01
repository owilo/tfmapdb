import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

export default function Gallery() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/')
      .then(res => {
        if (!res.ok) throw new Error(`Status ${res.status}`)
        return res.json()
      })
      .then(data => {
        setItems(data)
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
    <div style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}>
      {items.map(item => (
        <div key={item.code} style={{ border: '1px solid #ccc', padding: '1rem', borderRadius: '8px' }}>
          <h3>{item.author_name}</h3>
          <h3>P{item.category_id}</h3>
          <h3>@{item.code}</h3>
          <img src={`/api/map/${item.code}/image.png`} alt="Map" style={{ width: '100%', borderRadius: '4px' }} />
          <Link to={`/map/${item.code}`}>View Details</Link>
        </div>
      ))}
    </div>
  )
}
