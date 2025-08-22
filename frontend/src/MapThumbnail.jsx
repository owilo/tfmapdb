import { Link } from 'react-router-dom'
import './style/main.css'
import CategoryIcon from './CategoryIcon'
import categories from './assets/categories.json'
import { Trans, useTranslation } from 'react-i18next';
import clsx from 'clsx';

export default function MapThumbnail({ code, category, author = undefined }) {
  const { t } = useTranslation();

  return <div
    className={clsx("bg-gray-200 rounded-sm shadow-lg px-2 py-1 truncate", author || "pb-2")}
  >
    <div className="flex justify-between items-center">
      <Link
        to={`/map/${code}`}
        className="font-semibold text-sky-700 hover:text-sky-500 transition duration-200"
      >
        @{code}
      </Link>
      <Link
        to={`/category/${category}`}
        className="font-semibold text-gray-700 text-xs flex items-center gap-1 bg-gray-400 rounded-sm px-1 hover:brightness-110 transition duration-200 cursor-pointer"
        title={t(categories[category]?.name || categories.default.name)}
      >
        <CategoryIcon category={category} />
        <span>P{category}</span>
      </Link>
    </div>

    <Link to={`/map/${code}`}>
      <img src={`/api/map/${code}/image.png`} alt="Map" className='w-full rounded-sm hover:brightness-110 transition duration-200' loading="lazy" />
    </Link>

    {author &&
      <div className="text-sm text-gray-600">
        <Trans
          i18nKey="gallery.by_user"
          values={{ user: author }}
          components={[
            <Link
              to={`/author/${encodeURIComponent(author)}`}
              className="font-semibold text-sky-900 hover:text-sky-700 transition duration-200"
            />
          ]}
        />
      </div>
    }
  </div>
}