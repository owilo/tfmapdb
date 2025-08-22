import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Trans, useTranslation } from 'react-i18next';
import './style/main.css'
import './style/animations.css'
import CategoryIcon from './CategoryIcon';
import categories from './assets/categories.json';

export default function AuthorProfile() {
  const { t } = useTranslation();
  const { name } = useParams()
  const [author, setAuthor] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`/api/author/${encodeURIComponent(name)}/`)
      .then(res => {
        if (!res.ok) throw new Error(`Status ${res.status}`)
        return res.json()
      })
      .then(data => {
        setAuthor(data)
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

      <h1 className="px-2 mb-1 font-semibold text-emerald-600 text-2xl">
        {name}
      </h1>

      <hr className="border-2 border-t border-gray-500" />

      <div className='my-3 space-y-3 px-1'>
        <Link
          to={`https://atelier801.com/profile?pr=${encodeURIComponent(name)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block bg-sky-700 text-white font-semibold px-2 py-1 rounded hover:bg-sky-600 transition duration-200"
        >
          <span className="flex items-center">
            <img src="/src/assets/images/atelier801.png" alt="Atelier801" className="h-5 w-auto align-middle mr-1" />
            <span className="ml-1 relative -top-px">{t("author_profile.view_on_atelier801")}</span>
          </span>
        </Link>

        <div>
          <h2 className='font-light text-gray-600 text-lg'>{t("author_profile.maps_statistics")}</h2>
          <hr className="border-1 border-t border-gray-500 mb-2" />
        </div>

        <div
          className='flex flex-col bg-gray-200 rounded-sm shadow-lg px-2 py-1 truncate'
        >
          <span>
            {t("author_profile.map_count")}&nbsp;
            <Link
              to={`/gallery?s=${encodeURIComponent(name)}`}
              className="font-semibold text-sky-900 hover:text-sky-700 transition duration-200"
            >
              {author.total_maps}
            </Link>
          </span>
          <span>
            {t("author_profile.perm_count")}&nbsp;
            <Link
              to={`/gallery?s=${encodeURIComponent(`${name} #h`)}`}
              className="font-semibold text-sky-900 hover:text-sky-700 transition duration-200"
            >
              {author.permed_maps}
            </Link>
          </span>
          <span>
            {t("author_profile.high_perm_count")}&nbsp;
            <Link
              to={`/gallery?s=${encodeURIComponent(`${name} #h`)}`}
              className="font-semibold text-sky-900 hover:text-sky-700 transition duration-200"
            >
              {author.high_maps}
            </Link>
          </span>
          <span>
            {t("author_profile.categories")}&nbsp;
            <span className='space-x-1'>
              {author.categories.map(categoryEntry => (categoryEntry.permanent &&
                <Link
                  to={`/category/${categoryEntry.category}`}
                  className="font-semibold text-gray-700 text-xs inline-flex items-center gap-1 bg-gray-400 rounded-sm px-1 hover:brightness-110 transition duration-200 cursor-pointer"
                  title={t(categories[categoryEntry.category]?.name || categories.default.name)}
                >
                  <CategoryIcon category={categoryEntry.category} />
                  <span>P{categoryEntry.category}</span>
                </Link>
              ))}
            </span>
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {author.categories.map(categoryEntry => (
            <div
              key={categoryEntry.category}
              className='flex justify-between bg-gray-200 rounded-sm shadow-lg px-2 py-1 truncate'
            >
              <Link
                to={`/category/${encodeURIComponent(categoryEntry.category)}`}
                className="flex items-center transition duration-200 cursor-pointer font-semibold text-sky-700 hover:text-sky-500 mr-2"
              >
                <CategoryIcon category={categoryEntry.category} />
                <span className='relative font-semibold -top-px truncate'>
                  &nbsp;P{categoryEntry.category} &ndash; {t(categories[categoryEntry.category]?.name)}
                </span>
              </Link>
              <span className='relative -top-px'>
                <Trans
                  i18nKey="info.map_count"
                  count={categoryEntry.map_count}
                  values={{ count: categoryEntry.map_count }}
                  components={[
                    <Link
                      to={`/gallery?s=${encodeURIComponent(`${name} #${categoryEntry.category}`)}`}
                      className="font-semibold text-sky-900 hover:text-sky-700 transition duration-200"
                    />
                  ]}
                />
              </span>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}