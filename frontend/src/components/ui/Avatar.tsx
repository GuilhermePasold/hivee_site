import type { CSSProperties } from "react";

interface AvatarProps {
  src: string | null | undefined;
  alt: string;
  size?: number;
  className?: string;
}

function initials(name: string): string {
  return name
    .split(" ")
    .map((w) => w[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function colorFromName(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 30%, 25%)`;
}

export default function Avatar({ src, alt, size = 64, className = "" }: AvatarProps) {
  if (src) {
    return (
      <img
        src={src}
        alt={alt}
        className={className}
        style={{ width: size, height: size }}
        onError={(e) => {
          const t = e.currentTarget;
          t.style.display = "none";
          t.nextElementSibling?.classList.remove("hidden");
        }}
      />
    );
  }

  return (
    <div
      className={`flex items-center justify-center font-semibold text-white/80 ${className}`}
      style={{ width: size, height: size, background: colorFromName(alt), fontSize: size * 0.35 }}
      title={alt}
    >
      {initials(alt)}
    </div>
  );
}
