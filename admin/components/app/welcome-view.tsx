import { ArrowRight, Loader2 } from 'lucide-react';
import { DeepgramIcon, GeminiIcon, LiveKitIcon } from '@/components/app/brand-icons';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/shadcn/utils';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  /** True while the session is connecting — shows the "Connecting" state on the CTA. */
  isStarting?: boolean;
}

/** Almanac "contents" — the sections this baat-cheet can cover. */
const TOPICS = [
  { n: '01', label: 'Symptoms samajhna', hi: 'लक्षण', dot: 'bg-teal' },
  { n: '02', label: 'Home-care guidance', hi: 'घरेलू देखभाल', dot: 'bg-terracotta' },
  { n: '03', label: 'Sarkari schemes', hi: 'सरकारी योजनाएँ', dot: 'bg-indigo' },
];

/**
 * "Aarogya Almanac" — the landing reads like the cover of a printed health
 * patrika: double-rule masthead, oversized display headline, Devanagari
 * accents, a halftone ink strip, a numbered contents list and a rubber-stamp
 * badge. Warm, art-directed, distinctly Bharat — no gradients/glow/3D.
 */
export const WelcomeView = ({
  startButtonText,
  onStartCall,
  isStarting = false,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="w-full px-6 pt-28 pb-20 md:pt-32">
      <section className="relative mx-auto w-full max-w-3xl">
        {/* Soft halftone "sun" — a print-texture wash behind the headline. No
            hard rings: edges fade out so it reads as atmosphere, not a stray
            circle crossing the type. */}
        <div
          aria-hidden
          className="pointer-events-none absolute -top-4 -right-8 aspect-square w-[clamp(12rem,34vw,24rem)]"
        >
          <div className="halftone text-primary size-full rounded-full [mask-image:radial-gradient(circle,#000_30%,transparent_68%)] opacity-55" />
        </div>

        <div className="relative z-10">
          {/* Masthead — double-rule, issue-style */}
          <div className="border-foreground/80 flex items-end justify-between border-b-2 pb-2.5 font-mono text-[0.7rem] tracking-[0.2em] uppercase">
            <span className="text-foreground flex items-center gap-2">
              <span className="bg-primary inline-block size-2.5 rotate-45" aria-hidden />
              आरोग्य साथी
            </span>
            <span className="text-muted-foreground">Ank 01 · Voice</span>
          </div>
          <div className="border-foreground/25 mt-[3px] border-b" />

          {/* Eyebrow */}
          <p className="text-muted-foreground mt-8 font-mono text-[0.7rem] tracking-[0.28em] uppercase">
            स्वास्थ्य · Voice · Bharat
          </p>

          {/* Headline — oversized editorial display */}
          <h1 className="font-display mt-4 text-[clamp(3.25rem,13vw,7.5rem)] leading-[0.85] font-light tracking-[-0.02em] text-balance">
            Tabiyat
            <br />
            kaisi hai <span className="text-primary italic">aaj?</span>
          </h1>

          {/* Halftone ink strip */}
          <div className="halftone mt-6 h-5 w-44 max-w-full" aria-hidden />

          {/* Subhead + Devanagari pull-quote */}
          <div className="mt-6 grid gap-6 sm:grid-cols-[1.35fr_1fr] sm:items-start">
            <p className="text-foreground/80 max-w-md text-base leading-relaxed text-pretty">
              Hindi ya English — jaise aap bolein, waise samjhega. Chhote sheher aur gaon ke liye ek
              bharosemand health saathi.
            </p>
            <p className="font-display text-muted-foreground text-lg leading-snug text-balance sm:text-right">
              “आपकी सेहत,
              <br />
              आपकी भाषा में।”
            </p>
          </div>

          {/* Contents index */}
          <div className="mt-10">
            <p className="text-muted-foreground/70 font-mono text-[0.65rem] tracking-[0.24em] uppercase">
              Is baat-cheet me
            </p>
            <ol className="border-foreground/25 mt-2 border-t">
              {TOPICS.map((t) => (
                <li
                  key={t.n}
                  className="border-foreground/15 flex items-center gap-4 border-b py-3.5"
                >
                  <span className="text-muted-foreground/50 font-mono text-sm tabular-nums">
                    {t.n}
                  </span>
                  <span className={cn('size-1.5 shrink-0 rounded-full', t.dot)} aria-hidden />
                  <span className="text-foreground flex-1 text-lg tracking-tight">{t.label}</span>
                  <span className="text-muted-foreground/55 font-display hidden text-base sm:inline">
                    {t.hi}
                  </span>
                </li>
              ))}
            </ol>
          </div>

          {/* CTA + rubber-stamp badge */}
          <div className="mt-10 flex flex-wrap items-center gap-x-8 gap-y-6">
            <Button
              size="lg"
              onClick={onStartCall}
              disabled={isStarting}
              aria-busy={isStarting}
              className="group text-primary-foreground h-16 gap-3 rounded-none px-10 font-mono text-sm font-bold tracking-[0.16em] uppercase transition-transform duration-200 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.99]"
            >
              {isStarting ? (
                <>
                  Jud rahe hain…
                  <Loader2 className="size-4 animate-spin" />
                </>
              ) : (
                <>
                  {startButtonText}
                  <ArrowRight className="size-5 transition-transform duration-200 group-hover:translate-x-1.5" />
                </>
              )}
            </Button>

            <span
              aria-hidden
              className="border-primary/45 text-primary/80 relative flex size-24 -rotate-[9deg] flex-col items-center justify-center gap-0.5 rounded-full border-2 text-center font-mono text-[0.58rem] leading-none font-bold tracking-[0.14em] uppercase"
            >
              <span
                className="border-primary/25 absolute inset-1.5 rounded-full border"
                aria-hidden
              />
              हिंदी
              <span className="text-[0.95rem] tracking-[0.1em]">FIRST</span>
              <span className="text-primary/55 text-[0.5rem] tracking-[0.08em]">निजी बातचीत</span>
            </span>
          </div>

          {/* Trust microcopy */}
          <p className="text-muted-foreground/80 mt-8 max-w-md text-xs leading-5">
            Main doctor nahi hoon — sirf ek saathi. Kisi bhi emergency (saans lene me dikkat, seene
            me dard, tez bleeding) me turant nazdeeki doctor ya aspataal jaayein.
          </p>

          {/* Colophon rule — "Built with" credit uses Simple Icons brand glyphs */}
          <div className="border-foreground/25 text-muted-foreground/60 mt-12 flex flex-wrap items-center justify-between gap-y-2 border-t pt-3 font-mono text-[0.62rem] tracking-[0.2em] uppercase">
            <span>Voice for Bharat · Health Access</span>
            <span className="flex items-center gap-2.5">
              <span className="text-muted-foreground/45">Built with</span>
              <span className="text-foreground/70 tracking-[0.14em]">Murf Falcon</span>
              <span className="text-muted-foreground/30" aria-hidden>
                ·
              </span>
              <LiveKitIcon className="text-muted-foreground/70 size-3.5" />
              <DeepgramIcon className="text-muted-foreground/70 size-3.5" />
              <GeminiIcon className="text-muted-foreground/70 size-3.5" />
            </span>
          </div>
        </div>
      </section>
    </div>
  );
};
