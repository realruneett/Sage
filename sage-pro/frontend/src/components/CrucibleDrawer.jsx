import { motion, AnimatePresence } from 'framer-motion'
import { X, Compass, Code2, Shield, Merge } from 'lucide-react'

const AGENT_META = {
  route: { icon: Compass, label: 'Router', color: 'text-gray-500' },
  arch: { icon: Compass, label: 'Architect', color: 'text-blue-600' },
  impl: { icon: Code2, label: 'Implementer', color: 'text-violet-600' },
  red: { icon: Shield, label: 'Red Team', color: 'text-red-500' },
  synth: { icon: Merge, label: 'Synthesizer', color: 'text-emerald-600' },
  emit: { icon: Code2, label: 'Emitter', color: 'text-orange-600' },
}

function formatTrace(text) {
  let html = text
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-[12px] font-mono">$1</code>')
  html = html.replace(/\n/g, '<br/>')
  return html
}

export default function CrucibleDrawer({ open, trace, onClose }) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/10 z-40"
          />
          <motion.aside
            initial={{ x: 420 }}
            animate={{ x: 0 }}
            exit={{ x: 420 }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 w-[400px] bg-white border-l border-[var(--color-border)] z-50 flex flex-col shadow-xl"
          >
            <div className="px-5 py-4 border-b border-[var(--color-border-light)] flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-[var(--color-ink)]">AODE Reasoning Trace</h3>
                <p className="text-[11px] text-[var(--color-ink-muted)] mt-0.5">Adversarial Orthogonal Divergence Engine</p>
              </div>
              <button onClick={onClose} className="p-1.5 rounded-md hover:bg-gray-50 text-[var(--color-ink-muted)] transition-colors">
                <X size={16} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-4">
              {trace && trace.map((step, i) => {
                const meta = AGENT_META[step.id] || AGENT_META.route
                const Icon = meta.icon
                return (
                  <motion.div
                    key={step.id}
                    initial={{ opacity: 0, x: 12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.08 }}
                    className="relative pl-7 pb-6 last:pb-0"
                  >
                    {/* Timeline line */}
                    {i < trace.length - 1 && (
                      <div className="absolute left-[11px] top-6 bottom-0 w-px bg-[var(--color-border)]" />
                    )}

                    {/* Icon dot */}
                    <div className={`absolute left-0 top-0.5 w-6 h-6 rounded-full bg-white border border-[var(--color-border)] flex items-center justify-center ${meta.color}`}>
                      <Icon size={12} />
                    </div>

                    {/* Content */}
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs font-semibold ${meta.color}`}>{meta.label}</span>
                        <span className="text-[10px] font-mono text-[var(--color-ink-muted)]">{step.time}</span>
                      </div>
                      <div
                        className="text-[13px] leading-relaxed text-gray-600"
                        dangerouslySetInnerHTML={{ __html: formatTrace(step.output) }}
                      />
                    </div>
                  </motion.div>
                )
              })}
              {!trace && (
                <p className="text-sm text-[var(--color-ink-muted)] text-center py-12">No trace data available</p>
              )}
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}
