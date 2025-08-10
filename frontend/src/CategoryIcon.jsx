import categories from './assets/categories.json'

export default function CategoryIcon({ categoryId }) {
  const iconPath = `/src/assets/category_icons/${categories[categories[categoryId] ? categoryId : "default"].image}.webp`;

  return (
    <img
      src={iconPath}
      alt={categoryId}
      className='h-[1em] align-middle select-none'
    />
  );
}