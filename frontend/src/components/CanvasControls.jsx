import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';

export default function CanvasControls({
  zoom,
  onZoomIn,
  onZoomOut,
  onResetFit,
}) {
  return (
    <div className="absolute bottom-5 left-6 z-20 h-9 flex items-center gap-1 bg-[#f4f0e8]/95 backdrop-blur-md px-2.5 rounded-xl border border-[#dfd8c8] shadow-xs text-xs font-mono select-none">
      <button
        type="button"
        onClick={onZoomOut}
        className="text-[#706b63] hover:text-[#1e1c19] transition-colors cursor-pointer p-1 rounded-md hover:bg-[#eae4d6]"
        title="Zoom out"
      >
        <ZoomOut size={14} />
      </button>

      <span className="text-[#1e1c19] font-mono text-[11.5px] px-1 font-medium min-w-[38px] text-center">
        {Math.round(zoom * 100)}%
      </span>

      <button
        type="button"
        onClick={onZoomIn}
        className="text-[#706b63] hover:text-[#1e1c19] transition-colors cursor-pointer p-1 rounded-md hover:bg-[#eae4d6]"
        title="Zoom in"
      >
        <ZoomIn size={14} />
      </button>

      <div className="w-[1px] h-3.5 bg-[#dfd8c8] mx-1" />

      <button
        type="button"
        onClick={onResetFit}
        className="flex items-center gap-1 text-[#706b63] hover:text-[#1e1c19] transition-colors cursor-pointer px-1.5 py-1 rounded-md hover:bg-[#eae4d6] text-[11.5px]"
        title="Reset Fit (100%)"
      >
        <Maximize2 size={13} />
        <span>Fit</span>
      </button>
    </div>
  );
}
