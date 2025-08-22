import { useEffect, useState } from 'react'
import './style/main.css'
import Searchbar from './Searchbar'
import { useTranslation } from 'react-i18next';
import MapThumbnail from './MapThumbnail'

export default function Gallery() {
  const { t } = useTranslation();
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
    <>
      <title>{t("gallery.title")}</title>
      <div className="sticky top-0 z-10">
        <Searchbar placeholder={t("gallery.search_placeholder")} />
      </div>
      <div className='mt-3 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3'>
        {maps.map(map => (
          <MapThumbnail
            code={map.code}
            category={map.category}
            author={map.author_name}
          />
        ))}
      </div>
    </>
  )
}