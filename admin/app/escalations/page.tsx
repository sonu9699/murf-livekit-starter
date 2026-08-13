'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ActivityIcon,
  ArrowLeftIcon,
  CheckCircle2Icon,
  CheckIcon,
  RotateCcwIcon,
  SearchIcon,
  ShieldAlertIcon,
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/shadcn/utils';

interface Escalation {
  id: string;
  caller_name: string;
  language: string;
  symptoms: string;
  urgency: string;
  followup_method: string;
  summary: string;
  status: 'open' | 'resolved';
  created_at: string;
}

export default function EscalationsPage() {
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'open' | 'resolved'>('all');

  const fetchEscalations = async () => {
    try {
      const res = await fetch('/api/escalations');
      if (res.ok) {
        const data = await res.json();
        setEscalations(data);
      } else {
        toast.error('Failed to load escalation requests');
      }
    } catch (err) {
      console.error(err);
      toast.error('Error connecting to Server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEscalations();
  }, []);

  const toggleStatus = async (id: string, currentStatus: 'open' | 'resolved') => {
    const nextStatus = currentStatus === 'open' ? 'resolved' : 'open';
    try {
      const res = await fetch('/api/escalations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id, status: nextStatus }),
      });
      if (res.ok) {
        const updated = await res.json();
        setEscalations(updated);
        toast.success(`Request ${id} marked as ${nextStatus}`);
      } else {
        toast.error('Failed to update request status');
      }
    } catch (err) {
      console.error(err);
      toast.error('Error updating status');
    }
  };

  const filtered = escalations.filter((esc) => {
    const matchesSearch =
      esc.caller_name.toLowerCase().includes(search.toLowerCase()) ||
      esc.symptoms.toLowerCase().includes(search.toLowerCase()) ||
      esc.id.toLowerCase().includes(search.toLowerCase());

    if (filter === 'all') return matchesSearch;
    return esc.status === filter && matchesSearch;
  });

  const getUrgencyBadge = (urgency: string) => {
    const val = urgency.toLowerCase();
    if (val.includes('emergency')) {
      return (
        <span className="bg-destructive/15 text-destructive border-destructive/20 relative inline-flex animate-pulse items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold">
          <span className="relative flex h-2 w-2">
            <span className="bg-destructive absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"></span>
            <span className="bg-destructive relative inline-flex h-2 w-2 rounded-full"></span>
          </span>
          Emergency
        </span>
      );
    } else if (val.includes('high')) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/20 bg-amber-500/15 px-3 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400">
          High
        </span>
      );
    } else if (val.includes('medium')) {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-yellow-500/20 bg-yellow-500/15 px-3 py-1 text-xs font-semibold text-yellow-600 dark:text-yellow-400">
          Medium
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/20 bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
          Low
        </span>
      );
    }
  };

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleString('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'short',
        timeZone: 'Asia/Kolkata',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="bg-background text-foreground min-h-screen px-4 pt-24 pb-16 md:px-8">
      {/* Top Banner / Navigation */}
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <div className="border-border/60 flex flex-col justify-between gap-4 border-b pb-6 md:flex-row md:items-center">
          <div className="space-y-1">
            <Link
              href="/"
              className="text-muted-foreground hover:text-foreground group mb-2 inline-flex items-center gap-1.5 font-mono text-sm tracking-wider uppercase transition-colors"
            >
              <ArrowLeftIcon className="size-4 transition-transform group-hover:-translate-x-1" />
              Ghar / Home
            </Link>
            <h1 className="font-display flex items-center gap-2.5 text-3xl font-light tracking-tight">
              <ShieldAlertIcon className="text-primary size-8" />
              Human Help Escalations
            </h1>
            <p className="text-muted-foreground text-sm">
              Manage doctor referral and emergency escalation requests created by Pooja.
            </p>
          </div>

          {/* Quick Metrics */}
          <div className="flex gap-4">
            <div className="bg-card border-border/80 min-w-[100px] rounded-2xl border px-5 py-3 text-center shadow-sm">
              <div className="text-destructive text-2xl font-semibold">
                {
                  escalations.filter(
                    (e) => e.status === 'open' && e.urgency.toLowerCase().includes('emergency')
                  ).length
                }
              </div>
              <div className="text-muted-foreground mt-0.5 font-mono text-[10px] tracking-wider uppercase">
                Emergencies
              </div>
            </div>
            <div className="bg-card border-border/80 min-w-[100px] rounded-2xl border px-5 py-3 text-center shadow-sm">
              <div className="text-primary text-2xl font-semibold">
                {escalations.filter((e) => e.status === 'open').length}
              </div>
              <div className="text-muted-foreground mt-0.5 font-mono text-[10px] tracking-wider uppercase">
                Open Tasks
              </div>
            </div>
            <div className="bg-card border-border/80 min-w-[100px] rounded-2xl border px-5 py-3 text-center shadow-sm">
              <div className="text-2xl font-semibold text-emerald-500">
                {escalations.filter((e) => e.status === 'resolved').length}
              </div>
              <div className="text-muted-foreground mt-0.5 font-mono text-[10px] tracking-wider uppercase">
                Resolved
              </div>
            </div>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          {/* Tabs */}
          <div className="bg-muted flex gap-1 self-start rounded-full p-1">
            <button onClick={() => setFilter('all')} className={ariaActive(filter === 'all')}>
              All ({escalations.length})
            </button>
            <button onClick={() => setFilter('open')} className={ariaActive(filter === 'open')}>
              Open ({escalations.filter((e) => e.status === 'open').length})
            </button>
            <button
              onClick={() => setFilter('resolved')}
              className={ariaActive(filter === 'resolved')}
            >
              Resolved ({escalations.filter((e) => e.status === 'resolved').length})
            </button>
          </div>

          {/* Search bar */}
          <div className="relative w-full max-w-md flex-1">
            <SearchIcon className="text-muted-foreground pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by name, symptoms, or reference ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-card border-border/80 placeholder:text-muted-foreground focus:border-primary/50 w-full rounded-full border py-2 pr-4 pl-10 text-sm shadow-sm transition-colors outline-none"
            />
          </div>
        </div>

        {/* Content list */}
        {loading ? (
          <div className="flex flex-col items-center justify-center gap-3 py-20">
            <ActivityIcon className="text-primary size-8 animate-spin" />
            <p className="text-muted-foreground font-mono text-sm">Loading referals...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="border-border/80 bg-card/20 space-y-3 rounded-3xl border border-dashed p-16 text-center shadow-inner">
            <CheckCircle2Icon className="mx-auto size-12 text-emerald-500/80" />
            <h3 className="font-display text-xl font-light">Sab Surakshit Hai!</h3>
            <p className="text-muted-foreground mx-auto max-w-md text-sm">
              {search
                ? 'No referals match your search criteria. Try modifying your search term.'
                : 'No open human help referals. Pooja is successfully assisting patients with basic home care!'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {filtered.map((esc) => (
              <div
                key={esc.id}
                className={cn(
                  'bg-card flex flex-col justify-between rounded-3xl border p-6 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:shadow-md',
                  esc.status === 'resolved'
                    ? 'border-border/40 opacity-75'
                    : esc.urgency.toLowerCase().includes('emergency')
                      ? 'border-destructive/30 ring-destructive/10 ring-1'
                      : 'border-border/80'
                )}
              >
                <div>
                  {/* Card Header */}
                  <div className="border-border/40 mb-4 flex items-center justify-between gap-4 border-b pb-3">
                    <span className="text-muted-foreground bg-muted rounded px-2.5 py-1 font-mono text-xs font-bold">
                      {esc.id}
                    </span>
                    <div className="flex items-center gap-2">
                      {getUrgencyBadge(esc.urgency)}
                      {esc.status === 'resolved' && (
                        <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-500">
                          Resolved
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Card Body */}
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-muted-foreground block font-mono text-[9px] tracking-wider uppercase">
                          Patient Name
                        </span>
                        <span className="text-sm font-semibold">{esc.caller_name}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground block font-mono text-[9px] tracking-wider uppercase">
                          Language & Contact
                        </span>
                        <span className="text-sm font-semibold capitalize">
                          {esc.language} ({esc.followup_method})
                        </span>
                      </div>
                    </div>

                    <div>
                      <span className="text-muted-foreground mb-1 block font-mono text-[9px] tracking-wider uppercase">
                        Symptoms Reported
                      </span>
                      <p className="text-foreground/90 text-sm font-medium italic">
                        &ldquo;{esc.symptoms}&rdquo;
                      </p>
                    </div>

                    <div className="bg-muted/40 border-border/30 space-y-1.5 rounded-2xl border p-4">
                      <span className="text-muted-foreground block font-mono text-[9px] tracking-wider uppercase">
                        Agent Summary
                      </span>
                      <p className="text-muted-foreground text-sm leading-relaxed">{esc.summary}</p>
                    </div>
                  </div>
                </div>

                {/* Card Action Footer */}
                <div className="border-border/40 mt-6 flex items-center justify-between gap-4 border-t pt-4">
                  <span className="text-muted-foreground font-mono text-[10px]">
                    Logged: {formatDate(esc.created_at)}
                  </span>

                  <button
                    onClick={() => toggleStatus(esc.id, esc.status)}
                    className={cn(
                      'inline-flex items-center gap-1.5 rounded-full border px-4 py-2 text-xs font-semibold transition-all active:scale-95',
                      esc.status === 'open'
                        ? 'bg-primary text-primary-foreground hover:bg-primary/95 border-transparent hover:shadow-sm'
                        : 'bg-background text-foreground border-border hover:bg-muted'
                    )}
                  >
                    {esc.status === 'open' ? (
                      <>
                        <CheckIcon className="size-4" />
                        Resolve Case
                      </>
                    ) : (
                      <>
                        <RotateCcwIcon className="size-3.5" />
                        Re-open Case
                      </>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ariaActive(active: boolean) {
  return cn(
    'text-xs font-semibold px-4 py-2 rounded-full transition-all',
    active
      ? 'bg-background text-foreground shadow-sm'
      : 'text-muted-foreground hover:text-foreground'
  );
}
