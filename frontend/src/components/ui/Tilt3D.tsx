import { useRef, type ReactNode } from "react";

// Mouse-tracking 3D tilt (animation, based on the aceternity 3d-card-effect).
export default function Tilt3D({
  children,
  className,
  max = 9,
}: {
  children: ReactNode;
  className?: string;
  max?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);

  function onMove(e: React.MouseEvent<HTMLDivElement>) {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const x = (e.clientX - r.left - r.width / 2) / (r.width / 2);
    const y = (e.clientY - r.top - r.height / 2) / (r.height / 2);
    el.style.transform = `perspective(900px) rotateY(${x * max}deg) rotateX(${-y * max}deg) scale(1.02)`;
  }
  function onLeave() {
    const el = ref.current;
    if (el) el.style.transform = "perspective(900px) rotateY(0deg) rotateX(0deg) scale(1)";
  }

  return (
    <div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      className={className}
      style={{ transformStyle: "preserve-3d", transition: "transform 0.25s cubic-bezier(0.16,1,0.3,1)", willChange: "transform" }}
    >
      {children}
    </div>
  );
}
