import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import './style/main.css'
import Searchbar from './Searchbar'
import CategoryIcon from './CategoryIcon'
import categories from './assets/categories.json'
import { Trans, useTranslation } from 'react-i18next'
import clsx from 'clsx'

const OTHER_KEY = 'supercategories.other'

const SUPER_CATEGORIES = {
  'supercategories.normal': [0, 1, 4, 5, 6, 7, 8, 9, 12, 66],
  'supercategories.bootcamp': [3, 13],
  'supercategories.survivor': [10, 11, 24],
  'supercategories.racing': [17],
  'supercategories.defilante': [18],
  'supercategories.module': [41],
  'supercategories.tribehouse': [22],
  'supercategories.test': [20, 21, 23, 32, 34, 42, 38, 60, 87],
  'supercategories.deleted': [43, 44],
}

const TAG_TABS = {
  modules: {
    ids: ['hc', 'div', 'ninja', 'lavarun', 'discodance', 'signal'],
    titleKey: 'categorytabs.module_tags',
  },
  contests: {
    ids: ['ctst2024', 'ctst2025'],
    titleKey: 'categorytabs.contest_tags',
  },
  automatic: {
    ids: ['autowin', 'afkdeath'],
    titleKey: 'categorytabs.automatic_tags',
  },
}

const getId = (it) => String(it?.category ?? it?.tag ?? it?.id ?? it?.name ?? '').trim()

function groupBySupercategories(items = [], supercategories = {}, otherKey = OTHER_KEY, getIdFn = getId) {
  const idToSuper = new Map()
  for (const [scKey, ids] of Object.entries(supercategories)) {
    for (const id of ids) idToSuper.set(String(id), scKey)
  }

  const order = Object.keys(supercategories).concat([otherKey])
  const buckets = Object.fromEntries(order.map((k) => [k, []]))

  for (const item of items) {
    const idStr = String(getIdFn(item) ?? '')
    const sc = idToSuper.get(idStr) || otherKey
    buckets[sc] = buckets[sc] || []
    buckets[sc].push(item)
  }

  return { order, buckets }
}

const ItemCard = React.memo(function ItemCard({ item, isTag = false }) {
  const { t } = useTranslation()
  const idKey = getId(item)
  const labelKey = categories[idKey]?.name

  const prefix = isTag ? '$' : '#'
  const mainLink = isTag ? `/tag/${encodeURIComponent(idKey)}` : `/category/${encodeURIComponent(idKey)}`
  const galleryQuery = `/gallery?s=${encodeURIComponent(prefix + idKey)}`
  const authorsQuery = `/authors?s=${encodeURIComponent(prefix + idKey)}`

  return (
    <div className="bg-gray-100 rounded-sm shadow-lg px-2 py-1 truncate">
      <div>
        <Link
          to={mainLink}
          className="flex items-center transition duration-200 cursor-pointer font-semibold text-sky-700 hover:text-sky-500"
        >
          <CategoryIcon category={idKey} />
          <span className="relative font-semibold -top-px truncate">
            &nbsp;{isTag ? idKey : `P${idKey}`}
            {labelKey && (
              <>
                &nbsp;&ndash;&nbsp;{t(labelKey)}
              </>
            )}
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
            />,
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
            />,
          ]}
        />
      </span>
    </div>
  )
})

function Section({ titleKey, children }) {
  const { t } = useTranslation()
  return (
    <section>
      <h2 className="font-light text-gray-600">{t(titleKey)}</h2>
      <hr className="border-1 border-t border-gray-500 mb-2" />
      {children}
    </section>
  )
}

function useCategoriesAndTags() {
  const [categoriesData, setCategories] = useState([])
  const [tagsData, setTags] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const ac = new AbortController()
    const params = window.location.search

    let mounted = true
    setLoading(true)
    setError(null)

    ;(async () => {
      try {
        const [catsRes, tagsRes] = await Promise.all([
          fetch(`/api/categories${params}`, { signal: ac.signal }),
          fetch(`/api/tags${params}`, { signal: ac.signal }),
        ])

        if (!catsRes.ok || !tagsRes.ok) {
          throw new Error(`Fetch failed: ${catsRes.status} / ${tagsRes.status}`)
        }

        const [cats, tgs] = await Promise.all([catsRes.json(), tagsRes.json()])
        if (!mounted) return
        setCategories(cats || [])
        setTags(tgs || [])
      } catch (err) {
        if (err.name === 'AbortError') return
        console.error(err)
        if (mounted) setError('Could not load categories or tags.')
      } finally {
        if (mounted) setLoading(false)
      }
    })()

    return () => {
      mounted = false
      ac.abort()
    }
  }, [])

  return { categoriesData, tagsData, loading, error }
}

export default function CategoriesList() {
  const { t } = useTranslation()
  const { categoriesData, tagsData, loading, error } = useCategoriesAndTags()

  const groupedCategories = useMemo(
    () => groupBySupercategories(categoriesData, SUPER_CATEGORIES, OTHER_KEY, (it) => String(it.category)),
    [categoriesData]
  )

  const { modulesItems, contestItems, automaticItems, otherTagItems } = useMemo(() => {
    const byId = (list, ids) => list.filter((x) => ids.includes(getId(x)))

    const modules = byId(tagsData, TAG_TABS.modules.ids)
    const contests = byId(tagsData, TAG_TABS.contests.ids)
    const automatic = byId(tagsData, TAG_TABS.automatic.ids)

    const knownIds = new Set([
      ...TAG_TABS.modules.ids,
      ...TAG_TABS.contests.ids,
      ...TAG_TABS.automatic.ids,
    ].map(String))

    const other = tagsData.filter((t) => !knownIds.has(getId(t)))

    return {
      modulesItems: modules,
      contestItems: contests,
      automaticItems: automatic,
      otherTagItems: other,
    }
  }, [tagsData])

  const TAB_DEFS = useMemo(
    () => [
      { key: 'categories', label: 'categorytabs.categories' },
      { key: 'modules', label: TAG_TABS.modules.titleKey },
      { key: 'contests', label: TAG_TABS.contests.titleKey },
      { key: 'automatic', label: TAG_TABS.automatic.titleKey },
      { key: 'other', label: 'categorytabs.other_tags' },
    ],
    []
  )

  const getTabFromUrl = useCallback(() => {
    try {
      const sp = new URLSearchParams(window.location.search)
      return sp.get('tab') || 'categories'
    } catch (e) {
      return 'categories'
    }
  }, [])

  const [activeTab, setActiveTabState] = useState(() => getTabFromUrl())

  const setActiveTab = (tab) => {
    setActiveTabState(tab)
    try {
      const sp = new URLSearchParams(window.location.search)
      sp.set('tab', tab)
      const newUrl = window.location.pathname + (sp.toString() ? `?${sp.toString()}` : '')
      window.history.replaceState(null, '', newUrl)
    } catch (e) {
      // ignore
    }
  }

  useEffect(() => {
    const onPop = () => setActiveTabState(getTabFromUrl())
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [getTabFromUrl])

  if (loading) return <p>Loading...</p>
  if (error) return <p>{error}</p>

  const renderGrid = (items, isTag = false) =>
    items.length === 0 ? (
      <p className="text-sm text-gray-600">{t('categorytabs.no_items')}</p>
    ) : (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {items.map((it) => (
          <ItemCard key={getId(it)} item={it} isTag={isTag} />
        ))}
      </div>
    )

  return (
    <>
      <title>{t('categories_list.title')}</title>

      <div className="sticky top-0 z-10">
        <div className="flex gap-2 overflow-auto pb-2 justify-center">
          {TAB_DEFS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              aria-pressed={activeTab === tab.key}
              className={clsx(
                'px-3 py-1 rounded-md text-sm font-medium transition duration-200 cursor-pointer',
                activeTab === tab.key
                  ? 'bg-emerald-600 text-white hover:bg-emerald-500'
                  : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
              )}
            >
              {t(tab.label)}
            </button>
          ))}
        </div>

        <Searchbar placeholder={t('categories_list.search_placeholder')} />
      </div>

      <div className="space-y-3 mt-3">
        {activeTab === 'categories' && (
          <>
            {groupedCategories.order.map((scKey) => {
              const items = groupedCategories.buckets[scKey] || []
              if (!items.length) return null

              return (
                <Section key={scKey} titleKey={scKey}>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {items.map((cat) => (
                      <ItemCard key={String(cat.category ?? getId(cat))} item={cat} />
                    ))}
                  </div>
                </Section>
              )
            })}
          </>
        )}

        {activeTab === 'modules' && (
          <Section titleKey={TAG_TABS.modules.titleKey}>{renderGrid(modulesItems, true)}</Section>
        )}

        {activeTab === 'contests' && (
          <Section titleKey={TAG_TABS.contests.titleKey}>{renderGrid(contestItems, true)}</Section>
        )}

        {activeTab === 'automatic' && (
          <Section titleKey={TAG_TABS.automatic.titleKey}>{renderGrid(automaticItems, true)}</Section>
        )}

        {activeTab === 'other' && (
          <Section titleKey={'categorytabs.other_tags'}>{renderGrid(otherTagItems, true)}</Section>
        )}
      </div>
    </>
  )
}
