export function consumeAdminHandoff(location, history) {
  const params = new URLSearchParams((location.hash || '').replace(/^#/, ''))
  const token = params.get('session')
  if (token) history.replaceState(null, '', `${location.pathname}${location.search}`)
  return token
}
