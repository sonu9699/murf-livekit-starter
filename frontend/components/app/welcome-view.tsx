import { ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/shadcn/utils';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

/** Numbered topic index — reads as an editorial contents list, not a chip row. */
const TOPICS = [
  { n: '01', label: 'Symptoms samajhna', dot: 'bg-teal' },
  { n: '02', label: 'Home-care guidance', dot: 'bg-terracotta' },
  { n: '03', label: 'Sarkari schemes', dot: 'bg-indigo' },
];

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="w-full px-6">
      <section className="mx-auto flex max-w-2xl flex-col items-start text-left">
        {/* Masthead — issue-style meta bar */}
        <div className="border-foreground/15 flex w-full items-baseline justify-between border-b pb-4 font-mono text-[0.7rem] tracking-[0.22em] uppercase">
          <span className="text-foreground flex items-center gap-2">
            <span className="bg-primary inline-block size-2 rounded-[2px]" aria-hidden />
            Aarogya Saathi
          </span>
          <span className="text-muted-foreground/70 normal-case">No. 01 — Voice · Bharat</span>
        </div>

        {/* Headline — oversized, off-grid editorial display */}
        <h1 className="font-display mt-8 text-6xl leading-[0.9] font-light tracking-tight text-balance sm:text-7xl md:text-8xl">
          Tabiyat
          <br />
          kaisi hai <span className="text-primary italic">aaj?</span>
        </h1>

        {/* Subhead */}
        <p className="text-muted-foreground mt-6 max-w-md text-base leading-relaxed text-pretty">
          Chhote sheher aur gaon ke liye ek bharosemand health saathi. Hindi ya English — jaise aap
          bolein, waise samjhega.
        </p>

        {/* Topic index — numbered contents list */}
        <ol className="border-foreground/15 mt-9 w-full max-w-md border-t font-mono text-sm">
          {TOPICS.map((item) => (
            <li key={item.n} className="border-foreground/15 flex items-center gap-4 border-b py-3">
              <span className="text-muted-foreground/60 tabular-nums">{item.n}</span>
              <span className={cn('size-1.5 rounded-full', item.dot)} aria-hidden />
              <span className="text-foreground tracking-wide">{item.label}</span>
            </li>
          ))}
        </ol>

        {/* CTA — sharp, mono, editorial (not a soft pill) */}
        <Button
          size="lg"
          onClick={onStartCall}
          className="group text-foreground mt-9 h-14 gap-3 rounded-none px-8 font-mono text-xs font-bold tracking-[0.18em] uppercase transition-transform duration-200 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.99]"
        >
          {startButtonText}
          <ArrowRight className="size-4 transition-transform duration-200 group-hover:translate-x-1" />
        </Button>

        {/* Trust microcopy */}
        <p className="text-muted-foreground/80 mt-6 max-w-md text-xs leading-5">
          Main doctor nahi hoon — sirf ek saathi. Kisi bhi emergency (saans lene me dikkat, seene me
          dard, tez bleeding) me turant nazdeeki doctor ya aspataal jaayein.
        </p>
      </section>

      {/* Editorial footer */}
      <div className="fixed bottom-[max(1.25rem,env(safe-area-inset-bottom))] left-0 hidden w-full items-center justify-center px-6 sm:flex">
        <p className="text-muted-foreground/60 font-mono text-[0.65rem] tracking-[0.2em] uppercase">
          Voice for Bharat · Health Access · Murf Falcon
        </p>
      </div>
    </div>
  );
};
