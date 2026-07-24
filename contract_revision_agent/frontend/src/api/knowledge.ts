export async function uploadKbFile(file: File) {
  const form = new FormData()
  form.append('file', file)
  const resp = await fetch('/api/kb/upload', { method: 'POST', body: form })
  return await resp.json()
}

export async function processDocument(filepath: string, chunkSize = 500) {
  const resp = await fetch('/api/kb/process', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filepath, chunk_size: chunkSize }),
  })
  return await resp.json()
}

export async function searchKnowledge(query: string, topK = 5) {
  const resp = await fetch(`/api/kb/search?q=${encodeURIComponent(query)}&top_k=${topK}`)
  return await resp.json()
}

export async function getKbStatus() {
  const resp = await fetch('/api/kb/status')
  return await resp.json()
}

export async function deleteKbEntries(ids: string[]) {
  const resp = await fetch('/api/kb/entries', {
    method: 'DELETE', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids }),
  })
  return await resp.json()
}
