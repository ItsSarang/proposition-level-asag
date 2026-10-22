export default function Header({
  activeTab = 'workbench',
  onTabChange,
}) {

  return (
    <header className="sticky top-0 z-50 w-full bg-[#f2eee5]/95 backdrop-blur-md border-b border-[#dfd8c8] select-none">
      <div className="w-full px-6 h-13 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2.5 shrink-0">
          <span className="font-bold text-[#1e1c19] text-[16px] tracking-tight">
            ASAG Lab
          </span>
          <span className="hidden sm:inline-block text-[11px] font-mono text-[#8c8477] border-l border-[#dfd8c8] pl-2.5">
            Proposition-Level ASAG
          </span>
          <span className="bg-purple-100 text-purple-800 text-[11px] font-mono font-medium px-2.5 py-0.5 rounded-full border border-purple-300">
            v1.0.2 (Production)
          </span>
        </div>



        <nav className="flex items-center shrink-0">
          <div className="inline-flex items-center bg-[#e6e0d2] p-0.5 rounded-xl border border-[#d8d0bf]">
            <button
              type="button"
              onClick={() => onTabChange && onTabChange('workbench')}
              className={`px-3.5 py-1 rounded-lg text-[12px] font-mono tracking-wide transition-all cursor-pointer ${
                activeTab === 'workbench'
                  ? 'bg-[#faf8f4] text-[#1e1c19] font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19] font-normal'
              }`}
            >
              Workbench
            </button>
            <button
              type="button"
              onClick={() => onTabChange && onTabChange('research')}
              className={`px-3.5 py-1 rounded-lg text-[12px] font-mono tracking-wide transition-all cursor-pointer ${
                activeTab === 'research'
                  ? 'bg-[#faf8f4] text-[#1e1c19] font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19] font-normal'
              }`}
            >
              Research
            </button>
          </div>
        </nav>
      </div>
    </header>
  );
}
