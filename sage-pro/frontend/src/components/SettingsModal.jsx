import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'

export default function SettingsModal({ open, onClose }) {
  const [epsilon, setEpsilon] = useState(0.05)
  const [maxCycles, setMaxCycles] = useState(5)

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 10 }}
            transition={{ type: 'spring', damping: 30, stiffness: 400 }}
            className="fixed inset-0 flex items-center justify-center z-50 pointer-events-none"
          >
            <div className="bg-white rounded-2xl border border-[var(--color-border)] shadow-2xl w-[520px] max-h-[80vh] overflow-y-auto pointer-events-auto">
              {/* Header */}
              <div className="px-7 py-5 border-b border-[var(--color-border-light)] flex items-center justify-between">
                <h2 className="text-lg font-semibold text-[var(--color-ink)]">Settings & Benchmarks</h2>
                <button onClick={onClose} className="p-1.5 rounded-md hover:bg-gray-50 text-[var(--color-ink-muted)] transition-colors">
                  <X size={18} />
                </button>
              </div>

              <div className="px-7 py-6 space-y-8">
                {/* Benchmarks */}
                <div>
                  <h3 className="text-xs font-semibold uppercase tracking-widest text-[var(--color-ink-muted)] mb-5">Performance</h3>
                  <div className="grid grid-cols-3 gap-6">
                    {[
                      { label: 'HumanEval', value: '94.2%' },
                      { label: 'SWE-Bench', value: '71.8%' },
                      { label: 'LiveCodeBench', value: '86.4%' },
                    ].map(m => (
                      <div key={m.label} className="text-center">
                        <p className="text-3xl font-bold tracking-tight text-[var(--color-ink)]">{m.value}</p>
                        <p className="text-xs text-[var(--color-ink-muted)] mt-1">{m.label}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="h-px bg-[var(--color-border-light)]" />

                {/* Hyperparameters */}
                <div>
                  <h3 className="text-xs font-semibold uppercase tracking-widest text-[var(--color-ink-muted)] mb-5">Hyperparameters</h3>

                  <div className="space-y-6">
                    <div>
                      <div className="flex justify-between mb-2">
                        <label className="text-sm font-medium text-[var(--color-ink-secondary)]">Nash Epsilon</label>
                        <span className="text-sm font-mono text-[var(--color-ink-muted)]">{epsilon.toFixed(2)}</span>
                      </div>
                      <input
                        type="range"
                        min="0.01"
                        max="0.20"
                        step="0.01"
                        value={epsilon}
                        onChange={e => setEpsilon(parseFloat(e.target.value))}
                        className="w-full h-1.5 rounded-full bg-gray-200 appearance-none cursor-pointer accent-orange-600"
                      />
                      <p className="text-[11px] text-[var(--color-ink-muted)] mt-1">Convergence threshold for Nash Equilibrium</p>
                    </div>

                    <div>
                      <div className="flex justify-between mb-2">
                        <label className="text-sm font-medium text-[var(--color-ink-secondary)]">Max Crucible Cycles</label>
                        <span className="text-sm font-mono text-[var(--color-ink-muted)]">{maxCycles}</span>
                      </div>
                      <input
                        type="range"
                        min="1"
                        max="10"
                        step="1"
                        value={maxCycles}
                        onChange={e => setMaxCycles(parseInt(e.target.value))}
                        className="w-full h-1.5 rounded-full bg-gray-200 appearance-none cursor-pointer accent-orange-600"
                      />
                      <p className="text-[11px] text-[var(--color-ink-muted)] mt-1">Maximum adversarial refinement iterations</p>
                    </div>
                  </div>
                </div>

                <div className="h-px bg-[var(--color-border-light)]" />

                {/* Model Info */}
                <div>
                  <h3 className="text-xs font-semibold uppercase tracking-widest text-[var(--color-ink-muted)] mb-4">Active Ensemble</h3>
                  <div className="space-y-2.5">
                    {[
                      { role: 'Architect', model: 'Qwen2.5-Coder-32B-AWQ' },
                      { role: 'Implementer', model: 'Meta-Llama-3.1-70B-AWQ' },
                      { role: 'Synthesizer', model: 'Mistral-Large-123B-AWQ' },
                      { role: 'Red Team', model: 'DeepSeek-Coder-V2-Lite' },
                    ].map(m => (
                      <div key={m.role} className="flex items-center justify-between py-1.5">
                        <span className="text-sm text-[var(--color-ink-secondary)]">{m.role}</span>
                        <span className="text-xs font-mono text-[var(--color-ink-muted)] bg-gray-50 px-2.5 py-1 rounded-md">{m.model}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
