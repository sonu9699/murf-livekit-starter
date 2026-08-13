import { cn } from '@/lib/shadcn/utils';

/** Which accent the orb glows in — mirrors the agent's live state. */
export type OrbTone = 'primary' | 'teal' | 'indigo';

const RING_BG: Record<OrbTone, string> = {
  primary: 'bg-primary',
  teal: 'bg-teal',
  indigo: 'bg-indigo',
};

interface VoiceOrbProps {
  /** True while the agent is listening / thinking / speaking. */
  active?: boolean;
  tone?: OrbTone;
  className?: string;
  children?: React.ReactNode;
}

/**
 * A purely 2D pulsing halo around a center glyph (the Saathi avatar).
 * When active, two staggered rings expand and fade like a soft radar pulse.
 * No WebGL / 3D — just transform + opacity, so it stays cheap on mobile.
 */
export function VoiceOrb({ active = false, tone = 'primary', className, children }: VoiceOrbProps) {
  return (
    <span className={cn('relative inline-flex items-center justify-center', className)}>
      {active && (
        <>
          <span
            aria-hidden
            className={cn(
              'absolute inline-flex h-full w-full rounded-full opacity-30 motion-safe:animate-ping',
              RING_BG[tone]
            )}
          />
          <span
            aria-hidden
            className={cn(
              'absolute inline-flex h-full w-full rounded-full opacity-20 [animation-delay:0.45s] motion-safe:animate-ping',
              RING_BG[tone]
            )}
          />
        </>
      )}
      <span className="relative z-10 inline-flex items-center justify-center">{children}</span>
    </span>
  );
}
