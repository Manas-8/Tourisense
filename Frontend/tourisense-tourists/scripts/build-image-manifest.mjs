import { readFile, readdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const imageDir = path.join(root, 'public', 'images')
const catalogPath = path.resolve(root, '..', '..', 'Backend', 'Data', 'tourism_statistics.csv')
const allowed = new Set(['.jpg', '.jpeg', '.png', '.webp', '.avif', '.svg'])
const keyOf = value => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
  .replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
const filenameAliases = new Map([
  ['mussoorie', 'masoorie'],
  ['leh-ladakh', 'leh-ladakha'],
  ['vrindavan', 'vrindawan'],
])
async function listFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true })
  const files = []
  for (const entry of entries) {
    const full = path.join(directory, entry.name)
    if (entry.isDirectory()) files.push(...await listFiles(full))
    else if (entry.isFile()) files.push(full)
  }
  return files
}

function parseCsvLine(line) {
  const cells = []
  let cell = ''
  let quoted = false
  for (let index = 0; index < line.length; index += 1) {
    const character = line[index]
    if (character === '"' && line[index + 1] === '"' && quoted) { cell += '"'; index += 1 }
    else if (character === '"') quoted = !quoted
    else if (character === ',' && !quoted) { cells.push(cell); cell = '' }
    else cell += character
  }
  cells.push(cell)
  return cells
}

const catalogText = await readFile(catalogPath, 'utf8')
const catalogLines = catalogText.replace(/^\uFEFF/, '').split(/\r?\n/).filter(Boolean)
const headers = parseCsvLine(catalogLines.shift()).map(header => header.trim().toLowerCase())
const destinationColumn = headers.indexOf('destination')
if (destinationColumn < 0) throw new Error(`Destination column is missing from ${catalogPath}`)
const catalogNames = [...new Set(catalogLines.map(line => parseCsvLine(line)[destinationColumn]?.trim()).filter(Boolean))]
const filesByKey = new Map()
for (const file of (await listFiles(imageDir)).sort()) {
  const name = path.basename(file)
  const ext = path.extname(name).toLowerCase()
  if (!allowed.has(ext) || name === 'destination-fallback.svg') continue
  const key = keyOf(path.basename(name, ext))
  const relative = path.relative(imageDir, file).split(path.sep).map(encodeURIComponent).join('/')
  if (key && !filesByKey.has(key)) filesByKey.set(key, `/images/${relative}`)
}
const manifest = {}
for (const destination of catalogNames) {
  const key = keyOf(destination)
  const imageKey = filenameAliases.get(key) || key
  if (filesByKey.has(imageKey)) manifest[key] = filesByKey.get(imageKey)
}
await writeFile(path.join(imageDir, 'destination-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)
console.log(`Destination image manifest: ${Object.keys(manifest).length} of ${catalogNames.length} catalog destinations mapped.`)
