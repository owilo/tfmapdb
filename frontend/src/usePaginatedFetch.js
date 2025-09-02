import { useCallback, useEffect, useRef, useState } from 'react'

const DEFAULT_MAX_LIMIT = 100

export default function usePaginatedFetch({ endpoint, defaultLimit = 25, maxLimit = DEFAULT_MAX_LIMIT, useAbort = false }) {
  const [items, setItems] = useState([])
  const [nextCursor, setNextCursor] = useState(null)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [paramsString, setParamsString] = useState(window.location.search || '')

  const sentinelRef = useRef(null)
  const loadingRef = useRef(false)
  const abortRef = useRef(null)

  const buildUrl = useCallback((cursor = null, limit = defaultLimit) => {
    const l = Math.max(1, Math.min(limit, maxLimit))
    const params = new URLSearchParams(paramsString)
    params.set('limit', String(l))
    if (cursor) params.set('cursor', cursor)
    else params.delete('cursor')
    return `${endpoint}?${params.toString()}`
  }, [endpoint, paramsString, defaultLimit, maxLimit])

  const fetchPage = useCallback(async (cursor = null, append = true) => {
    if (loadingRef.current) return
    loadingRef.current = true
    setLoading(true)
    setError(null)

    if (useAbort) {
      if (abortRef.current) abortRef.current.abort()
      const ac = new AbortController()
      abortRef.current = ac
    }

    try {
      const url = buildUrl(cursor, defaultLimit)
      const res = await fetch(url, useAbort ? { signal: abortRef.current.signal } : undefined)
      if (!res.ok) throw new Error(`Status ${res.status}`)
      const data = await res.json()

      const results = Array.isArray(data.results) ? data.results : []
      const next = data.next_cursor ?? null
      const more = typeof data.has_more === 'boolean' ? data.has_more : (next !== null)

      setItems(prev => append ? [...prev, ...results] : results)
      setNextCursor(next)
      setHasMore(more)

    } catch (err) {
      if (err.name === 'AbortError') {
      } else {
        console.error(`${endpoint} fetch error`, err)
        setError('Could not load data.')
      }
    } finally {
      loadingRef.current = false
      setLoading(false)
      if (useAbort) abortRef.current = null
    }
  }, [buildUrl, defaultLimit, useAbort, endpoint])

  useEffect(() => {
    setItems([])
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
          if (hasMore && !loadingRef.current) {
            fetchPage(nextCursor, true)
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

  // helpers exposed
  const loadMore = useCallback(() => {
    if (!loadingRef.current && hasMore) fetchPage(nextCursor, true)
  }, [fetchPage, hasMore, nextCursor])

  const refresh = useCallback(() => {
    setItems([])
    setNextCursor(null)
    setHasMore(true)
    setError(null)
    fetchPage(null, false)
  }, [fetchPage])

  return {
    items,
    loading,
    error,
    hasMore,
    sentinelRef,
    loadMore,
    refresh,
    paramsString,
  }
}