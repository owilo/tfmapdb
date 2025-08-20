import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import './style/main.css'
import Searchbar from './Searchbar'
import CategoryIcon from './CategoryIcon'
import categories from './assets/categories.json'
import { Trans, useTranslation } from 'react-i18next';

function groupBySupercategoriesGeneric(items = [], supercategories = {}, otherKey = 'supercategories.other', getId = (it) => (it.category ?? it.tag ?? it.id ?? it.name ?? '').toString()) {
  const idToSuper = {}
  for (const [scKey, ids] of Object.entries(supercategories)) {
    for (const id of ids) {
      idToSuper[String(id)] = scKey
    }
  }

  const order = Object.keys(supercategories).concat([otherKey])
  const buckets = {}
  order.forEach(k => { buckets[k] = [] })

  for (const item of items) {
    const rawId = getId(item)
    const idStr = rawId === undefined || rawId === null ? '' : String(rawId)
    const sc = idToSuper[idStr] || otherKey
    if (!buckets[sc]) buckets[sc] = []
    buckets[sc].push(item)
  }

  return { order, buckets }
}

function ItemCard({ item, isTag = false }) {
  const { t } = useTranslation()
  const idKey = item.category ?? item.tag ?? item.id ?? item.name ?? ''
  const labelKey = categories[idKey]?.name

  const mainLink = isTag ? `/tag/${encodeURIComponent(idKey)}` : `/category/${encodeURIComponent(idKey)}`
  const galleryQuery = isTag ? `/gallery?s=%24${encodeURIComponent(idKey)}` : `/gallery?s=%23${encodeURIComponent(idKey)}`
  const authorsQuery = isTag ? `/authors?s=%24${encodeURIComponent(idKey)}` : `/authors?s=%23${encodeURIComponent(idKey)}`

  return (
    <div 
      key={String(idKey)} 
      className='bg-gray-200 rounded-sm shadow-lg px-2 py-1 truncate'
    >
      <div>
        <Link
          to={mainLink}
          className="flex items-center transition duration-200 cursor-pointer font-semibold text-sky-800 hover:text-sky-600"
        >
          <CategoryIcon category={idKey} />
          <span className='relative font-semibold -top-px truncate'>
            &nbsp;{isTag ? idKey : `P${idKey}`}{labelKey && <> &ndash; {t(labelKey)}</>}
          </span>
        </Link>
      </div>

      <hr className="border-1 border-t border-gray-400" />
        
      <span className="text-sm text-gray-800">
        <Trans
          i18nKey="info.map_count"
          count={item.maps_count}
          values={{ count: item.maps_count }}
          components={[
            <Link
              to={galleryQuery}
              className="font-semibold text-sky-900 hover:text-sky-700 transition duration-200"
            />
          ]}
        />
        &nbsp;&ndash;&nbsp;
        <Trans
          i18nKey="info.author_count"
          count={item.authors_count}
          values={{ count: item.authors_count }}
          components={[
            <Link
              to={authorsQuery}
              className="font-semibold text-sky-900 hover:text-sky-700 transition duration-200"
            />
          ]}
        />
      </span>
    </div>
  )
}

export default function CategoriesList() {
  const { t } = useTranslation();
  const [categoriesData, setCategories] = useState([])
  const [tagsData, setTags] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const other = 'supercategories.other'
  const supercategories = {
    'supercategories.normal' : [0, 1, 4, 5, 6, 7, 8, 9, 12, 66],
    'supercategories.bootcamp' : [3, 13],
    'supercategories.survivor' : [10, 11, 24],
    'supercategories.racing' : [17, 38],
    'supercategories.defilante' : [18],
    'supercategories.module' : [41],
    'supercategories.tribehouse' : [22],
    'supercategories.test' : [20, 21, 23, 32, 34, 42],
    'supercategories.deleted' : [43, 44],
  }

  const otherTagKey = 'supercategories.other_tags'
  const tagSupercategories = {
    'supercategories.module_tags': ["hc", "div"],
    'supercategories.contest_tags': ["ctst2024", "ctst2025"],
  }

  useEffect(() => {
    const params = window.location.search;
    setLoading(true)
    setError(null)

    const fetchCategories = fetch(`/api/categories${params}`).then(res => {
      if (!res.ok) throw new Error(`Status ${res.status}`)
      return res.json()
    })

    const fetchTags = fetch(`/api/tags${params}`).then(res => {
      if (!res.ok) throw new Error(`Status ${res.status}`)
      return res.json()
    })

    Promise.all([fetchCategories, fetchTags])
      .then(([cats, tgs]) => {
        setCategories(cats || [])
        setTags(tgs || [])
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setError('Could not load categories or tags.')
        setLoading(false)
      })
  }, [])

  const groupedCategories = useMemo(
    () => groupBySupercategoriesGeneric(categoriesData, supercategories, other, (it) => Number(it.category)),
    [categoriesData]
  )

  const groupedTags = useMemo(
    () => groupBySupercategoriesGeneric(tagsData, tagSupercategories, otherTagKey, (it) => (it.tag ?? it.category ?? it.id ?? it.name ?? '').toString()),
    [tagsData]
  )

  if (loading) return <p>Loading...</p>
  if (error) return <p>{error}</p>

  return (
    <>
      <title>{t("categories_list.title")}</title>

      <div className="sticky top-0 z-10">
        <Searchbar placeholder={t("categories_list.search_placeholder")} />
      </div>

      <div className="space-y-3 mt-3">
        {groupedCategories.order.map(scKey => {
          const items = groupedCategories.buckets[scKey] || []
          if (!items.length) return null

          return (
            <section key={scKey}>
              <p className='font-light text-gray-600'>{t(scKey)}</p>

              <hr className="border-1 border-t border-gray-500 mb-2" />

              <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3'>
                {items.map(categoryData => (
                  <ItemCard key={String(categoryData.category)} item={categoryData} />
                ))}
              </div>
            </section>
          )
        })}

        {groupedTags.order.map(scKey => {
          const items = groupedTags.buckets[scKey] || []
          if (!items.length) return null

          return (
            <section key={scKey} className="mt-2">
              <p className='font-light text-gray-600'>{t(scKey)}</p>

              <hr className="border-1 border-t border-gray-500 mb-2" />

              <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3'>
                {items.map(tagItem => (
                  <ItemCard key={(tagItem.tag ?? tagItem.category ?? tagItem.id ?? tagItem.name)} item={tagItem} isTag />
                ))}
              </div>
            </section>
          )
        })}
      </div>
    </>
  )
}