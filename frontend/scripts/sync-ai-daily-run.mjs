/**
 * Cross-platform runner for backend/scripts/sync_ai_daily.py (requires Python + git).
 */
import { spawnSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(__dirname, '..', '..')
const script = path.join(repoRoot, 'backend', 'scripts', 'sync_ai_daily.py')

const candidates = ['python3', 'python', 'py']
for (const py of candidates) {
  const r = spawnSync(py, [script], { cwd: repoRoot, stdio: 'inherit' })
  if (r.status === 0) {
    process.exit(0)
  }
  if (r.error && 'code' in r.error && r.error.code !== 'ENOENT') {
    process.exit(r.status ?? 1)
  }
}
console.error('[sync-ai-daily] No working Python interpreter found (tried: python3, python, py)')
process.exit(1)
