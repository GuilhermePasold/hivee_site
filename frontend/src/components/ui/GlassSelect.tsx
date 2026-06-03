import { AnimatePresence, motion } from "framer-motion";
import { Check, ChevronDown } from "lucide-react";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/utils";

export interface SelectOption {
  value: string;
  label: string;
}

interface MenuRect {
  top: number;
  left: number;
  width: number;
  placement: "down" | "up";
}

export default function GlassSelect({
  value,
  onChange,
  options,
  placeholder = "Selecione",
  className,
  triggerClassName,
}: {
  value: string;
  onChange: (v: string) => void;
  options: SelectOption[];
  placeholder?: string;
  className?: string;
  triggerClassName?: string;
}) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLUListElement>(null);
  const [rect, setRect] = useState<MenuRect | null>(null);

  // The menu is rendered in a portal at <body> with position:fixed so it can
  // never be clipped by an `overflow` ancestor nor sit behind a transformed
  // card (which creates its own stacking context).
  const reposition = () => {
    const el = triggerRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const spaceBelow = window.innerHeight - r.bottom;
    const placement: "down" | "up" = spaceBelow < 300 && r.top > spaceBelow ? "up" : "down";
    const width = Math.max(r.width, 200);
    // Keep the menu fully inside the viewport horizontally.
    const left = Math.max(8, Math.min(r.left, window.innerWidth - width - 8));
    setRect({
      top: placement === "down" ? r.bottom + 8 : r.top - 8,
      left,
      width,
      placement,
    });
  };

  useLayoutEffect(() => {
    if (!open) return;
    reposition();
    const onMove = () => reposition();
    window.addEventListener("scroll", onMove, true);
    window.addEventListener("resize", onMove);
    return () => {
      window.removeEventListener("scroll", onMove, true);
      window.removeEventListener("resize", onMove);
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      const t = e.target as Node;
      if (triggerRef.current?.contains(t) || menuRef.current?.contains(t)) return;
      setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [open]);

  const selected = options.find((o) => o.value === value);

  return (
    <div className={cn("relative", className)}>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "flex w-full cursor-pointer items-center justify-between gap-2 rounded-2xl border border-white/12 bg-white/5 px-4 py-3 text-left transition-colors hover:border-white/20 focus:border-gold-500/50 focus:outline-none",
          triggerClassName,
        )}
      >
        <span className={selected ? "truncate text-foreground" : "truncate text-muted-foreground"}>
          {selected ? selected.label : placeholder}
        </span>
        <ChevronDown
          className={cn("h-4 w-4 shrink-0 text-gold-400 transition-transform duration-300", open && "rotate-180")}
        />
      </button>

      {createPortal(
        <AnimatePresence>
          {open && rect && (
            <motion.ul
              ref={menuRef}
              initial={{ opacity: 0, y: rect.placement === "down" ? -6 : 6, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: rect.placement === "down" ? -6 : 6, scale: 0.98 }}
              transition={{ duration: 0.16, ease: [0.16, 1, 0.3, 1] }}
              style={{
                position: "fixed",
                top: rect.placement === "down" ? rect.top : undefined,
                bottom: rect.placement === "up" ? window.innerHeight - rect.top : undefined,
                left: rect.left,
                width: rect.width,
                minWidth: 200,
              }}
              className="glass-solid z-[200] max-h-72 overflow-auto rounded-2xl p-1.5"
            >
              {options.map((o) => {
                const active = o.value === value;
                return (
                  <li key={o.value || "__all"}>
                    <button
                      type="button"
                      onClick={() => {
                        onChange(o.value);
                        setOpen(false);
                      }}
                      className={cn(
                        "flex w-full items-center justify-between gap-2 rounded-xl px-3 py-2.5 text-left text-sm transition-colors",
                        active ? "bg-gold-500/15 text-gold-200" : "text-foreground/80 hover:bg-white/8 hover:text-foreground",
                      )}
                    >
                      <span className="truncate">{o.label}</span>
                      {active && <Check className="h-4 w-4 shrink-0 text-gold-400" />}
                    </button>
                  </li>
                );
              })}
            </motion.ul>
          )}
        </AnimatePresence>,
        document.body,
      )}
    </div>
  );
}
