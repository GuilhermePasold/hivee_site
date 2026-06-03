import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// shadcn-style class combiner used by the imported 21st.dev components.
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const BRL = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0,
});
