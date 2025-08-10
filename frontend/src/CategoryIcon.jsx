export default function CategoryIcon({ categoryId }) {
  const defaultIcon = '/src/assets/category_icons/default.webp';
  const iconPath = `/src/assets/category_icons/${categoryId}.webp`;

  return (
    <img
      src={iconPath}
      alt={categoryId}
      className='h-[1em] align-middle select-none'
      onError={(e) => { e.target.src = defaultIcon; }}
    />
  );
}