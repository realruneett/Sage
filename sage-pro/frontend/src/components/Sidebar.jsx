import { Plus, Settings, PanelLeftClose, MessageSquare } from 'lucide-react'

export default function Sidebar({ sessions, activeId, onSelect, onNew, onSettings, onCollapse }) {
  return (
    <aside className="w-[250px] min-w-[250px] bg-white border-r border-[var(--color-border)] flex flex-col h-full">
      {/* Header */}
      <div className="px-4 pt-5 pb-3 flex items-center justify-between">
        <span className="text-sm font-semibold tracking-tight text-[var(--color-ink)]">SAGE-PRO</span>
        <button onClick={onCollapse} className="p-1.5 rounded-md hover:bg-gray-50 text-[var(--color-ink-muted)] transition-colors">
          <PanelLeftClose size={16} />
        </button>
      </div>

      {/* New Session */}
      <div className="px-3 pb-2">
        <button
          onClick={onNew}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--color-ink-secondary)] rounded-lg border border-dashed border-[var(--color-border)] hover:bg-gray-50 hover:border-[var(--color-ink-muted)] transition-all"
        >
          <Plus size={15} />
          New Project
        </button>
      </div>

      {/* Sessions */}
      <div className="flex-1 overflow-y-auto px-2 py-1">
        {sessions.length === 0 && (
          <p className="px-3 py-6 text-xs text-[var(--color-ink-muted)] text-center">No sessions yet</p>
        )}
        {sessions.map(s => (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            className={`w-full text-left flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors mb-0.5 ${
              s.id === activeId
                ? 'bg-[var(--color-accent-soft)] text-orange-700 font-medium'
                : 'text-[var(--color-ink-secondary)] hover:bg-gray-50'
            }`}
          >
            <MessageSquare size={14} className="flex-shrink-0 opacity-50" />
            <span className="truncate">{s.title}</span>
          </button>
        ))}
      </div>

      {/* Footer */}
      <div className="px-3 py-3 border-t border-[var(--color-border-light)]">
        <button
          onClick={onSettings}
          className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-[var(--color-ink-muted)] rounded-lg hover:bg-gray-50 transition-colors"
        >
          <Settings size={15} />
          Settings
        </button>
      </div>
    </aside>
  )
}
