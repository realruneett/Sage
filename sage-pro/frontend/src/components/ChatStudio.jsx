import { useState, useRef, useEffect } from 'react'
import { PanelLeftOpen, ArrowUp, Paperclip, Terminal, Sparkles } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const SUGGESTIONS = [
  { title: 'Thread-safe LRU Cache', desc: 'With TTL and async eviction', prompt: 'Build a thread-safe LRU cache with TTL and async eviction in Python' },
  { title: 'Token Bucket Rate Limiter', desc: 'Sliding window + Redis', prompt: 'Implement a token-bucket rate limiter with sliding window and Redis backend' },
  { title: 'WebSocket Broker', desc: 'Pub/sub with JWT auth', prompt: 'Create a WebSocket message broker with pub/sub channels and JWT authentication' },
  { title: 'Distributed Task Queue', desc: 'Retry logic + dead-letter', prompt: 'Build a distributed task queue with exponential retry and dead-letter handling' },
]

const PIPELINE = [
  { id: 'route', label: 'Topological Routing', ms: 1000 },
  { id: 'arch', label: 'Architect Agent', ms: 3000 },
  { id: 'impl', label: 'Parallel Implementation', ms: 4500 },
  { id: 'red', label: 'Red-Team Attack', ms: 3500 },
  { id: 'synth', label: 'Nash Crucible Synthesis', ms: 2500 },
  { id: 'emit', label: 'Emit Hardened Artifacts', ms: 600 },
]

const MOCK_OUTPUTS = [
  '**Topological Routing** complete. Persistent Homology: B1=2, B2=0. Routed to void: "Core data structures".',
  '**Architect** designed the solution:\n- Data Structures: `OrderedDict` + `threading.RLock` + `heapq`\n- API: `get()`, `set()`, `delete()`, `clear()`, `stats()`\n- Concurrency: ReentrantLock with condition variables for async eviction',
  '**Parallel branches** synthesized:\n- Branch ABC (Design-first): 127 lines, clean architecture\n- Branch ACB (Threat-first): 156 lines, defensive coding\n- Lie Bracket Divergence: **0.142**',
  '**Red-Team** found 3 vulnerabilities:\n1. Race condition in TTL eviction thread (CRITICAL)\n2. Integer overflow in cache size calculation (MEDIUM)\n3. Missing negative TTL validation (LOW)',
  '**Nash Crucible** converged in 2 cycles:\n- Cycle 1: Damage = 0.089\n- Cycle 2: Damage = 0.031 — **CONVERGED**\n\nAll 3 vulnerabilities patched.',
  '**Hardened artifact** emitted:\n\n```python\nimport threading\nimport time\nfrom collections import OrderedDict\nfrom typing import Any, Optional\n\nclass ThreadSafeLRUCache:\n    \"\"\"Thread-safe LRU cache with TTL and async eviction.\n    \n    Adversarially hardened via SAGE-PRO Nash Equilibrium.\n    \"\"\"\n\n    def __init__(self, capacity: int = 128, default_ttl: float = 300.0) -> None:\n        if capacity <= 0:\n            raise ValueError(\"Capacity must be positive\")\n        self._capacity = capacity\n        self._default_ttl = default_ttl\n        self._cache: OrderedDict = OrderedDict()\n        self._ttls: dict[str, float] = {}\n        self._lock = threading.RLock()\n        self._stats = {\"hits\": 0, \"misses\": 0, \"evictions\": 0}\n\n    def get(self, key: str) -> Optional[Any]:\n        with self._lock:\n            if key not in self._cache:\n                self._stats[\"misses\"] += 1\n                return None\n            if self._is_expired(key):\n                self._remove(key)\n                self._stats[\"misses\"] += 1\n                return None\n            self._cache.move_to_end(key)\n            self._stats[\"hits\"] += 1\n            return self._cache[key]\n\n    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:\n        with self._lock:\n            if ttl is not None and ttl < 0:\n                raise ValueError(\"TTL must be non-negative\")\n            if key in self._cache:\n                self._cache.move_to_end(key)\n            self._cache[key] = value\n            self._ttls[key] = time.monotonic() + (ttl or self._default_ttl)\n            while len(self._cache) > self._capacity:\n                evicted_key, _ = self._cache.popitem(last=False)\n                del self._ttls[evicted_key]\n                self._stats[\"evictions\"] += 1\n```\n\n**Nash Equilibrium verified.** All 24 adversarial tests pass.',
]

function formatContent(text) {
  let html = text
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
    `<pre class="bg-[#0a0a0a] text-gray-300 rounded-lg p-4 my-3 overflow-x-auto text-[13px] leading-relaxed font-mono"><code>${code.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`
  )
  html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-[13px] font-mono">$1</code>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-[var(--color-ink)]">$1</strong>')
  html = html.replace(/\n/g, '<br/>')
  return html
}

function Message({ msg, onViewTrace }) {
  const isUser = msg.role === 'user'
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="max-w-[800px] w-full mx-auto px-6"
    >
      <div className={`py-6 ${!isUser ? 'border-b border-[var(--color-border-light)]' : ''}`}>
        <p className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isUser ? 'text-[var(--color-ink)]' : 'text-orange-600'}`}>
          {isUser ? 'You' : 'SAGE-PRO'}
        </p>
        {isUser ? (
          <p className="text-[15px] leading-relaxed text-[var(--color-ink-secondary)]">{msg.content}</p>
        ) : (
          <div>
            <div className="text-[15px] leading-[1.75] text-[var(--color-ink-secondary)]"
              dangerouslySetInnerHTML={{ __html: formatContent(msg.content) }}
            />
            {msg.trace && (
              <button
                onClick={() => onViewTrace(msg.trace)}
                className="mt-3 inline-flex items-center gap-1.5 text-xs text-[var(--color-ink-muted)] hover:text-orange-600 transition-colors"
              >
                <Sparkles size={12} />
                View AODE Trace
              </button>
            )}
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default function ChatStudio({ session, sidebarOpen, onToggleSidebar, onNewSession, addMessage, onViewTrace, onToggleTerminal }) {
  const [input, setInput] = useState('')
  const [generating, setGenerating] = useState(false)
  const textareaRef = useRef(null)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [session?.msgs])

  function resize() {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 180) + 'px'
  }

  async function send() {
    const text = input.trim()
    if (!text || generating) return
    if (!session) onNewSession()
    setInput('')
    setGenerating(true)
    if (textareaRef.current) { textareaRef.current.style.height = 'auto' }

    // Wait a tick for session to be created
    await new Promise(r => setTimeout(r, 50))
    addMessage('user', text)

    // Simulate pipeline
    const trace = []
    for (let i = 0; i < PIPELINE.length; i++) {
      await new Promise(r => setTimeout(r, PIPELINE[i].ms))
      trace.push({ ...PIPELINE[i], output: MOCK_OUTPUTS[i], time: (PIPELINE[i].ms / 1000).toFixed(1) + 's' })
    }

    const fullResponse = MOCK_OUTPUTS.join('\n\n---\n\n')
    addMessage('assistant', fullResponse, trace)
    setGenerating(false)
  }

  const msgs = session?.msgs || []
  const showWelcome = msgs.length === 0 && !generating

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Topbar */}
      <div className="h-12 flex items-center px-4 border-b border-[var(--color-border-light)] bg-white/60 backdrop-blur-sm">
        {!sidebarOpen && (
          <button onClick={onToggleSidebar} className="p-1.5 rounded-md hover:bg-gray-50 text-[var(--color-ink-muted)] mr-3 transition-colors">
            <PanelLeftOpen size={16} />
          </button>
        )}
        <span className="text-sm font-medium text-[var(--color-ink)]">{session?.title || 'SAGE-PRO'}</span>
        <div className="ml-auto flex items-center gap-2">
          <button onClick={onToggleTerminal} className="p-1.5 rounded-md hover:bg-gray-50 text-[var(--color-ink-muted)] transition-colors" title="Toggle Sandbox">
            <Terminal size={15} />
          </button>
          <span className="text-[11px] font-mono text-[var(--color-ink-muted)] bg-gray-50 px-2.5 py-1 rounded-full">
            Mistral-123B · Llama-70B · Qwen-32B
          </span>
        </div>
      </div>

      {/* Chat */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {showWelcome ? (
          <div className="flex flex-col items-center justify-center h-full px-6 text-center">
            <h1 className="text-3xl font-bold tracking-tight text-[var(--color-ink)] mb-2">What shall we build?</h1>
            <p className="text-[15px] text-[var(--color-ink-muted)] max-w-md leading-relaxed mb-10">
              Describe any coding task. Four adversarial agents will attack, defend, and harden your code until Nash Equilibrium.
            </p>
            <div className="grid grid-cols-2 gap-3 max-w-lg w-full">
              {SUGGESTIONS.map(s => (
                <button
                  key={s.title}
                  onClick={() => { setInput(s.prompt); textareaRef.current?.focus() }}
                  className="text-left p-4 rounded-xl border border-[var(--color-border)] hover:border-[var(--color-ink-muted)] hover:bg-white transition-all group"
                >
                  <p className="text-sm font-medium text-[var(--color-ink)] group-hover:text-orange-700 transition-colors">{s.title}</p>
                  <p className="text-xs text-[var(--color-ink-muted)] mt-0.5">{s.desc}</p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="py-4">
            <AnimatePresence>
              {msgs.map(m => <Message key={m.id} msg={m} onViewTrace={onViewTrace} />)}
            </AnimatePresence>
            {generating && (
              <div className="max-w-[800px] mx-auto px-6 py-6">
                <p className="text-xs font-semibold uppercase tracking-wider text-orange-600 mb-2">SAGE-PRO</p>
                <p className="text-sm text-[var(--color-ink-muted)] animate-pulse-text">Synthesizing through Nash Equilibrium...</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="px-6 pb-5 pt-3 bg-gradient-to-t from-[var(--color-surface)] via-[var(--color-surface)] to-transparent">
        <div className="max-w-[800px] mx-auto">
          <div className="flex items-end gap-2 bg-white border border-[var(--color-border)] rounded-2xl px-4 py-2 shadow-[0_1px_3px_rgba(0,0,0,0.04)] focus-within:border-[var(--color-ink-muted)] transition-colors">
            <button className="p-1.5 text-[var(--color-ink-muted)] hover:text-[var(--color-ink-secondary)] transition-colors mb-0.5">
              <Paperclip size={16} />
            </button>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => { setInput(e.target.value); resize() }}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
              placeholder="Describe the code you need..."
              rows={1}
              className="flex-1 resize-none outline-none text-[15px] leading-relaxed py-1.5 bg-transparent placeholder:text-[var(--color-ink-muted)]"
            />
            <button
              onClick={send}
              disabled={!input.trim() || generating}
              className="p-2 rounded-xl bg-[var(--color-ink)] text-white hover:bg-gray-800 disabled:opacity-20 disabled:cursor-not-allowed transition-all mb-0.5"
            >
              <ArrowUp size={16} />
            </button>
          </div>
          <p className="text-center text-[11px] text-[var(--color-ink-muted)] mt-2">
            SAGE-PRO hardens code via adversarial Nash Equilibrium on MI300X
          </p>
        </div>
      </div>
    </div>
  )
}
