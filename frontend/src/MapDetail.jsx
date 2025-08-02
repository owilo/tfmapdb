import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "./components/ui/collapsible";
import './style/Gallery.css'
import './style/animations.css'
import XMLViewer from './XMLViewer';

export default function MapDetail() {
  const { code } = useParams()
  const [entry, setEntry] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`/api/map/${code}/`)
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
  }, [code])

  if (loading) return <p>Loading…</p>
  if (error)   return <p style={{ color: 'red' }}>{error}</p>

  return (
    <div className='w-2xl p-2 mx-auto bg-neutral-200'>
      <Link to="/">← Back</Link>
      <h1>Entry #{entry.code}</h1>
      <img src={`/api/map/${entry.code}/image.png`} alt="Map" />

      <div>
        <Collapsible>
          <CollapsibleTrigger
            className="
              px-4 py-1 w-full text-start 
              bg-neutral-300 text-neutral-800 
              rounded-t-sm 
              rounded-b-sm 
              data-[state=open]:rounded-b-none
              hover:brightness-105 transition duration-200
            "
          >
            XML
          </CollapsibleTrigger>
          <CollapsibleContent
            className="
              overflow-hidden transition-all 
              data-[state=closed]:animate-collapsible-up 
              data-[state=open]:animate-collapsible-down
            "
          >
            <XMLViewer xml={entry.xml} />
          </CollapsibleContent>
        </Collapsible>
      </div>
    </div>
  )
}