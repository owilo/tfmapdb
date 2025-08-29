import { useCallback, useEffect, useRef, useState } from 'react'
import './style/main.css'
import Searchbar from './Searchbar'
import { useTranslation } from 'react-i18next';
import MapThumbnail from './MapThumbnail'

const DEFAULT_LIMIT = 20
const MAX_LIMIT = 100

export default function Gallery() {
  const { t } = useTranslation();

  const [maps, setMaps] = useState([])
  const [nextCursor, setNextCursor] = useState(null)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [paramsString, setParamsString] = useState(window.location.search || '')
  const sentinelRef = useRef(null)

  const loadingRef = useRef(false)

  const buildUrl = useCallback((cursor = null, limit = DEFAULT_LIMIT) => {
    const l = Math.max(1, Math.min(limit, MAX_LIMIT))
    const params = new URLSearchParams(paramsString)
    params.set('limit', String(l))
    if (cursor) params.set('cursor', cursor)
    else params.delete('cursor')
    return `/api/gallery?${params.toString()}`
  }, [paramsString])

  const fetchPage = useCallback(async (cursor = null, append = true) => {
    if (loadingRef.current) return
    loadingRef.current = true
    setLoading(true)
    setError(null)

    try {
      const url = buildUrl(cursor, DEFAULT_LIMIT)
      const res = await fetch(url)
      if (!res.ok) throw new Error(`Status ${res.status}`)
      const data = await res.json()

      const results = Array.isArray(data.results) ? data.results : []
      const next = data.next_cursor ?? null
      const more = typeof data.has_more === 'boolean' ? data.has_more : (next !== null)

      setMaps(prev => append ? [...prev, ...results] : results)
      setNextCursor(next)
      setHasMore(more)

    } catch (err) {
      console.error('Gallery fetch error', err)
      setError('Could not load gallery.')
    } finally {
      loadingRef.current = false
      setLoading(false)
    }
  }, [buildUrl])

  useEffect(() => {
    setMaps([])
    setNextCursor(null)
    setHasMore(true)
    setError(null)

    fetchPage(null, false)
  }, [paramsString, fetchPage])

  useEffect(() => {
    const onPop = () => setParamsString(window.location.search || '')
    window.addEventListener('popstate', onPop)

    const origPush = history.pushState
    history.pushState = function (...args) {
      const res = origPush.apply(this, args)
      window.dispatchEvent(new Event('popstate'))
      return res
    }

    return () => {
      window.removeEventListener('popstate', onPop)
      history.pushState = origPush
    }
  }, [])

  useEffect(() => {
    const sentinel = sentinelRef.current
    if (!sentinel) return

    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          if (hasMore && !loadingRef.current && nextCursor !== null) {
            fetchPage(nextCursor, true)
          } else if (hasMore && !loadingRef.current && nextCursor === null) {
            fetchPage(null, true)
          }
        }
      }
    }, {
      root: null,
      rootMargin: '400px',
      threshold: 0.01
    })

    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [hasMore, nextCursor, fetchPage])

  if (error) return <p>{error}</p>

  return (
    <>
      <title>{t("gallery.title")}</title>

      <div className="sticky top-0 z-10">
        <Searchbar placeholder={t("gallery.search_placeholder")} />
      </div>

      <div className='mt-3 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3'>
        {maps.map((map) => (
          <MapThumbnail
            key={map.code}
            code={map.code}
            category={map.category}
            author={map.author_name}
            similarity_score={map.similarity}
          />
        ))}
      </div>

      <div ref={sentinelRef} />

      <div className="mt-6 text-center">
        {loading && <div role="status" className='flex justify-center items-center'>
          <svg aria-hidden="true" className="w-6 h-6 text-white animate-spin dark:text-gray-600 fill-emerald-500" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor"/>
              <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="currentFill"/>
          </svg>
          <span className="text-lg text-gray-500">&nbsp;&nbsp;{t("navigation.loading")}</span>
        </div>}
      </div>
    </>
  )
}
