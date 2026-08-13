import { ArrowRight, House } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface CallEndedViewProps {
  onRestart: () => void;
  onHome: () => void;
}

/**
 * Shown after a call disconnects — an explicit "Call ended" state (one of the
 * five required agent states) instead of snapping straight back to Welcome.
 * Matches the "Aarogya Almanac" landing so the flow reads as one issue.
 */
export const CallEndedView = ({
  onRestart,
  onHome,
  ref,
}: React.ComponentProps<'div'> & CallEndedViewProps) => {
  return (
    <div
      ref={ref}
      className="flex min-h-svh w-full flex-col justify-center px-6 pt-28 pb-20 md:pt-32"
    >
      <section className="mx-auto w-full max-w-3xl">
        {/* Masthead — double-rule, issue-style */}
        <div className="border-foreground/80 flex items-end justify-between border-b-2 pb-2.5 font-mono text-[0.7rem] tracking-[0.2em] uppercase">
          <span className="text-foreground flex items-center gap-2">
            <span className="bg-muted-foreground/50 inline-block size-2.5 rotate-45" aria-hidden />
            आरोग्य साथी
          </span>
          <span className="text-muted-foreground">Baat poori hui</span>
        </div>
        <div className="border-foreground/25 mt-[3px] border-b" />

        {/* Headline */}
        <h1 className="font-display mt-8 text-[clamp(2.75rem,10vw,6rem)] leading-[0.9] font-light tracking-[-0.02em] text-balance">
          Apna khyaal
          <br />
          <span className="text-primary italic">rakhiye.</span>
        </h1>

        {/* Halftone ink strip */}
        <div className="halftone mt-6 h-5 w-40 max-w-full" aria-hidden />

        {/* Reassurance */}
        <p className="text-foreground/80 mt-6 max-w-md text-base leading-relaxed text-pretty">
          Baat khatam hui. Jab bhi tabiyat se judi koi baat poochhni ho, main yahin hun — phir se
          shuru kar sakte hain.
        </p>

        {/* Actions */}
        <div className="mt-9 flex w-full max-w-md flex-col gap-3 sm:flex-row">
          <Button
            size="lg"
            onClick={onRestart}
            className="group text-primary-foreground h-14 flex-1 gap-3 rounded-none px-8 font-mono text-xs font-bold tracking-[0.18em] uppercase transition-transform duration-200 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.99]"
          >
            Phir se baat karein
            <ArrowRight className="size-4 transition-transform duration-200 group-hover:translate-x-1" />
          </Button>
          <Button
            size="lg"
            variant="ghost"
            onClick={onHome}
            className="text-muted-foreground hover:text-foreground h-14 gap-2 rounded-none px-6 font-mono text-xs font-bold tracking-[0.18em] uppercase"
          >
            <House className="size-4" />
            Wapas home
          </Button>
        </div>

        {/* Trust microcopy */}
        <p className="text-muted-foreground/80 mt-8 max-w-md text-xs leading-5">
          Main doctor nahi hoon — sirf ek saathi. Kisi bhi emergency (saans lene me dikkat, seene me
          dard, tez bleeding) me turant nazdeeki doctor ya aspataal jaayein.
        </p>
      </section>
    </div>
  );
};
