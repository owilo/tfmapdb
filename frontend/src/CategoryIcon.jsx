import categories from './assets/categories.json'

export default function CategoryIcon({ category, className = '', ...props }) {
  const iconName = categories[categories[category] ? category : 'default'].image;
  const iconPath = `/src/assets/tag_icons/${iconName}`;

  return (
    <img
      src={iconPath}
      alt={category}
      className={`inline-block align-middle h-[1em] w-auto select-none ${className}`}
      {...props}
    />
  );
}