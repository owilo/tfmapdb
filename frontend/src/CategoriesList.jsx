import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import './style/main.css'
import Searchbar from './Searchbar'
import CategoryIcon from './CategoryIcon'
import categories from './assets/categories.json'
import { Trans, useTranslation } from 'react-i18next';

export default function CategoriesList() {
  const { t } = useTranslation();
  const [categoriesData, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const params = window.location.search;
    fetch(`/api/categories${params}`)
      .then(res => {
        if (!res.ok) throw new Error(`Status ${res.status}`)
        return res.json()
      })
      .then(data => {
        setCategories(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setError('Could not load categories list.')
        setLoading(false)
      })
  }, [])

  if (loading) return <p>Loading...</p>
  if (error) return <p>{error}</p>

  return (
    <>
      <title>{t("categories_list.title")}</title>
      <div className="sticky top-0 z-10">
        <Searchbar placeholder={t("categories_list.search_placeholder")} />
      </div>
      <div className='mt-3 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3'>
        {categoriesData.map(categoryData => (
          <div 
            key={categoryData.category} 
            className='bg-gray-200 rounded-sm shadow-lg px-2 py-1 truncate'
          >
            <div>
              <Link
                to={`/category/${categoryData.category}`}
                className="flex items-center transition duration-200 cursor-pointer font-semibold text-sky-800 hover:text-sky-600"
              >
                <CategoryIcon category={categoryData.category} />
                <span className='relative font-semibold -top-px truncate'>
                  &nbsp;P{categoryData.category} &ndash; {t(categories[categoryData.category].name)}
                </span>
              </Link>
            </div>

            <hr class="border-1 border-t border-gray-400" />
              
            <span className="text-sm text-gray-800">
              <Trans
                i18nKey="info.map_count"
                count={categoryData.maps_count}
                values={{ count: categoryData.maps_count }}
                components={[
                  <Link
                    to={`/gallery?s=%23${categoryData.category}`}
                    className="font-semibold text-sky-900 hover:text-sky-700 transition duration-200"
                  />
                ]}
              />
              &nbsp;&ndash;&nbsp;
              <Trans
                i18nKey="info.author_count"
                count={categoryData.authors_count}
                values={{ count: categoryData.authors_count }}
                components={[
                  <Link
                    to={`/authors?s=%23${categoryData.category}`}
                    className="font-semibold text-sky-900 hover:text-sky-700 transition duration-200"
                  />
                ]}
              />
            </span>
            {/*<span className="text-sm text-gray-600">
              {categories[categoryData.category].description}
            </span>*/}
          </div>
        ))}
      </div>
    </>
  )
}