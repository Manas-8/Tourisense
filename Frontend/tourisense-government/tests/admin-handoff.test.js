import test from 'node:test'
import assert from 'node:assert/strict'
import { consumeAdminHandoff } from '../src/services/adminHandoff.js'

test('government app consumes and removes the URL fragment session handoff', () => {
  let replaced = ''
  const location = { hash: '#session=admin-token', pathname: '/government/dashboard', search: '?view=main' }
  const history = { replaceState: (_state, _title, url) => { replaced = url } }
  assert.equal(consumeAdminHandoff(location, history), 'admin-token')
  assert.equal(replaced, '/government/dashboard?view=main')
})

test('a route with no handoff does not create a session', () => {
  let called = false
  assert.equal(consumeAdminHandoff({ hash: '', pathname: '/', search: '' }, { replaceState: () => { called = true } }), null)
  assert.equal(called, false)
})
