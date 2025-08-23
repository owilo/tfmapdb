import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Trans, useTranslation } from 'react-i18next';
import './style/main.css'
import './style/animations.css'
import CategoryIcon from './CategoryIcon';
import categories from './assets/categories.json';
import MapThumbnail from './MapThumbnail';

/**
 * description
 * number of maps
 * number of authors
 * latest permed maps
*/

export default function TagDetail({ type }) {
  const { t } = useTranslation();
  const { id } = useParams()
  const [tag, setTag] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`/api/${type}/${encodeURIComponent(id)}/`)
      .then(res => {
        if (!res.ok) throw new Error(`Status ${res.status}`)
        return res.json()
      })
      .then(data => {
        setTag(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setError(`Could not load tag or category ${id}.`)
        setLoading(false)
      })
  }, [name])

  if (loading) return <p>Loading…</p>
  if (error)   return <p style={{ color: 'red' }}>{error}</p>

  const isCategory = type === "category"
  const isKnown = categories[id] != null
  const idHeader = isCategory ? `P${id}` : id
  const pageTitle = isKnown && t(categories[id].name)

  const uriComponent = isCategory ? `%23${id}` : `%24${id}`

  return (
    <>
      <title>{isKnown ? `${idHeader} – ${pageTitle}` : `${idHeader}`}</title>

      <h1 className="flex items-center gap-2 px-2 mb-1 font-semibold text-emerald-600 text-2xl">
        {isKnown && <CategoryIcon category={id} />}
        {isKnown ? `${idHeader} – ${pageTitle}` : `${idHeader}`}
      </h1>

      <hr className="border-2 border-t border-gray-500" />

      <div className='my-3 space-y-3 px-1'>
        <div>
          <h2 className='font-light text-gray-600 text-lg mt-4'>
            {t(isCategory ? "tag_data.category_data" : "tag_data.tag_data")}
          </h2>
          <hr className="border-1 border-t border-gray-500 mb-2" />
        </div>

        <div
          className='flex flex-col bg-gray-200 rounded-sm shadow-lg px-2 py-1 truncate'
        >
          <span>
            {t("tag_data.perm_count")}&nbsp;
            <Link
              to={`/gallery?s=${uriComponent}`}
              className="font-semibold text-sky-900 hover:text-sky-700 transition duration-200"
            >
              {tag.total_maps}
            </Link>
          </span>
          <span>
            {t("tag_data.author_count")}&nbsp;
            <Link
              to={`/authors?s=${uriComponent}`}
              className="font-semibold text-sky-900 hover:text-sky-700 transition duration-200"
            >
              {tag.total_authors}
            </Link>
          </span>
        </div>

        <div>
          <h2 className='font-light text-gray-600 text-lg mt-4'>
            {t("tag_data.last_permed")}
            &nbsp;
            <Link
              to={`/gallery?s=${uriComponent}`}
              className="font-semibold text-sm text-sky-900 hover:text-sky-700 transition duration-200"
            >
              ({t("navigation.see_more")})
            </Link>
          </h2>
          <hr className="border-1 border-t border-gray-500 mb-2" />
        </div>

        <div className="overflow-x-scroll flex flex-nowrap space-x-2">
          {tag.last_permed.map(last_permed => (
            <div key={last_permed.code} className='w-1/3 lg:w-1/5 flex-shrink-0'>
              <MapThumbnail
                code={last_permed.code}
                category={last_permed.category}
                author={last_permed.author}
              />
            </div>
          ))}
        </div>
      </div>
    </>
  )
}