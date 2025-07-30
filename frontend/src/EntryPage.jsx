import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'

export default function EntryPage() {
  const { id } = useParams()
  const [entry, setEntry] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`/api/entry/${id}/`)
      .then(res => {
        if (!res.ok) throw new Error(`Status ${res.status}`)
        return res.json()
      })
      .then(data => {
        setEntry(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setError('Could not load entry.')
        setLoading(false)
      })
  }, [id])

  if (loading) return <p>Loading…</p>
  if (error)   return <p style={{ color: 'red' }}>{error}</p>

  return (
    <div style={{
      maxWidth: '600px',
      margin: '2rem auto',
      padding: '1.5rem',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      borderRadius: '8px',
      background: '#600'
    }}>
      <Link to="/">← Back</Link>
      <h1>Entry #{entry.id}</h1>
      <p style={{ whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>{entry.text}</p>
    </div>
  )
}