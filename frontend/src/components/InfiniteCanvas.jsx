import { useRef, useState, useEffect, useCallback } from 'react';

export default function InfiniteCanvas({
  children,
  zoom = 1,
  onZoomChange,
  showGrid = true,
  contentWidth,
  contentHeight,
  fitTrigger = 0,
  allowWheelZoom = true,
}) {
  const containerRef = useRef(null);
  const [offset, setOffset] = useState({ x: 60, y: 40 });
  const [isDragging, setIsDragging] = useState(false);
  const [isFitting, setIsFitting] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const fitTimerRef = useRef(null);
  const zoomRef = useRef(zoom);
  zoomRef.current = zoom;

  const handleFit = useCallback(() => {
    if (!containerRef.current || !contentWidth || !contentHeight) {
      setOffset({ x: 60, y: 40 });
      if (onZoomChange) onZoomChange(1);
      return;
    }

    const containerW = containerRef.current.clientWidth;
    const containerH = containerRef.current.clientHeight;

    const padX = 40;
    const padY = 40;
    const availW = Math.max(100, containerW - padX * 2);
    const availH = Math.max(100, containerH - padY * 2);

    const scaleX = availW / contentWidth;
    const scaleY = availH / contentHeight;
    let idealZoom = Math.min(scaleX, scaleY);

    if (idealZoom >= 0.85) {
      idealZoom = 1.0;
    } else {
      idealZoom = Math.max(0.55, Number(idealZoom.toFixed(2)));
    }

    const scaledW = contentWidth * idealZoom;
    const scaledH = contentHeight * idealZoom;

    const newOffsetX = Math.max(20, Math.round((containerW - scaledW) / 2));
    const newOffsetY = Math.max(20, Math.round((containerH - scaledH) / 2));

    setIsFitting(true);
    setOffset({ x: newOffsetX, y: newOffsetY });
    if (onZoomChange && Math.abs(zoomRef.current - idealZoom) > 0.01) {
      onZoomChange(idealZoom);
    }

    if (fitTimerRef.current) clearTimeout(fitTimerRef.current);
    fitTimerRef.current = setTimeout(() => {
      setIsFitting(false);
    }, 1150);
  }, [contentWidth, contentHeight, onZoomChange]);

  useEffect(() => {
    if (fitTrigger > 0) {
      handleFit();
    }
  }, [fitTrigger, handleFit]);

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
          handleFit();
        }
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [handleFit]);

  const handleMouseDown = (e) => {
    if (e.button !== 0) return;
    if (e.target.closest('button, select, input, textarea, a, [data-interactive="true"]')) {
      return;
    }
    setIsDragging(true);
    dragStartRef.current = {
      x: e.clientX - offset.x,
      y: e.clientY - offset.y,
    };
  };

  const handleMouseMove = useCallback(
    (e) => {
      if (!isDragging) return;
      setOffset({
        x: e.clientX - dragStartRef.current.x,
        y: e.clientY - dragStartRef.current.y,
      });
    },
    [isDragging]
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  const handleWheel = (e) => {
    e.preventDefault();
    if (!allowWheelZoom) {
      setOffset((prev) => ({
        ...prev,
        y: prev.y - e.deltaY,
      }));
      return;
    }
    if (!onZoomChange) return;
    const delta = e.deltaY < 0 ? 0.08 : -0.08;
    const newZoom = Math.min(Math.max(zoom + delta, 0.35), 2.2);
    onZoomChange(Number(newZoom.toFixed(2)));
  };

  return (
    <div
      ref={containerRef}
      onMouseDown={handleMouseDown}
      onWheel={handleWheel}
      className={`relative flex-1 w-full h-full overflow-hidden select-none ${
        showGrid ? 'dot-grid' : 'bg-[#f7f4ed]'
      } ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
    >
      <div
        className="absolute origin-top-left"
        style={{
          transform: `translate(${offset.x}px, ${offset.y}px) scale(${zoom})`,
          transition: isDragging
            ? 'none'
            : isFitting
            ? 'transform 1.1s cubic-bezier(0.45, 0.05, 0.15, 0.98)'
            : 'transform 75ms ease-out',
        }}
      >
        {children}
      </div>
    </div>
  );
}
