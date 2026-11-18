export function cityMapSearchUrl(label) {
  const query = String(label || '').trim()
  if (!query) return ''
  return `https://www.openstreetmap.org/search?query=${encodeURIComponent(query)}`
}
