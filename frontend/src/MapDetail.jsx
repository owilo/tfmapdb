import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Image, BookOpen, Settings, ListCollapse, Book } from "lucide-react";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "./components/ui/collapsible";
import './style/main.css'
import './style/animations.css'
import XMLViewer from './XMLViewer';
import clsx from 'clsx';

export default function MapDetail() {
  const { code } = useParams()
  const [map, setMap] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`/api/map/${code}/`)
      .then(res => {
        if (!res.ok) throw new Error(`Status ${res.status}`)
        return res.json()
      })
      .then(data => {
        setMap(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setError('Could not load map detail.')
        setLoading(false)
      })
  }, [code])

  if (loading) return <p>Loading…</p>
  if (error)   return <p style={{ color: 'red' }}>{error}</p>

  const headerStyle = `
    flex items-center space-x-2
    px-2 py-1 w-full text-start 
    bg-gray-300 text-gray-800 
    rounded-t-sm 
    rounded-b-sm 
    data-[state=open]:rounded-b-none
    hover:brightness-105 transition duration-200
  `
  const contentStyle = `
    p-1
    bg-gray-100 text-gray-800
    overflow-hidden transition-all 
    data-[state=closed]:animate-collapsible-up 
    data-[state=open]:animate-collapsible-down
    rounded-b-sm
  `

  return (
    <>
      <title>{`@${map.code}`}</title>
      <meta name="author" content={map.author.name} />
      <div className="flex flex-col h-full bg-gray-200 rounded-lg shadow-lg overflow-hidden">
        <div className="relative bg-gray-300 text-gray-900 font-bold text-lg p-1 rounded-lg shadow-lg">
          <Link
            to="/gallery"
            aria-label="Back to gallery"
            className="absolute top-1/2 transform -translate-y-1/2 left-1 bg-gray-400 flex items-center rounded-full p-1 text-gray-600 hover:brightness-110 transition duration-200"
          >
            <ArrowLeft className="w-3 h-3" />
            <span className='text-xs px-1'>Back to gallery</span>
          </Link>

          <h1 className="text-center font-semibold text-gray-800 text-xl">
            @{map?.code}
          </h1>
        </div>

        <div className="flex flex-1 overflow-hidden">
          <div className="w-3/5 flex overflow-auto flex-col border-r border-neutral-300 p-2 space-y-2">
            <Collapsible defaultOpen>
              <CollapsibleTrigger className={clsx(headerStyle)}>
                <Image size='1.25em' />
                <span className='relative -top-px'>Map image</span>
              </CollapsibleTrigger>
              <CollapsibleContent className={clsx(contentStyle)}>
                <div className="p-2">
                  <img
                    src={`/api/map/${map.code}/image.png`}
                    alt="Map"
                    loading="lazy"
                    className="w-full object-contain bg-[#6a7495] max-h-[300px]"
                  />
                  {/*style={{ maxHeight: `${map.map_data.height}px` }}*/}
                </div>
              </CollapsibleContent>
            </Collapsible>

            <Collapsible defaultOpen>
              <CollapsibleTrigger className={clsx(headerStyle)}>
                <BookOpen size='1.25em' />
                <span className='relative -top-px'>Map information</span>
              </CollapsibleTrigger>
              <CollapsibleContent className={clsx(contentStyle)}>
                <ul>
                  <li><span className='font-semibold'>Code:</span> @{map.code}</li>
                  <li><span className='font-semibold'>Author:</span> {map.author.name}</li>
                  <li><span className='font-semibold'>Category:</span> P{map.category}</li>
                </ul>
              </CollapsibleContent>
            </Collapsible>

            <Collapsible defaultOpen>
              <CollapsibleTrigger className={clsx(headerStyle)}>
                <Settings size='1.25em' />
                <span className='relative -top-px'>Map properties</span>
              </CollapsibleTrigger>
              <CollapsibleContent className={clsx(contentStyle)}>
                <ul>
                  <li><span className='font-semibold'>Dimensions:</span> {map.map_data.length}&times;{map.map_data.height}</li>
                </ul>
              </CollapsibleContent>
            </Collapsible>

            <Collapsible defaultOpen>
              <CollapsibleTrigger className={clsx(headerStyle)}>
                <ListCollapse size='1.25em' />
                <span className='relative -top-px'>Content information</span>
              </CollapsibleTrigger>
              <CollapsibleContent className={clsx(contentStyle)}>
                <ul>
                  <li><span className='font-semibold'>Grounds count:</span> {map.map_data.grounds_count}/60</li>
                  <li><span className='font-semibold'>Decorations count:</span> {map.map_data.decorations_count}</li>
                  <li><span className='font-semibold'>Objects count:</span> {map.map_data.objects_count}/40</li>
                  <li><span className='font-semibold'>Joints count:</span> {map.map_data.joints_count}</li>
                </ul>
              </CollapsibleContent>
            </Collapsible>
          </div>

          <div className="w-2/5 overflow-auto p-2">
            <XMLViewer xml={map.xml} indentSize={2} />
          </div>
        </div>
      </div>
    </>
  )
}