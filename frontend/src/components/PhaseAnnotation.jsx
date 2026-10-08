import { useId } from 'react';

export default function PhaseAnnotation({
  number,
  title,
  description,
  connector = 'right-down',
  visible = true,
  titleSize = '22px',
  descSize = '17px',
  className = '',
  style = {},
}) {
  const uniqueId = useId().replace(/:/g, '');
  const markerId = `arrowhead-anno-${uniqueId}`;

  const isRightLayout = connector === 'right-down' || connector === 'right';

  let svgWidth = 76;
  let svgHeight = 44;
  let viewBox = '0 0 76 44';
  let pathD = 'M 4 10 C 28 11, 48 22, 70 36';
  let svgClasses = 'mt-1.5 shrink-0';

  if (connector === 'down-right') {
    svgWidth = 56;
    svgHeight = 36;
    viewBox = '0 0 56 36';
    pathD = 'M 8 2 C 10 16, 24 26, 50 32';
    svgClasses = '-mt-0.5 shrink-0 ml-2';
  } else if (connector === 'down') {
    svgWidth = 32;
    svgHeight = 44;
    viewBox = '0 0 32 44';
    pathD = 'M 16 2 C 18 16, 12 28, 16 38';
    svgClasses = 'shrink-0 ml-4';
  } else if (connector === 'right') {
    svgWidth = 66;
    svgHeight = 26;
    viewBox = '0 0 66 26';
    pathD = 'M 2 13 C 24 10, 44 17, 60 13';
    svgClasses = 'mt-2 shrink-0';
  }

  return (
    <div
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(-4px)',
        transition: 'opacity 0.45s cubic-bezier(0.16, 1, 0.3, 1), transform 0.45s cubic-bezier(0.16, 1, 0.3, 1)',
        pointerEvents: visible ? 'auto' : 'none',
        ...style,
      }}
      className={`absolute z-40 flex ${isRightLayout ? 'flex-row items-start' : 'flex-col items-start'} select-none gap-2 ${className}`}
    >
      <div className="flex flex-col select-none">
        <div
          style={{ fontSize: typeof titleSize === 'number' ? `${titleSize}px` : titleSize }}
          className="font-handwriting font-bold text-[#2c2250] tracking-wide uppercase leading-tight select-none"
        >
          <span className="mr-1.5">{number}</span>
          <span>{title}</span>
        </div>
        <div
          style={{ fontSize: typeof descSize === 'number' ? `${descSize}px` : descSize }}
          className="font-handwriting italic text-[#5e564a] leading-snug mt-0.5 max-w-[340px] select-none"
        >
          {description}
        </div>
      </div>

      {connector !== 'none' && (
        <svg
          width={svgWidth}
          height={svgHeight}
          viewBox={viewBox}
          className={`overflow-visible pointer-events-none select-none text-indigo-700/70 hidden sm:block ${svgClasses}`}
        >
          <defs>
            <marker
              id={markerId}
              viewBox="0 0 8 8"
              refX="6"
              refY="4"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path
                d="M 1 1 L 6 4 L 1 7"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </marker>
          </defs>
          <path
            d={pathD}
            fill="none"
            stroke="currentColor"
            strokeWidth="1.4"
            strokeLinecap="round"
            markerEnd={`url(#${markerId})`}
            style={{
              strokeDasharray: 120,
              strokeDashoffset: visible ? 0 : 120,
              transition: 'stroke-dashoffset 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          />
        </svg>
      )}
    </div>
  );
}
