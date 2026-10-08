import { useRef, useState, useEffect, useCallback } from 'react';

export default function InfiniteCanvas({
  children,
  zoom = 1,
  onZoomChange,
  showGrid = true,
  contentWidth,
  contentHeight,
  contentBounds = null,
  fitTrigger = 0,
  allowWheelZoom = true,
  phaseKey = '',
  onCanvasClick,
}) {
  const containerRef = useRef(null);
  const [offset, setOffset] = useState({ x: 60, y: 40 });
  const [isDragging, setIsDragging] = useState(false);
  const [isFitting, setIsFitting] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const fitTimerRef = useRef(null);
  const zoomRef = useRef(zoom);
  useEffect(() => {
    zoomRef.current = zoom;
  }, [zoom]);

  const handleFit = useCallback(() => {
    if (!containerRef.current || !contentWidth || !contentHeight) {
      setOffset({ x: 60, y: 40 });
      if (onZoomChange) onZoomChange(1);
      return;
    }

    const containerW = containerRef.current.clientWidth;
    const containerH = containerRef.current.clientHeight;

    const padX = 52;
    const padY = 40;
    const availW = Math.max(100, containerW - padX * 2);
    const availH = Math.max(100, containerH - padY * 2);

    const bMinX = contentBounds ? contentBounds.minX : 0;
    const bMinY = contentBounds ? contentBounds.minY : 0;
    const bMaxX = contentBounds ? contentBounds.maxX : contentWidth;
    const bMaxY = contentBounds ? contentBounds.maxY : contentHeight;

    const boundW = Math.max(1, bMaxX - bMinX);
    const boundH = Math.max(1, bMaxY - bMinY);

    const scaleX = availW / boundW;
    const scaleY = availH / boundH;
    let idealZoom = Math.min(scaleX, scaleY);

    if (idealZoom >= 1.0) {
      idealZoom = 1.0;
    } else {
      idealZoom = Math.max(0.45, Math.min(1.0, Number(idealZoom.toFixed(2))));
    }

    const newOffsetX = Math.max(24 - bMinX * idealZoom, Math.round((containerW - (bMinX + bMaxX) * idealZoom) / 2));
    const newOffsetY = Math.max(20 - bMinY * idealZoom, Math.round((containerH - (bMinY + bMaxY) * idealZoom) / 2));

    setIsFitting(true);
    setOffset({ x: newOffsetX, y: newOffsetY });
    if (onZoomChange && Math.abs(zoomRef.current - idealZoom) > 0.01) {
      onZoomChange(idealZoom);
    }

    if (fitTimerRef.current) clearTimeout(fitTimerRef.current);
    fitTimerRef.current = setTimeout(() => {
      setIsFitting(false);
    }, 1150);
  }, [contentWidth, contentHeight, contentBounds, onZoomChange]);

  useEffect(() => {
    if (fitTrigger > 0) {
      handleFit();
    }
  }, [fitTrigger, handleFit]);

  const prevPhaseKeyRef = useRef('');
  useEffect(() => {
    if (phaseKey && phaseKey !== prevPhaseKeyRef.current) {
      prevPhaseKeyRef.current = phaseKey;
      handleFit();
      const t1 = setTimeout(() => {
        handleFit();
      }, 350);
      const t2 = setTimeout(() => {
        handleFit();
      }, 750);
      return () => {
        clearTimeout(t1);
        clearTimeout(t2);
      };
    }
  }, [phaseKey, handleFit]);

  const prevDimensionsRef = useRef({ width: 0, height: 0 });
  const resizeDebounceRef = useRef(null);
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width <= 0 || height <= 0) continue;
        const prevW = prevDimensionsRef.current.width;
        const prevH = prevDimensionsRef.current.height;
        const diffW = Math.abs(width - prevW);
        const diffH = Math.abs(height - prevH);

        if (prevW === 0 && prevH === 0) {
          prevDimensionsRef.current = { width, height };
          handleFit();
          continue;
        }

        if (diffW > 4 || diffH > 4) {
          prevDimensionsRef.current = { width, height };
          handleFit();
          if (resizeDebounceRef.current) clearTimeout(resizeDebounceRef.current);
          resizeDebounceRef.current = setTimeout(() => {
            handleFit();
          }, 260);
        }
      }
    });
    observer.observe(containerRef.current);
    return () => {
      observer.disconnect();
      if (resizeDebounceRef.current) clearTimeout(resizeDebounceRef.current);
    };
  }, [handleFit, phaseKey]);

  const handleClick = (e) => {
    if (!e.target.closest('button, select, input, textarea, a, [data-interactive="true"]')) {
      if (onCanvasClick) onCanvasClick(e);
    }
  };

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
      onClick={handleClick}
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
