import { X, ChevronDown } from 'lucide-react'
import { motion } from 'framer-motion'

const MOCK_LOGS = [
  { type: 'info', text: '[sandbox] Initializing isolated environment...' },
  { type: 'info', text: '[sandbox] Python 3.10.12, Ruff 0.7.0, Mypy 1.12.0' },
  { type: 'info', text: '[ruff] Running linter on lru_cache.py...' },
  { type: 'pass', text: '[ruff] 0 violations found' },
  { type: 'info', text: '[mypy] Running type checker...' },
  { type: 'pass', text: '[mypy] Success: no issues found in 1 source file' },
  { type: 'info', text: '[pytest] Running 24 adversarial tests...' },
  { type: 'pass', text: '[pytest] test_basic_set_get PASSED' },
  { type: 'pass', text: '[pytest] test_ttl_expiry PASSED' },
  { type: 'pass', text: '[pytest] test_lru_eviction_order PASSED' },
  { type: 'pass', text: '[pytest] test_concurrent_access PASSED' },
  { type: 'pass', text: '[pytest] test_negative_ttl_raises PASSED' },
  { type: 'pass', text: '[pytest] test_zero_capacity_raises PASSED' },
  { type: 'fail', text: '[pytest] test_overflow_stress FAILED (Cycle 1 — patched in Cycle 2)' },
  { type: 'pass', text: '[pytest] test_overflow_stress PASSED (Cycle 2)' },
  { type: 'info', text: '[pytest] 24/24 passed. Execution time: 0.342s' },
  { type: 'info', text: '[bandit] Security scan complete. 0 issues.' },
  { type: 'info', text: '[sandbox] Session complete. Artifacts emitted.' },
]

export default function SandboxTerminal({ onClose }) {
  return (
    <motion.div
      initial={{ height: 0 }}
      animate={{ height: 280 }}
      exit={{ height: 0 }}
      className="border-t border-[var(--color-border)] bg-[#0a0a0a] overflow-hidden flex flex-col"
    >
      <div className="flex items-center justify-between px-4 py-2 bg-[#111] border-b border-gray-800">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500 opacity-70" />
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500 opacity-70" />
          <div className="w-2.5 h-2.5 rounded-full bg-green-500 opacity-70" />
          <span className="ml-2 text-[11px] font-mono text-gray-500">sandbox — sage-pro</span>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={onClose} className="p-1 text-gray-500 hover:text-gray-300 transition-colors">
            <ChevronDown size={14} />
          </button>
          <button onClick={onClose} className="p-1 text-gray-500 hover:text-gray-300 transition-colors">
            <X size={14} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 font-mono text-[12px] leading-[1.8]">
        {MOCK_LOGS.map((log, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.04 }}
            className={
              log.type === 'pass' ? 'text-green-500/80' :
              log.type === 'fail' ? 'text-red-400/80' :
              'text-gray-500'
            }
          >
            {log.text}
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}
