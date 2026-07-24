export async function uploadFile(file: File): Promise<{ success: boolean; filename?: string; path?: string; error?: string }> {
  const form = new FormData()
  form.append('file', file)
  const resp = await fetch('/api/upload', { method: 'POST', body: form })
  return await resp.json()
}

export async function startRevision(filepath: string): Promise<{ success: boolean; task_id?: string }> {
  const resp = await fetch('/api/contract/revise', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filepath }),
  })
  return await resp.json()
}

export async function getRevisionStatus(taskId: string): Promise<{ status: string; result?: string; error?: string }> {
  const resp = await fetch(`/api/contract/status/${taskId}`)
  return await resp.json()
}
