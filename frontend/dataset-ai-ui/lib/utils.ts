import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

// Standard shadcn utility: clsx for conditional class composition,
// tailwind-merge to resolve conflicting Tailwind classes (e.g. a later
// `px-4` overriding an earlier `px-6`) instead of emitting both.
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
