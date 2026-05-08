import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ChatStudio from './components/ChatStudio'
import CrucibleDrawer from './components/CrucibleDrawer'
import SandboxTerminal from './components/SandboxTerminal'
import SettingsModal from './components/SettingsModal'

export default function App() {
  const [sessions, setSessions] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [terminalOpen, setTerminalOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [drawerTrace, setDrawerTrace] = useState(null)

  const active = sessions.find(s => s.id === activeId) || null

  function newSession() {
    const s = { id: Date.now(), title: 'New Session', msgs: [] }
    setSessions(prev => [s, ...prev])
    setActiveId(s.id)
  }

  function addMessage(role, content, trace) {
    setSessions(prev =>
      prev.map(s =>
        s.id === activeId
          ? {
              ...s,
              title: s.msgs.length === 0 && role === 'user' ? content.slice(0, 50) : s.title,
              msgs: [...s.msgs, { role, content, trace, id: Date.now() }],
            }
          : s
      )
    )
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-surface)]">
      {sidebarOpen && (
        <Sidebar
          sessions={sessions}
          activeId={activeId}
          onSelect={setActiveId}
          onNew={newSession}
          onSettings={() => setSettingsOpen(true)}
          onCollapse={() => setSidebarOpen(false)}
        />
      )}

      <div className="flex-1 flex flex-col min-w-0 relative">
        <ChatStudio
          session={active}
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onNewSession={newSession}
          addMessage={addMessage}
          onViewTrace={trace => { setDrawerTrace(trace); setDrawerOpen(true) }}
          onToggleTerminal={() => setTerminalOpen(!terminalOpen)}
        />

        {terminalOpen && <SandboxTerminal onClose={() => setTerminalOpen(false)} />}
      </div>

      <CrucibleDrawer
        open={drawerOpen}
        trace={drawerTrace}
        onClose={() => setDrawerOpen(false)}
      />

      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </div>
  )
}
