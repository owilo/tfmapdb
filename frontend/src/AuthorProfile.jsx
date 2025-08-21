import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import './style/main.css'
import './style/animations.css'

export default function AuthorProfile() {
  const { name } = useParams()
  const [entry, setEntry] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`/api/author/${encodeURIComponent(name)}/`)
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
        setError(`Could not load author ${name}.`)
        setLoading(false)
      })
  }, [name])

  if (loading) return <p>Loading…</p>
  if (error)   return <p style={{ color: 'red' }}>{error}</p>

  return (
    <>
      <title>{`${name}`}</title>
      <div className='w-2xl p-2 mx-auto bg-neutral-200'>
        <Link to="/authors">← Back</Link>
        <h1>Author {name}</h1>
        <pre>
            {console.log(entry)}
        </pre>
      </div>
    </>
  )
}