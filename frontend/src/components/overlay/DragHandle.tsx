import React from "react";

interface DragHandleProps {
  onDragStart?: (e: React.MouseEvent) => void;
  className?: string;
}

export const DragHandle: React.FC<DragHandleProps> = ({
  onDragStart,
  className = "pt-1 pb-1",
}) => {
  return (
    <div
      onMouseDown={onDragStart}
      className={`w-full flex items-center justify-center cursor-grab active:cursor-grabbing group touch-none select-none ${className}`}
      title="Drag to reposition"
    >
      <div className="w-8 h-[3.5px] bg-handle/60 rounded-full transition-all duration-200 group-hover:w-12 group-hover:h-[4px] group-hover:bg-white/90 group-hover:shadow-[0_0_10px_rgba(255,255,255,0.6)]" />
    </div>
  );
};
