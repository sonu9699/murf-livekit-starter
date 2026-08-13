import { cn } from '@/lib/shadcn/utils';

/**
 * Brand glyphs from Simple Icons (https://github.com/simple-icons/simple-icons —
 * the icon SVGs are CC0). Rendered monochrome via `currentColor` so they sit
 * quietly in the editorial colophon. Murf has no Simple Icon, so it stays a
 * text wordmark in the credit line.
 */

interface BrandIconProps {
  className?: string;
}

function BrandGlyph({ title, path, className }: { title: string; path: string } & BrandIconProps) {
  return (
    <svg
      role="img"
      viewBox="0 0 24 24"
      aria-label={title}
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      className={cn('size-3.5', className)}
    >
      <title>{title}</title>
      <path d={path} />
    </svg>
  );
}

const LIVEKIT_PATH =
  'M0 0v24h14.4v-4.799h4.8V24H24v-4.8h-4.799v-4.8h-4.8v4.8H4.8V0H0zm14.4 14.4V9.602h4.801V4.8H24V0h-4.8v4.8h-4.8v4.8H9.6v4.8h4.8z';
const DEEPGRAM_PATH =
  'M11.203 24H1.517a.364.364 0 0 1-.258-.62l6.239-6.275a.366.366 0 0 1 .259-.108h3.52c2.723 0 5.025-2.127 5.107-4.845a5.004 5.004 0 0 0-4.999-5.148H7.613v4.646c0 .2-.164.364-.365.364H.968a.365.365 0 0 1-.363-.364V.364C.605.164.768 0 .969 0h10.416c6.684 0 12.111 5.485 12.01 12.187C23.293 18.77 17.794 24 11.202 24z';
const GEMINI_PATH =
  'M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81';

export function LiveKitIcon({ className }: BrandIconProps) {
  return <BrandGlyph title="LiveKit" path={LIVEKIT_PATH} className={className} />;
}

export function DeepgramIcon({ className }: BrandIconProps) {
  return <BrandGlyph title="Deepgram" path={DEEPGRAM_PATH} className={className} />;
}

export function GeminiIcon({ className }: BrandIconProps) {
  return <BrandGlyph title="Google Gemini" path={GEMINI_PATH} className={className} />;
}
