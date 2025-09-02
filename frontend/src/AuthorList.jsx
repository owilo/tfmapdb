import React from 'react'
import { Link } from 'react-router-dom'
import './style/main.css'
import Searchbar from './Searchbar'
import CategoryIcon from './CategoryIcon'
import categories from './assets/categories.json'
import { Trans, useTranslation } from 'react-i18next'
import usePaginatedFetch from './usePaginatedFetch'

export default function AuthorList() {
  const { t } = useTranslation()

  const { items: authors, loading, error, sentinelRef } = usePaginatedFetch({ endpoint: '/api/authors', defaultLimit: 36, useAbort: true })

  if (loading && authors.length === 0) return <p>{t('loading') || 'Loading...'}</p>
  if (error && authors.length === 0) return <p>{error}</p>

  return (
    <>
      <title>{t('author_list.title')}</title>
      <div className="sticky top-0 z-10">
        <Searchbar placeholder={t('author_list.search_placeholder')} />
      </div>

      <div className='mt-3 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 items-start'>
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

            <hr className="border-1 border-t border-gray-400" />

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

      <div ref={sentinelRef} />

      <div className="mt-6 text-center">
        {loading && <div role="status" className='flex justify-center items-center'>
          <svg aria-hidden="true" className="w-6 h-6 text-white animate-spin dark:text-gray-600 fill-emerald-500" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor"/>
              <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="currentFill"/>
          </svg>
          <span className="text-lg text-gray-500">&nbsp;&nbsp;{t('navigation.loading')}</span>
        </div>}
      </div>
    </>
  )
}