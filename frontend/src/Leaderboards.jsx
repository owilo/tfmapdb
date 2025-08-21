import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import './style/main.css'
import Searchbar from './Searchbar'
import CategoryIcon from './CategoryIcon'
import categories from './assets/categories.json'
import { Trans, useTranslation } from 'react-i18next';
import clsx from 'clsx'
import { List } from 'lucide-react';

function getPositionColorClass(position) {
  switch (position) {
    case 0:
      return "text-[#e3a90b]";
    case 1:
      return "text-[#909090]";
    case 2:
      return "text-[#87511f]";
    default:
      return "text-gray-800";
  }
}

function LeaderboardEntry({ header, leaderboard, key }) {
  return <>
    <div
      key={key}
      className='w-full bg-gray-200 rounded-sm shadow-lg px-2 py-1 truncate'
    >
      <div>
        {header}
        <hr className="border-1 border-t border-gray-400" />
      </div>
      <div>
        {leaderboard.map((playerTies, position) => (
          playerTies.map(playerData => (
            <div
              key={playerData.name}
              role="listitem"
              className="flex items-center px-1 odd:bg-zinc-200 even:bg-zinc-300"
            >
              <span
                className={`min-w-8 shrink-0 font-semibold ${getPositionColorClass(position)}`}
                aria-hidden
              >
                {position + 1}.
              </span>

              <div className='flex-1 font-semibold text-sky-900 hover:text-sky-700 transition duration-200 truncate'>
                <Link to={`/author/${encodeURIComponent(playerData.name)}`}>{playerData.name}</Link>
              </div>

              <span className="ml-4 font-medium tabular-nums">
                {playerData.count}
              </span>
            </div>
          ))
        ))}
      </div>
    </div>
  </>
}

export default function Gallery() {
  const { t } = useTranslation();
  const [leaderboards, setLeaderboards] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const params = window.location.search;
    fetch(`/api/leaderboards${params}`)
      .then(res => {
        if (!res.ok) throw new Error(`Status ${res.status}`)
        return res.json()
      })
      .then(data => {
        setLeaderboards(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setError('Could not load leaderboard.')
        setLoading(false)
      })
  }, [])

  if (loading) return <p>Loading...</p>
  if (error) return <p>{error}</p>

  const categoryLeaderboards = Object.entries(leaderboards).filter(([key]) => Number.isInteger(Number(key)));

  return (
    <>
      <title>{t("leaderboards.title")}</title>
      {/*<div className="sticky top-0 z-10">
        <Searchbar placeholder={t("gallery.search_placeholder")} />
      </div>*/}
      <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 place-items-start'>
        {categoryLeaderboards.map(([key, leaderboard]) => (
          <LeaderboardEntry
            key={key}
            header={
              <Link
                to={`/category/${key}`}
                className="flex items-center transition duration-200 cursor-pointer font-semibold text-sky-900 hover:text-sky-700"
              >
                <CategoryIcon category={key} />
                <span className='relative font-semibold -top-px truncate'>
                  &nbsp;P{key} &ndash; {t(categories[key]?.name || categories.default.name)}
                </span>
              </Link>
            }
            leaderboard={leaderboard}
          />
        ))}

        <LeaderboardEntry
          key="high_perms"
          header={
            <div className="flex items-center">
              <List className='inline-block' size='1em' />
              &nbsp;
              <span className='relative font-semibold -top-px truncate'>
                {t("leaderboards.high_perms")}
              </span>
            </div>
          }
          leaderboard={leaderboards.all} />

        <LeaderboardEntry
          key="category"
          header={
            <div className="flex items-center">
              <List className='inline-block' size='1em' />
              &nbsp;
              <span className='relative font-semibold -top-px truncate'>
                {t("leaderboards.category")}
              </span>
            </div>
          }
          leaderboard={leaderboards.cat} />

        <LeaderboardEntry
          key="exported"
          header={
            <div className="flex items-center">
              <List className='inline-block' size='1em' />
              &nbsp;
              <span className='relative font-semibold -top-px truncate'>
                {t("leaderboards.exported")}
              </span>
            </div>
          }
          leaderboard={leaderboards.total} />
      </div>
    </>
  )
}