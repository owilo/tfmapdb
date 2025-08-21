import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Image, BookOpen, Settings, ListCollapse } from "lucide-react";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "./components/ui/collapsible";
import './style/main.css'
import './style/animations.css'
import XMLViewer from './XMLViewer';
import clsx from 'clsx';
import CategoryIcon from './CategoryIcon';
import categories from './assets/categories.json';
import { useTranslation } from 'react-i18next';

function CollapsibleSection({
  icon: Icon,
  title,
  children,
  defaultOpen = true,
  triggerClassName,
  contentClassName,
}) {
  const baseTrigger =
    'flex items-center space-x-2 px-2 py-1 w-full text-start ' +
    'bg-gray-300 text-gray-800 rounded-t-sm rounded-b-sm ' +
    'data-[state=open]:rounded-b-none hover:brightness-105 transition duration-200';

  const baseContent =
    'bg-gray-100 text-gray-800 overflow-hidden transition-all ' +
    'data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down ' +
    'rounded-b-sm';

  return (
    <Collapsible defaultOpen={defaultOpen}>
      <CollapsibleTrigger className={clsx(baseTrigger, triggerClassName)}>
        {Icon && <Icon size="1.25em" />}
        <span className="relative -top-px">{title}</span>
      </CollapsibleTrigger>

      <CollapsibleContent className={clsx(baseContent, contentClassName)}>
        {children}
      </CollapsibleContent>
    </Collapsible>
  );
}


export default function MapDetail() {
  const { t } = useTranslation();
  const { code } = useParams()
  const [map, setMap] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`/api/map/${code}/`)
      .then(res => {
        if (!res.ok) throw new Error(`Status ${res.status}`)
        return res.json()
      })
      .then(data => {
        setMap(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setError('Could not load map detail.')
        setLoading(false)
      })
  }, [code])

  if (loading) return <p>Loading…</p>
  if (error)   return <p style={{ color: 'red' }}>{error}</p>

  return (
    <>
      <title>{`@${map.code}`}</title>
      <meta name="author" content={map.author.name} />
      <div className="flex flex-col h-full bg-gray-200 rounded-lg shadow-lg overflow-hidden">
        <div className="relative bg-gray-300 text-gray-900 font-bold text-lg p-1 rounded-lg shadow-lg">
          <Link
            to="/gallery"
            aria-label="Back to gallery"
            className="absolute top-1/2 transform -translate-y-1/2 left-1 bg-gray-400 flex items-center rounded-full p-1 text-gray-600 hover:brightness-110 transition duration-200"
          >
            <ArrowLeft className="w-3 h-3" />
            <span className='text-xs px-1'>{t("navigation.back_to_gallery")}</span>
          </Link>

          <h1 className="text-center font-semibold text-gray-800 text-xl">
            @{map.code}
          </h1>
        </div>

        <div className="flex flex-1 overflow-hidden">
          <div className="w-3/5 flex overflow-auto flex-col border-r border-neutral-300 p-2 space-y-2">
            <CollapsibleSection icon={Image} title={t("map.image")} defaultOpen>
              <img
                src={`/api/map/${map.code}/image.png`}
                alt="Map"
                loading="lazy"
                className="w-full object-contain bg-[#626b8a] max-h-[300px]"
              />
            </CollapsibleSection>

            <CollapsibleSection icon={BookOpen} title={t("map.details")} defaultOpen contentClassName="px-2 py-1">
              <ul>
                <li><span className='font-semibold'>{t("map.code")}</span>&nbsp;@{map.code}</li>
                <li>
                  <span className='font-semibold'>{t("map.author")}</span>&nbsp;
                  <Link
                    to={`/author/${encodeURIComponent(map.author.name)}`}
                    className='font-semibold text-sky-800 hover:text-sky-700 transition duration-200'
                  >
                    {map.author.name}
                  </Link>
                </li>
                <li className='flex items-center'>
                  <span className='font-semibold'>{t("map.category")}</span>&nbsp;
                  <Link
                    to={`/category/${map.category}`}
                    className="font-semibold text-gray-700 text-sm flex items-center gap-1 bg-gray-400 rounded-sm px-1 hover:brightness-110 transition duration-200 cursor-pointer"
                    title={t(categories[map.category]?.name || categories.default.name)}
                  >
                    <CategoryIcon category={map.category} />
                    <span>P{map.category}</span>
                  </Link>
                </li>
                {map.tags.length > 0 && <li className='flex items-center'>
                  <span className='font-semibold'>{t("map.tags")}</span>&nbsp;
                  {map.tags.map(tag => (
                    <Link
                      to={`/gallery/?s=%24${tag}`}
                      className="mr-1 font-semibold text-gray-700 text-sm flex items-center gap-1 bg-gray-400 rounded-sm px-1 hover:brightness-110 transition duration-200 cursor-pointer"
                      title={tag}
                    >
                      <CategoryIcon category={tag} />
                      <span>{t(categories[tag]?.name) || tag}</span>
                    </Link>
                  ))}
                </li>}
              </ul>
            </CollapsibleSection>

            <CollapsibleSection icon={Settings} title={t("map.properties")} defaultOpen contentClassName="px-2 py-1">
              <ul>
                <li><span className='font-semibold'>{t("map.dimensions")}</span>&nbsp;{map.map_data.length}×{map.map_data.height}</li>
              </ul>
            </CollapsibleSection>

            <CollapsibleSection icon={ListCollapse} title={t("map.content")} defaultOpen contentClassName="px-2 py-1">
              <ul>
                <li><span className='font-semibold'>{t("map.grounds_count")}</span>&nbsp;{map.map_data.grounds_count}/60</li>
                <li><span className='font-semibold'>{t("map.decorations_count")}</span>&nbsp;{map.map_data.decorations_count}/50</li>
                <li><span className='font-semibold'>{t("map.objects_count")}</span>&nbsp;{map.map_data.objects_count}/40</li>
                <li><span className='font-semibold'>{t("map.joints_count")}</span>&nbsp;{map.map_data.joints_count}</li>
              </ul>
            </CollapsibleSection>
          </div>

          <div className="w-2/5 overflow-auto p-2">
            <XMLViewer xml={map.xml} indentSize={2} />
          </div>
        </div>
      </div>
    </>
  )
}