import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import './style/main.css'
import Searchbar from './Searchbar'
import CategoryIcon from './CategoryIcon'
import categories from './assets/categories.json'
import { Trans, useTranslation } from 'react-i18next';

export default function AuthorList() {
  const { t } = useTranslation();
  const [authors, setAuthors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const params = window.location.search;
    fetch(`/api/authors${params}`)
      .then(res => {
        if (!res.ok) throw new Error(`Status ${res.status}`)
        return res.json()
      })
      .then(data => {
        setAuthors(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setError('Could not load authors list.')
        setLoading(false)
      })
  }, [])

  if (loading) return <p>Loading...</p>
  if (error) return <p>{error}</p>

  return (
    <>
      <title>{t("author_list.title")}</title>
      <div className="sticky top-0 z-10">
        <Searchbar placeholder={t("author_list.search_placeholder")} />
      </div>
      <div className='mt-3 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3'>
        {authors.map(author => (
          <div
            key={author.name}
            className='bg-gray-100 rounded-sm shadow-lg px-2 py-1 truncate'
          >
            <Link
              className='flex items-center font-semibold text-sky-700 hover:text-sky-500 transition duration-200'
              to={`/author/${encodeURIComponent(author.name)}`}
            >
              {author.name}
            </Link>

            <hr class="border-1 border-t border-gray-400" />

            <span className="text-sm text-gray-800">
              <Trans
                i18nKey="info.map_count"
                count={author.total_maps}
                values={{ count: author.total_maps }}
                components={[
                  <Link
                    to={`/gallery?s=${encodeURIComponent(author.name)}`}
                    className="font-semibold text-sky-900 hover:text-sky-700 transition duration-200"
                  />
                ]}
              />
              &nbsp;&ndash;&nbsp;
              <Trans
                i18nKey="info.high_perm_count"
                count={author.total_high_perms}
                values={{ count: author.total_high_perms }}
                components={[
                  <Link
                    to={`/gallery?s=${encodeURIComponent(`${author.name} #h`)}`}
                    className="font-semibold text-sky-900 hover:text-sky-700 transition duration-200"
                  />
                ]}
              />
            </span>

            <div className='flex flex-wrap gap-1 my-1 text-sm text-gray-600'>
              {author.category_tags.map(category => (
                <Link
                  key={category}
                  to={`/category/${category}`}
                  className="font-semibold text-gray-700 text-xs flex items-center gap-1 bg-gray-400 rounded-sm px-1 hover:brightness-110 transition duration-200 cursor-pointer"
                  title={t(categories[category]?.name || categories.default.name)}
                >
                  <CategoryIcon category={category} />
                  <span>P{category}</span>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  )
}