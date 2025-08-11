import tags from './assets/tags.json'

export default function TagIcon({ tag, className = '', ...props }) {
  const iconName = tags[tags[tag] ? tag : 'default'].image;
  const iconPath = `/src/assets/tag_icons/${iconName}.webp`;

  return (
    <img
      src={iconPath}
      alt={tag}
      className={`inline-block align-middle h-[1em] w-auto select-none ${className}`}
      {...props}
    />
  );
}