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
import clsx from 'clsx';

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

  const headerStyle = `
    px-4 py-1 w-full text-start 
    bg-neutral-300 text-neutral-800 
    rounded-t-sm 
    rounded-b-sm 
    data-[state=open]:rounded-b-none
    hover:brightness-105 transition duration-200
  `
  const contentStyle = `
    overflow-hidden transition-all 
    data-[state=closed]:animate-collapsible-up 
    data-[state=open]:animate-collapsible-down
  `

  return (
    <div className='w-2xl p-2 mx-auto bg-neutral-200'>
      <Link to="/gallery">← Back</Link>
      <h1>Map @{entry.code}</h1>
      <Collapsible defaultOpen>
        <CollapsibleTrigger className={clsx(headerStyle)}>Image</CollapsibleTrigger>
        <CollapsibleContent className={clsx(contentStyle)}>
          <img src={`/api/map/${entry.code}/image.png`} alt="Map" />
        </CollapsibleContent>
      </Collapsible>

      <Collapsible>
        <CollapsibleTrigger className={clsx(headerStyle)}>XML</CollapsibleTrigger>
        <CollapsibleContent className={clsx(contentStyle)}>
          <XMLViewer xml={entry.xml} maxLines={15} indentSize={4} />
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}