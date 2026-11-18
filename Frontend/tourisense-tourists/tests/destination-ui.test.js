import test from 'node:test'
import assert from 'node:assert/strict'
import { access, readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { DESTINATION_IMAGE_FALLBACK, destinationImagePath, estimatedTemperatureBand, normalizeDestinationImageKey } from '../src/utils/destinationImages.js'
import { cityMapSearchUrl } from '../src/utils/mapLinks.js'
import { buildGovernmentHandoffUrl } from '../src/services/authService.js'

test('local image matching uses normalized existing mapping and a local fallback', async () => {
  assert.equal(normalizeDestinationImageKey('Taj Mahal, Agra'), 'taj-mahal-agra')
  assert.equal(destinationImagePath('Taj Mahal', { 'taj-mahal': '/images/taj-mahal.webp' }), '/images/taj-mahal.webp')
  assert.equal(destinationImagePath('Unknown City', {}), DESTINATION_IMAGE_FALLBACK)
  await access(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../public', DESTINATION_IMAGE_FALLBACK.slice(1)))
  const manifest = JSON.parse(await readFile(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../public/images/destination-manifest.json'), 'utf8'))
  assert.equal(destinationImagePath('Mussoorie', manifest), '/images/masoorie.jpg')
  assert.equal(destinationImagePath('Leh Ladakh', manifest), '/images/leh%20ladakha.jpg')
  for (const imagePath of Object.values(manifest)) {
    await access(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../public', imagePath.slice(1).replaceAll('%20', ' ')))
  }
})

test('monthly temperature display stays within a centered three degree band, including below zero', () => {
  const winter = estimatedTemperatureBand({ reference_range: [5, 15], monthly_adjustment: -12, range: [-7, 3] })
  const summer = estimatedTemperatureBand({ reference_range: [5, 15], monthly_adjustment: 8, range: [13, 23] })
  assert.deepEqual(winter, [-3.5, -0.5])
  assert.deepEqual(summer, [16.5, 19.5])
  assert.ok(winter[1] - winter[0] <= 3)
  assert.ok(summer[1] - summer[0] <= 3)
  assert.equal(estimatedTemperatureBand({ range: null }), null)
})

test('map action opens a location search and never invents coordinates', () => {
  const url = cityMapSearchUrl('Manali, Himachal Pradesh, India')
  assert.match(url, /^https:\/\/www\.openstreetmap\.org\/search\?query=/)
  assert.match(decodeURIComponent(url), /Manali/)
  assert.equal(cityMapSearchUrl(''), '')
})

test('admin login creates a one-time route handoff carrying only an authenticated session token', () => {
  const url = new URL(buildGovernmentHandoffUrl('http://localhost:5174', 'jwt-example'))
  assert.equal(url.pathname, '/government/dashboard')
  assert.equal(new URLSearchParams(url.hash.slice(1)).get('session'), 'jwt-example')
  assert.throws(() => buildGovernmentHandoffUrl('http://localhost:5174', ''), /token is required/)
  assert.equal(new URL(buildGovernmentHandoffUrl('https://example.test/portal', 'token')).pathname, '/portal/government/dashboard')
})
