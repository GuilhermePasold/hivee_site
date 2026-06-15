import { useEffect, useRef, useState } from "react";
import { Hash, Plus, X } from "lucide-react";
import { api } from "@/lib/api";
import type { Tag } from "@/types";

interface TagInputProps {
  value: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  max?: number;
}

const norm = (s: string) => s.trim().toLowerCase();

// Campo de tags de serviço com autocomplete: digita, vê sugestões existentes
// (clica pra adicionar) ou cria uma nova tag na hora. Tudo livre de hardcode:
// as sugestões vêm do vocabulário real do backend (`/api/tags/`).
export default function TagInput({ value, onChange, placeholder, max = 15 }: TagInputProps) {
  const [text, setText] = useState("");
  const [suggestions, setSuggestions] = useState<Tag[]>([]);
  const [open, setOpen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    const q = text.trim();
    const t = setTimeout(() => {
      api
        .tags(q || undefined)
        .then((tags) => setSuggestions(tags))
        .catch(() => setSuggestions([]));
    }, 220);
    return () => clearTimeout(t);
  }, [text]);

  const selected = new Set(value.map(norm));
  const filtered = suggestions.filter((t) => !selected.has(norm(t.name)));
  const typed = text.trim();
  const exactExists =
    !!typed && suggestions.some((t) => norm(t.name) === norm(typed));
  const canCreate = !!typed && !exactExists && !selected.has(norm(typed));

  function addTag(name: string) {
    const clean = name.trim();
    if (!clean || selected.has(norm(clean)) || value.length >= max) return;
    onChange([...value, clean]);
    setText("");
    setOpen(false);
  }

  function removeTag(name: string) {
    onChange(value.filter((t) => t !== name));
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      if (filtered[0] && norm(filtered[0].name).startsWith(norm(typed)) && !canCreate) {
        addTag(filtered[0].name);
      } else if (typed) {
        addTag(typed);
      }
    } else if (e.key === "Backspace" && !text && value.length) {
      removeTag(value[value.length - 1]);
    }
  }

  return (
    <div ref={boxRef} className="relative">
      <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-white/12 bg-white/5 p-2.5 focus-within:border-gold-500/50">
        {value.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1.5 rounded-full border border-gold-500/40 bg-gold-500/15 px-3 py-1 text-sm text-gold-100"
          >
            <Hash className="h-3 w-3 text-gold-300" />
            {tag}
            <button
              type="button"
              onClick={() => removeTag(tag)}
              aria-label={`Remover ${tag}`}
              className="ml-0.5 rounded-full p-0.5 text-gold-200/70 hover:bg-white/10 hover:text-white"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        {value.length < max && (
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            onFocus={() => setOpen(true)}
            onKeyDown={onKeyDown}
            placeholder={value.length ? "" : placeholder || "Digite um serviço e Enter"}
            className="min-w-[140px] flex-1 bg-transparent px-1.5 py-1 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
          />
        )}
      </div>

      {open && (filtered.length > 0 || canCreate) && (
        <div className="absolute z-30 mt-2 w-full overflow-hidden rounded-2xl border border-white/12 bg-[#15151a] shadow-xl">
          {canCreate && (
            <button
              type="button"
              onClick={() => addTag(typed)}
              className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm text-gold-200 hover:bg-white/5"
            >
              <Plus className="h-4 w-4" /> Criar tag “{typed}”
            </button>
          )}
          {filtered.slice(0, 8).map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => addTag(t.name)}
              className="flex w-full items-center justify-between px-4 py-2.5 text-left text-sm text-foreground/85 hover:bg-white/5"
            >
              <span className="inline-flex items-center gap-2">
                <Hash className="h-3.5 w-3.5 text-gold-400" /> {t.name}
              </span>
              {!!t.provider_count && (
                <span className="text-xs text-muted-foreground">{t.provider_count}</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
