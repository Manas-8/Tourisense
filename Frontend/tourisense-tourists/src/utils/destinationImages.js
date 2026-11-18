export const DESTINATION_IMAGE_FALLBACK = '/images/destination-fallback.svg'

export function normalizeDestinationImageKey(value) {
  return String(value || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
    .replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

export function destinationImagePath(name, manifest = {}) {
  return manifest[normalizeDestinationImageKey(name)] || DESTINATION_IMAGE_FALLBACK
}

export function estimatedTemperatureBand(temperature) {
  if (!temperature || !Array.isArray(temperature.range) || temperature.range.length < 2) return null
  const reference = Array.isArray(temperature.reference_range) && temperature.reference_range.length >= 2
    ? temperature.reference_range
    : temperature.range
  const low = Number(reference[0])
  const high = Number(reference[1])
  const adjustment = Number(temperature.monthly_adjustment || 0)
  if (![low, high, adjustment].every(Number.isFinite)) return null

  // Keep the displayed span narrow and centered on the selected month's estimate.
  const center = (low + high) / 2 + adjustment
  const min = Math.round((center - 1.5) * 10) / 10
  const max = Math.round((center + 1.5) * 10) / 10
  return [min, max]
}
