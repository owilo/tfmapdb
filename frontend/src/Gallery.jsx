import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import './style/main.css'
import Searchbar from './Searchbar'
import CategoryIcon from './CategoryIcon'
import categories from './assets/categories.json'
import { Trans, useTranslation } from 'react-i18next';

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
          <div
            key={map.code}
            className='bg-gray-200 rounded-sm shadow-lg px-2 py-1 truncate'
          >
            <div className="flex justify-between items-center">
              <Link
                to={`/map/${map.code}`}
                className="font-semibold text-sky-700 hover:text-sky-500 transition duration-200"
              >
                @{map.code}
              </Link>
              <Link
                to={`/category/${map.category}`}
                className="font-semibold text-gray-700 text-xs flex items-center gap-1 bg-gray-400 rounded-sm px-1 hover:brightness-110 transition duration-200 cursor-pointer"
                title={t(categories[map.category]?.name || categories.default.name)}
              >
                <CategoryIcon category={map.category} />
                <span>P{map.category}</span>
              </Link>
            </div>

            <Link to={`/map/${map.code}`}>
              <img src={`/api/map/${map.code}/image.png`} alt="Map" className='w-full rounded-sm hover:brightness-110 transition duration-200' loading="lazy" />
            </Link>

            <div className="text-sm text-gray-600">
              <Trans
                i18nKey="gallery.by_user"
                values={{ user: map.author_name }}
                components={[
                  <Link
                    to={`/author/${encodeURIComponent(map.author_name)}`}
                    className="font-semibold text-sky-900 hover:text-sky-700 transition duration-200"
                  />
                ]}
              />
            </div>  
          </div>
        ))}
      </div>
    </>
  )
}