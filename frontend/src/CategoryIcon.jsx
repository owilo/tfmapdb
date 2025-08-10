import categories from './assets/categories.json'

export default function CategoryIcon({ category }) {
  const iconPath = `/src/assets/category_icons/${categories[categories[category] ? category : "default"].image}.webp`;

  return (
    <img
      src={iconPath}
      alt={category}
      className='h-[1em] align-middle select-none'
    />
  );
}