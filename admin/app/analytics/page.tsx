'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ActivityIcon,
  ArrowLeftIcon,
  CheckCircle2Icon,
  ClockIcon,
  PhoneCallIcon,
  PhoneOffIcon,
  PhoneOutgoingIcon,
  RefreshCwIcon,
  SearchIcon,
  TrendingUpIcon,
  XCircleIcon,
  UsersIcon,
  BarChart3Icon,
  DownloadIcon,
  FileTextIcon,
  ChevronRightIcon,
  InfoIcon,
  HeartIcon,
  SparklesIcon,
  UserCheckIcon,
  AlertTriangleIcon,
  Trash2Icon,
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/shadcn/utils';

interface CallLog {
  id: string;
  caller_name: string | null;
  status: 'success' | 'failed';
  reason: string;
  duration: number;
  created_at: string;
}

interface Patient {
  caller_id: string;
  name: string;
  language: string;
  age_band: string;
  conditions: string[] | string;
  last_triage: string;
  updated_at: string;
}

type TabType = 'overview' | 'logs' | 'patients' | 'dialer';

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [calls, setCalls] = useState<CallLog[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loadingCalls, setLoadingCalls] = useState(true);
  const [loadingPatients, setLoadingPatients] = useState(false);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'success' | 'failed'>('all');
  const [refreshing, setRefreshing] = useState(false);
  
  // Call Details Drawer State
  const [selectedCall, setSelectedCall] = useState<CallLog | null>(null);

  // Dialer Form State
  const [dialTo, setDialTo] = useState('');
  const [dialName, setDialName] = useState('');
  const [dialScenario, setDialScenario] = useState('vaccination_reminder');
  const [dialBabyAge, setDialBabyAge] = useState('2');
  const [dialing, setDialing] = useState(false);

  const fetchCalls = async (silent = false) => {
    if (!silent) setLoadingCalls(true);
    else setRefreshing(true);
    
    try {
      const res = await fetch('/api/calls');
      if (res.ok) {
        const data = await res.json();
        setCalls(data);
      } else {
        toast.error('Failed to load call analytics');
      }
    } catch (err) {
      console.error(err);
      toast.error('Error connecting to server');
    } finally {
      setLoadingCalls(false);
      setRefreshing(false);
    }
  };

  const fetchPatients = async () => {
    setLoadingPatients(true);
    try {
      const res = await fetch('/api/patients');
      if (res.ok) {
        const data = await res.json();
        setPatients(data);
      } else {
        toast.error('Failed to load patient directory');
      }
    } catch (err) {
      console.error(err);
      toast.error('Error loading patient directory');
    } finally {
      setLoadingPatients(false);
    }
  };

  useEffect(() => {
    fetchCalls();
    fetchPatients();
  }, []);

  const handleRefresh = () => {
    fetchCalls(true);
    fetchPatients();
    toast.success('Stats and profiles refreshed');
  };

  const handleResetDatabase = async () => {
    if (!window.confirm('WARNING: Are you sure you want to permanently delete all call logs, patient profiles, and escalations? This action cannot be undone.')) {
      return;
    }
    
    try {
      const res = await fetch('/api/reset', { method: 'POST' });
      const data = await res.json();
      if (res.ok && data.success) {
        toast.success('Database and logs successfully reset!');
        setCalls([]);
        setPatients([]);
      } else {
        toast.error(data.error || 'Failed to reset data');
      }
    } catch (err) {
      console.error(err);
      toast.error('Error connecting to reset API');
    }
  };

  const triggerOutboundCall = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dialTo) {
      toast.error('Please enter a phone number or SIP ID');
      return;
    }
    setDialing(true);
    try {
      const res = await fetch('/api/outbound', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          to: dialTo,
          name: dialName || 'Rahul',
          scenario: dialScenario,
          babyAge: Number(dialBabyAge) || 2,
        }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        toast.success(`Call initiated successfully to ${dialTo}!`);
        // Switch to logs and refresh
        setTimeout(() => {
          fetchCalls();
          setActiveTab('logs');
        }, 1500);
      } else {
        toast.error(data.error || 'Failed to place call');
      }
    } catch (err) {
      console.error(err);
      toast.error('Network error triggering call');
    } finally {
      setDialing(false);
    }
  };

  const handleQuickCallPatient = (patient: Patient) => {
    setDialTo(patient.name); // Using name for SIP routing or phone if available
    setDialName(patient.name);
    // Auto configure scenario based on patient conditions or last triage
    if (patient.last_triage.toLowerCase().includes('vaccin') || patient.age_band.toLowerCase().includes('month') || patient.age_band.match(/^[0-9]+$/)) {
      setDialScenario('vaccination_reminder');
      const ageMatch = patient.age_band.match(/\d+/);
      if (ageMatch) setDialBabyAge(ageMatch[0]);
    } else {
      setDialScenario('triage_followup');
    }
    setActiveTab('dialer');
    toast.info(`Configured dialer for ${patient.name}`);
  };

  const exportCallsCSV = () => {
    if (calls.length === 0) {
      toast.error('No call logs to export');
      return;
    }
    const headers = ['ID', 'Caller Name', 'Status', 'Duration (secs)', 'Outcome/Reason', 'Timestamp (UTC)'];
    const rows = calls.map(c => [
      c.id,
      c.caller_name || 'Anonymous',
      c.status,
      c.duration,
      `"${c.reason.replace(/"/g, '""')}"`,
      c.created_at
    ]);
    
    const csvContent = 'data:text/csv;charset=utf-8,' 
      + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
      
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `aarogya_call_logs_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success('Call logs exported as CSV');
  };

  // Metrics processing
  const totalCalls = calls.length;
  const successfulCalls = calls.filter((c) => c.status === 'success').length;
  const failedCalls = calls.filter((c) => c.status === 'failed').length;
  const successRate = totalCalls > 0 ? Math.round((successfulCalls / totalCalls) * 100) : 0;
  const averageDuration = totalCalls > 0 
    ? Math.round(calls.reduce((acc, c) => acc + c.duration, 0) / totalCalls) 
    : 0;

  // Chart data calculations (Duration categories)
  const durationGroups = {
    short: calls.filter(c => c.duration < 15).length,
    medium: calls.filter(c => c.duration >= 15 && c.duration < 45).length,
    long: calls.filter(c => c.duration >= 45 && c.duration < 120).length,
    extended: calls.filter(c => c.duration >= 120).length,
  };
  const maxDurationCount = Math.max(...Object.values(durationGroups), 1);

  // Chart data calculations (Call hours)
  const hourlyCounts = Array(24).fill(0);
  calls.forEach(c => {
    try {
      const hr = new Date(c.created_at).getHours();
      if (hr >= 0 && hr < 24) hourlyCounts[hr]++;
    } catch {}
  });
  const maxHourlyCount = Math.max(...hourlyCounts, 1);

  const filteredCalls = calls.filter((call) => {
    const name = call.caller_name || 'anonymous';
    const matchesSearch =
      name.toLowerCase().includes(search.toLowerCase()) ||
      call.reason.toLowerCase().includes(search.toLowerCase()) ||
      call.id.toLowerCase().includes(search.toLowerCase());

    if (filter === 'all') return matchesSearch;
    return call.status === filter && matchesSearch;
  });

  const filteredPatients = patients.filter((pat) => {
    const matchesSearch =
      pat.name.toLowerCase().includes(search.toLowerCase()) ||
      pat.language.toLowerCase().includes(search.toLowerCase()) ||
      (Array.isArray(pat.conditions) ? pat.conditions.join(' ') : String(pat.conditions)).toLowerCase().includes(search.toLowerCase()) ||
      pat.last_triage.toLowerCase().includes(search.toLowerCase());
    return matchesSearch;
  });

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

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  // SVG circular progress math
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (successRate / 100) * circumference;

  return (
    <div className="bg-background text-foreground min-h-screen px-4 pt-24 pb-16 md:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        
        {/* Top Header & Navigation */}
        <div className="border-border/60 flex flex-col justify-between gap-4 border-b pb-6 md:flex-row md:items-end">
          <div className="space-y-1">
            <Link
              href="/"
              className="text-muted-foreground hover:text-foreground group mb-2 inline-flex items-center gap-1.5 font-mono text-sm tracking-wider uppercase transition-colors"
            >
              <ArrowLeftIcon className="size-4 transition-transform group-hover:-translate-x-1" />
              Ghar / Home
            </Link>
            <h1 className="font-display flex items-center gap-3 text-3xl font-light tracking-tight">
              <PhoneCallIcon className="text-primary size-8 animate-pulse" />
              Aarogya Saathi Admin Hub
            </h1>
            <p className="text-muted-foreground text-sm">
              Manage patient memory profiles, view detailed analytics, and trigger outbound calls in real-time.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleRefresh}
              disabled={refreshing || loadingCalls}
              className="border-border/80 hover:bg-primary/10 flex items-center gap-2 rounded-full border bg-card px-4 py-2 font-mono text-xs font-semibold tracking-wider uppercase transition-all hover:shadow-sm active:scale-95 disabled:opacity-55"
            >
              <RefreshCwIcon className={cn('size-3.5', refreshing && 'animate-spin')} />
              Refresh Data
            </button>
            
            <button
              onClick={exportCallsCSV}
              className="border-border/80 hover:bg-primary/10 flex items-center gap-2 rounded-full border bg-card px-4 py-2 font-mono text-xs font-semibold tracking-wider uppercase transition-all hover:shadow-sm active:scale-95"
            >
              <DownloadIcon className="size-3.5" />
              CSV Export
            </button>

            <button
              onClick={handleResetDatabase}
              className="border-destructive/40 text-destructive hover:bg-destructive/10 flex items-center gap-2 rounded-full border bg-card px-4 py-2 font-mono text-xs font-semibold tracking-wider uppercase transition-all hover:shadow-sm active:scale-95"
            >
              <Trash2Icon className="size-3.5" />
              Reset Data
            </button>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-border/40 gap-1 overflow-x-auto pb-px">
          <button
            onClick={() => { setActiveTab('overview'); setSearch(''); }}
            className={cn(
              "px-5 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2 whitespace-nowrap",
              activeTab === 'overview'
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
            )}
          >
            <BarChart3Icon className="size-4" />
            Overview Dashboard
          </button>
          
          <button
            onClick={() => { setActiveTab('logs'); setSearch(''); }}
            className={cn(
              "px-5 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2 whitespace-nowrap",
              activeTab === 'logs'
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
            )}
          >
            <FileTextIcon className="size-4" />
            Call Logs ({calls.length})
          </button>

          <button
            onClick={() => { setActiveTab('patients'); setSearch(''); }}
            className={cn(
              "px-5 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2 whitespace-nowrap",
              activeTab === 'patients'
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
            )}
          >
            <UsersIcon className="size-4" />
            Patient Directory ({patients.length})
          </button>

          <button
            onClick={() => { setActiveTab('dialer'); setSearch(''); }}
            className={cn(
              "px-5 py-3 text-sm font-medium border-b-2 transition-all flex items-center gap-2 whitespace-nowrap",
              activeTab === 'dialer'
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
            )}
          >
            <PhoneOutgoingIcon className="size-4" />
            Outbound Dialer
          </button>
        </div>

        {/* ==================== TAB CONTENT: OVERVIEW ==================== */}
        {activeTab === 'overview' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* Top Cards Grid */}
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <div className="bg-card/50 backdrop-blur-md border-border/80 flex flex-col justify-between rounded-2xl border p-5 shadow-sm">
                <div className="text-muted-foreground font-mono text-[10px] tracking-wider uppercase">
                  Total Agent Interactions
                </div>
                <div className="text-foreground text-3xl font-bold mt-2">{totalCalls}</div>
                <div className="text-muted-foreground text-xs mt-1 font-mono">
                  Incoming & Outbound
                </div>
              </div>
              
              <div className="bg-card/50 backdrop-blur-md border-border/80 flex flex-col justify-between rounded-2xl border p-5 shadow-sm">
                <div className="text-emerald-500 font-mono text-[10px] tracking-wider uppercase">
                  Successful Outcomes
                </div>
                <div className="text-emerald-500 text-3xl font-bold mt-2">{successfulCalls}</div>
                <div className="text-muted-foreground text-xs mt-1 font-mono">
                  Full advice given
                </div>
              </div>
              
              <div className="bg-card/50 backdrop-blur-md border-border/80 flex flex-col justify-between rounded-2xl border p-5 shadow-sm">
                <div className="text-muted-foreground font-mono text-[10px] tracking-wider uppercase">
                  Patient Memory Profiles
                </div>
                <div className="text-foreground text-3xl font-bold mt-2">{patients.length}</div>
                <div className="text-muted-foreground text-xs mt-1 font-mono">
                  Persisted SQLite records
                </div>
              </div>

              <div className="bg-card/50 backdrop-blur-md border-border/80 flex flex-col justify-between rounded-2xl border p-5 shadow-sm">
                <div className="text-teal-600 dark:text-teal-400 font-mono text-[10px] tracking-wider uppercase">
                  Avg Interaction Time
                </div>
                <div className="text-teal-600 dark:text-teal-400 text-3xl font-bold mt-2">
                  {formatDuration(averageDuration)}
                </div>
                <div className="text-muted-foreground text-xs mt-1 font-mono">
                  Across all sessions
                </div>
              </div>
            </div>

            {/* Visual Charts Section */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              {/* Chart 1: Success Rate Donut */}
              <div className="bg-card/40 border border-border/80 rounded-3xl p-6 flex flex-col items-center justify-between min-h-[300px]">
                <div className="w-full flex items-center justify-between mb-4">
                  <h3 className="font-medium text-sm">Interaction Success Rate</h3>
                  <SparklesIcon className="size-4 text-emerald-500" />
                </div>
                
                <div className="relative flex items-center justify-center">
                  <svg className="w-36 h-36 transform -rotate-90">
                    {/* Background Circle */}
                    <circle
                      cx="72"
                      cy="72"
                      r={radius}
                      className="stroke-muted/30"
                      strokeWidth="10"
                      fill="transparent"
                    />
                    {/* Foreground Success Circle */}
                    <circle
                      cx="72"
                      cy="72"
                      r={radius}
                      className="stroke-emerald-500 transition-all duration-1000 ease-out"
                      strokeWidth="10"
                      strokeDasharray={circumference}
                      strokeDashoffset={strokeDashoffset}
                      strokeLinecap="round"
                      fill="transparent"
                    />
                  </svg>
                  <div className="absolute text-center">
                    <span className="text-3xl font-bold">{successRate}%</span>
                    <p className="text-[10px] text-muted-foreground font-mono uppercase tracking-wider">Success</p>
                  </div>
                </div>

                <div className="text-center text-xs text-muted-foreground mt-4 px-2">
                  Percentage of calls where Aarogya Saathi resolved patient triage or scheduled follow-ups without dropouts.
                </div>
              </div>

              {/* Chart 2: Call Duration Bar Chart */}
              <div className="bg-card/40 border border-border/80 rounded-3xl p-6 flex flex-col justify-between min-h-[300px]">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-medium text-sm">Duration Distribution</h3>
                  <ClockIcon className="size-4 text-primary" />
                </div>

                <div className="flex items-end justify-between gap-3 h-40 px-2">
                  {/* Short */}
                  <div className="flex flex-col items-center flex-1 gap-2">
                    <span className="text-[10px] font-mono font-bold">{durationGroups.short}</span>
                    <div 
                      className="bg-muted hover:bg-primary/40 rounded-t-md w-full transition-all duration-500"
                      style={{ height: `${(durationGroups.short / maxDurationCount) * 110}px` }}
                    />
                    <span className="text-[10px] text-muted-foreground whitespace-nowrap">&lt;15s</span>
                  </div>

                  {/* Medium */}
                  <div className="flex flex-col items-center flex-1 gap-2">
                    <span className="text-[10px] font-mono font-bold">{durationGroups.medium}</span>
                    <div 
                      className="bg-primary/60 hover:bg-primary/80 rounded-t-md w-full transition-all duration-500"
                      style={{ height: `${(durationGroups.medium / maxDurationCount) * 110}px` }}
                    />
                    <span className="text-[10px] text-muted-foreground whitespace-nowrap">15s-45s</span>
                  </div>

                  {/* Long */}
                  <div className="flex flex-col items-center flex-1 gap-2">
                    <span className="text-[10px] font-mono font-bold">{durationGroups.long}</span>
                    <div 
                      className="bg-primary hover:bg-primary/95 rounded-t-md w-full transition-all duration-500"
                      style={{ height: `${(durationGroups.long / maxDurationCount) * 110}px` }}
                    />
                    <span className="text-[10px] text-muted-foreground whitespace-nowrap">45s-2m</span>
                  </div>

                  {/* Extended */}
                  <div className="flex flex-col items-center flex-1 gap-2">
                    <span className="text-[10px] font-mono font-bold">{durationGroups.extended}</span>
                    <div 
                      className="bg-indigo-600 dark:bg-indigo-400 rounded-t-md w-full transition-all duration-500"
                      style={{ height: `${(durationGroups.extended / maxDurationCount) * 110}px` }}
                    />
                    <span className="text-[10px] text-muted-foreground whitespace-nowrap">&gt;2m</span>
                  </div>
                </div>

                <div className="text-xs text-muted-foreground mt-4 text-center">
                  Overview of patient engagement sessions. Long calls represent detailed symptoms triage.
                </div>
              </div>

              {/* Chart 3: Call Volume Hourly Trend */}
              <div className="bg-card/40 border border-border/80 rounded-3xl p-6 flex flex-col justify-between min-h-[300px]">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-medium text-sm">Hourly Interaction Volume</h3>
                  <TrendingUpIcon className="size-4 text-indigo-500" />
                </div>

                {/* SVG Line / Bar chart of 24 hours */}
                <div className="flex items-end justify-between h-40 border-b border-border/40 pb-1 px-1">
                  {hourlyCounts.map((count, hr) => (
                    <div key={hr} className="flex flex-col items-center flex-1 h-full justify-end group relative">
                      {/* Tooltip on hover */}
                      <span className="absolute -top-6 hidden group-hover:block bg-popover text-popover-foreground border border-border rounded text-[9px] px-1 py-0.5 z-10 font-mono shadow-sm">
                        {hr}:00 ({count})
                      </span>
                      <div 
                        className={cn(
                          "w-1 rounded-t-full transition-all duration-500",
                          count > 0 ? "bg-primary" : "bg-muted/40"
                        )}
                        style={{ height: `${(count / maxHourlyCount) * 100}%` }}
                      />
                    </div>
                  ))}
                </div>

                {/* X Axis Labels */}
                <div className="flex justify-between text-[9px] text-muted-foreground font-mono px-1">
                  <span>12 AM</span>
                  <span>6 AM</span>
                  <span>12 PM</span>
                  <span>6 PM</span>
                  <span>11 PM</span>
                </div>

                <div className="text-xs text-muted-foreground mt-4 text-center">
                  Hourly active calling patterns on Aarogya Saathi. Shows system load and peak triage times.
                </div>
              </div>
            </div>

            {/* Health insights list */}
            <div className="bg-card/30 border border-border/80 rounded-3xl p-6">
              <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                <HeartIcon className="size-4 text-destructive" />
                Aarogya Saathi Health Insights & Medical Summary
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="border border-border/60 rounded-2xl p-4 bg-background/50">
                  <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider block">Top Reported Conditions</span>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {patients.length > 0 ? (
                      Array.from(new Set(patients.flatMap(p => Array.isArray(p.conditions) ? p.conditions : []))).slice(0, 5).map((cond, idx) => (
                        <span key={idx} className="px-2 py-0.5 bg-primary/10 border border-primary/20 text-primary rounded-full text-xs font-medium">
                          {cond}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-muted-foreground italic">No patient data recorded</span>
                    )}
                  </div>
                </div>

                <div className="border border-border/60 rounded-2xl p-4 bg-background/50">
                  <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider block">Primary Languages spoken</span>
                  <div className="mt-2 space-y-1">
                    {Array.from(new Set(patients.map(p => p.language).filter(Boolean))).slice(0, 3).map((lang, idx) => {
                      const count = patients.filter(p => p.language === lang).length;
                      const percentage = Math.round((count / patients.length) * 100);
                      return (
                        <div key={idx} className="flex justify-between items-center text-xs">
                          <span className="font-medium">{lang}</span>
                          <span className="text-muted-foreground font-mono">{percentage}% ({count})</span>
                        </div>
                      );
                    })}
                    {patients.length === 0 && <span className="text-xs text-muted-foreground italic">No languages logged</span>}
                  </div>
                </div>

                <div className="border border-border/60 rounded-2xl p-4 bg-background/50">
                  <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider block">Active Triage Case Status</span>
                  <div className="mt-2 space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="flex items-center gap-1"><UserCheckIcon className="size-3.5 text-emerald-500" /> Monitored Patients</span>
                      <span className="font-mono font-bold">{patients.length}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="flex items-center gap-1"><AlertTriangleIcon className="size-3.5 text-destructive animate-pulse" /> Emergencies Triaged</span>
                      <span className="font-mono font-bold text-destructive">
                        {calls.filter(c => c.reason.toLowerCase().includes('emergency') || c.reason.toLowerCase().includes('escalat')).length}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ==================== TAB CONTENT: CALL LOGS ==================== */}
        {activeTab === 'logs' && (
          <div className="space-y-4 animate-in fade-in duration-200">
            {/* Search and Filters */}
            <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <div className="bg-muted flex gap-1 self-start rounded-full p-1">
                <button onClick={() => setFilter('all')} className={ariaActive(filter === 'all')}>
                  All ({totalCalls})
                </button>
                <button onClick={() => setFilter('success')} className={ariaActive(filter === 'success')}>
                  Successful ({successfulCalls})
                </button>
                <button onClick={() => setFilter('failed')} className={ariaActive(filter === 'failed')}>
                  Failed ({failedCalls})
                </button>
              </div>

              <div className="relative w-full max-w-md flex-1">
                <SearchIcon className="text-muted-foreground pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by caller name, details, or room ID..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="bg-card border-border/80 placeholder:text-muted-foreground focus:border-primary/50 w-full rounded-full border py-2 pr-4 pl-10 text-sm shadow-sm transition-colors outline-none"
                />
              </div>
            </div>

            {/* Logs List Table */}
            {loadingCalls ? (
              <div className="flex flex-col items-center justify-center gap-3 py-20">
                <ActivityIcon className="text-primary size-8 animate-spin" />
                <p className="text-muted-foreground font-mono text-sm">Loading call logs...</p>
              </div>
            ) : filteredCalls.length === 0 ? (
              <div className="border-border/80 bg-card/20 space-y-3 rounded-3xl border border-dashed p-16 text-center shadow-inner">
                <PhoneOffIcon className="mx-auto size-12 text-muted-foreground/60" />
                <h3 className="font-display text-xl font-light">No Call Logs Found</h3>
                <p className="text-muted-foreground mx-auto max-w-md text-sm">
                  {search
                    ? 'No calls match your search query. Try another term.'
                    : 'No voice assistant calls logged yet.'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto rounded-2xl border border-border/80 bg-card shadow-sm">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-border/80 font-mono text-[9px] tracking-wider uppercase text-muted-foreground bg-muted/40">
                      <th className="px-6 py-4">Status</th>
                      <th className="px-6 py-4">Caller Name</th>
                      <th className="px-6 py-4">Duration</th>
                      <th className="px-6 py-4">Outcome / Diagnostic Reasons</th>
                      <th className="px-6 py-4">Time (IST)</th>
                      <th className="px-6 py-4 text-right">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40 text-sm">
                    {filteredCalls.map((call) => (
                      <tr key={call.id} className="hover:bg-muted/10 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          {call.status === 'success' ? (
                            <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                              <CheckCircle2Icon className="size-3.5" />
                              Success
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-full border border-destructive/20 bg-destructive/10 px-2.5 py-0.5 text-xs font-semibold text-destructive">
                              <XCircleIcon className="size-3.5" />
                              Failed
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 font-semibold whitespace-nowrap">
                          {call.caller_name || (
                            <span className="text-muted-foreground font-normal italic">Anonymous</span>
                          )}
                        </td>
                        <td className="px-6 py-4 font-mono text-xs whitespace-nowrap">
                          {formatDuration(call.duration)}
                        </td>
                        <td className="px-6 py-4 text-muted-foreground text-xs leading-relaxed max-w-xs md:max-w-md truncate hover:text-clip hover:whitespace-normal">
                          {call.reason}
                        </td>
                        <td className="px-6 py-4 text-muted-foreground font-mono text-xs whitespace-nowrap">
                          {formatDate(call.created_at)}
                        </td>
                        <td className="px-6 py-4 text-right whitespace-nowrap">
                          <button
                            onClick={() => setSelectedCall(call)}
                            className="text-primary hover:text-primary-hover font-mono text-xs font-semibold inline-flex items-center gap-0.5 hover:underline"
                          >
                            View
                            <ChevronRightIcon className="size-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ==================== TAB CONTENT: PATIENT DIRECTORY ==================== */}
        {activeTab === 'patients' && (
          <div className="space-y-4 animate-in fade-in duration-200">
            {/* Search and Filters */}
            <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
              <h3 className="text-sm font-medium">Patient Directory Records (SQLite Persisted)</h3>
              
              <div className="relative w-full max-w-md flex-1">
                <SearchIcon className="text-muted-foreground pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search by name, symptoms, or language..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="bg-card border-border/80 placeholder:text-muted-foreground focus:border-primary/50 w-full rounded-full border py-2 pr-4 pl-10 text-sm shadow-sm transition-colors outline-none"
                />
              </div>
            </div>

            {loadingPatients ? (
              <div className="flex flex-col items-center justify-center gap-3 py-20">
                <ActivityIcon className="text-primary size-8 animate-spin" />
                <p className="text-muted-foreground font-mono text-sm">Querying patient profiles...</p>
              </div>
            ) : filteredPatients.length === 0 ? (
              <div className="border-border/80 bg-card/20 space-y-3 rounded-3xl border border-dashed p-16 text-center shadow-inner">
                <UsersIcon className="mx-auto size-12 text-muted-foreground/60" />
                <h3 className="font-display text-xl font-light">No Patients Registered</h3>
                <p className="text-muted-foreground mx-auto max-w-md text-sm">
                  {search
                    ? 'No patient records match your search parameters.'
                    : 'Aarogya Saathi database is empty. Profiles are created when callers introduce themselves by name.'}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredPatients.map((pat) => (
                  <div key={pat.caller_id} className="bg-card border border-border/80 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start">
                        <div className="space-y-1">
                          <h4 className="font-semibold text-lg">{pat.name}</h4>
                          <div className="flex flex-wrap gap-2 text-xs">
                            <span className="bg-muted px-2 py-0.5 rounded-md text-muted-foreground font-mono">
                              Language: {pat.language || 'Not set'}
                            </span>
                            <span className="bg-muted px-2 py-0.5 rounded-md text-muted-foreground font-mono">
                              Age Band: {pat.age_band || 'Unknown'}
                            </span>
                          </div>
                        </div>
                        
                        <button
                          onClick={() => handleQuickCallPatient(pat)}
                          className="bg-primary hover:bg-primary-hover text-white rounded-full p-2.5 transition-colors active:scale-95 flex items-center justify-center shadow-sm"
                          title={`Quick Call ${pat.name}`}
                        >
                          <PhoneOutgoingIcon className="size-4" />
                        </button>
                      </div>

                      {/* Conditions list */}
                      <div className="mt-4">
                        <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider block">Diagnosed Conditions</span>
                        <div className="mt-1 flex flex-wrap gap-1">
                          {(() => {
                            const conds = Array.isArray(pat.conditions) 
                              ? pat.conditions 
                              : JSON.parse(typeof pat.conditions === 'string' ? pat.conditions : '[]');
                            
                            return conds.length > 0 ? (
                              conds.map((c: string, i: number) => (
                                <span key={i} className="px-2.5 py-0.5 bg-destructive/10 text-destructive border border-destructive/20 text-xs font-semibold rounded-full">
                                  {c}
                                </span>
                              ))
                            ) : (
                              <span className="text-xs text-muted-foreground italic">No underlying conditions flagged</span>
                            );
                          })()}
                        </div>
                      </div>

                      {/* Last Triage outcome */}
                      <div className="mt-4 border-t border-border/40 pt-3">
                        <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider block">Last Advised Triage Outcome</span>
                        <p className="text-xs text-foreground/80 mt-1 leading-relaxed italic bg-muted/40 p-2 rounded-xl border border-border/20">
                          "{pat.last_triage || 'No advice recorded'}"
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 flex justify-between items-center text-[10px] text-muted-foreground font-mono border-t border-border/40 pt-3">
                      <span>Ref ID: {pat.caller_id}</span>
                      <span>Updated: {formatDate(pat.updated_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ==================== TAB CONTENT: OUTBOUND DIALER ==================== */}
        {activeTab === 'dialer' && (
          <div className="max-w-xl mx-auto w-full animate-in fade-in duration-200">
            <div className="bg-card border border-border/80 rounded-3xl p-6 md:p-8 shadow-md">
              <div className="flex items-center gap-2.5 mb-6">
                <PhoneOutgoingIcon className="text-primary size-6 animate-pulse" />
                <div>
                  <h3 className="font-semibold text-lg">Initiate Outbound Call Campaign</h3>
                  <p className="text-xs text-muted-foreground">Places an outbound SIP/Phone call. The voice assistant Aarogya Saathi will join and speak to the patient.</p>
                </div>
              </div>

              <form onSubmit={triggerOutboundCall} className="space-y-4">
                <div className="space-y-1.5">
                  <label htmlFor="dial-to" className="text-xs font-mono text-muted-foreground uppercase tracking-wider block">
                    To (Phone number / SIP Address)
                  </label>
                  <input
                    type="text"
                    id="dial-to"
                    placeholder="e.g. +91XXXXXXXXXX or sip_username"
                    value={dialTo}
                    onChange={(e) => setDialTo(e.target.value)}
                    required
                    className="w-full bg-background border border-border/80 focus:border-primary/50 py-2.5 px-4 rounded-xl text-sm shadow-sm outline-none transition-colors"
                  />
                  <span className="text-[10px] text-muted-foreground block font-mono">
                    Ensure the phone matches standard format or the SIP ID matches registered trunk configuration.
                  </span>
                </div>

                <div className="space-y-1.5">
                  <label htmlFor="dial-name" className="text-xs font-mono text-muted-foreground uppercase tracking-wider block">
                    Patient Name
                  </label>
                  <input
                    type="text"
                    id="dial-name"
                    placeholder="e.g. Rahul Kumar"
                    value={dialName}
                    onChange={(e) => setDialName(e.target.value)}
                    className="w-full bg-background border border-border/80 focus:border-primary/50 py-2.5 px-4 rounded-xl text-sm shadow-sm outline-none transition-colors"
                  />
                </div>

                <div className="space-y-1.5">
                  <label htmlFor="dial-scenario" className="text-xs font-mono text-muted-foreground uppercase tracking-wider block">
                    Assistant Dialogue Scenario
                  </label>
                  <select
                    id="dial-scenario"
                    value={dialScenario}
                    onChange={(e) => setDialScenario(e.target.value)}
                    className="w-full bg-background border border-border/80 focus:border-primary/50 py-2.5 px-4 rounded-xl text-sm shadow-sm outline-none transition-colors"
                  >
                    <option value="vaccination_reminder">Vaccination Reminder (Immunization follow-up)</option>
                    <option value="triage_followup">Triage Follow-up (Check-in on previous symptom advice)</option>
                  </select>
                </div>

                {dialScenario === 'vaccination_reminder' && (
                  <div className="space-y-1.5">
                    <label htmlFor="dial-baby-age" className="text-xs font-mono text-muted-foreground uppercase tracking-wider block">
                      Baby's Age (in months)
                    </label>
                    <input
                      type="number"
                      id="dial-baby-age"
                      min="1"
                      max="48"
                      value={dialBabyAge}
                      onChange={(e) => setDialBabyAge(e.target.value)}
                      className="w-full bg-background border border-border/80 focus:border-primary/50 py-2.5 px-4 rounded-xl text-sm shadow-sm outline-none transition-colors"
                    />
                  </div>
                )}

                <div className="pt-4 border-t border-border/40">
                  <button
                    type="submit"
                    disabled={dialing}
                    className="w-full bg-primary hover:bg-primary/90 text-white font-semibold py-3 rounded-xl transition-all shadow-sm active:scale-[0.98] flex items-center justify-center gap-2 disabled:opacity-60"
                  >
                    {dialing ? (
                      <>
                        <ActivityIcon className="size-4 animate-spin" />
                        Triggering call...
                      </>
                    ) : (
                      <>
                        <PhoneOutgoingIcon className="size-4" />
                        Call Patient / Dial Now
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ==================== CALL DETAIL MODAL/SIDEBAR DRAWER ==================== */}
        {selectedCall && (
          <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-sm transition-opacity animate-in fade-in">
            {/* Click outside to close */}
            <div className="flex-1" onClick={() => setSelectedCall(null)} />
            
            {/* Drawer container */}
            <div className="bg-card w-full max-w-lg h-full border-l border-border/60 shadow-2xl p-6 md:p-8 flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-300">
              <div className="space-y-6">
                <div className="flex justify-between items-start border-b border-border/40 pb-4">
                  <div className="space-y-1">
                    <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">
                      Call Session Details
                    </span>
                    <h3 className="font-bold text-xl">{selectedCall.caller_name || 'Anonymous Patient'}</h3>
                  </div>
                  <button
                    onClick={() => setSelectedCall(null)}
                    className="border border-border/80 hover:bg-muted/80 rounded-full p-1.5 transition-colors"
                  >
                    <XCircleIcon className="size-5 text-muted-foreground" />
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-muted/40 p-4 rounded-xl border border-border/20">
                    <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider block">Outcome Status</span>
                    <div className="mt-1">
                      {selectedCall.status === 'success' ? (
                        <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                          <CheckCircle2Icon className="size-3.5" />
                          Success
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full border border-destructive/20 bg-destructive/10 px-2.5 py-0.5 text-xs font-semibold text-destructive">
                          <XCircleIcon className="size-3.5" />
                          Failed
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="bg-muted/40 p-4 rounded-xl border border-border/20">
                    <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider block">Call Duration</span>
                    <span className="font-mono text-sm font-semibold mt-1 block">{formatDuration(selectedCall.duration)}</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider block">Timestamp (IST)</span>
                  <span className="text-sm font-medium block">{formatDate(selectedCall.created_at)}</span>
                </div>

                <div className="space-y-2">
                  <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider block">LiveKit Room / Identity ID</span>
                  <span className="text-xs font-mono bg-muted/60 p-2.5 border border-border/30 rounded-lg block overflow-x-auto select-all">
                    {selectedCall.id}
                  </span>
                </div>

                <div className="space-y-2 border-t border-border/40 pt-4">
                  <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider block">Outcome summary / Call notes</span>
                  <p className="text-sm text-foreground/80 leading-relaxed bg-primary/5 border border-primary/10 p-4 rounded-xl">
                    {selectedCall.reason}
                  </p>
                </div>
              </div>

              <div className="border-t border-border/40 pt-6 mt-8 flex flex-col gap-2">
                {selectedCall.caller_name && (
                  <button
                    onClick={() => {
                      const matchedPatient = patients.find(p => p.name.toLowerCase() === selectedCall.caller_name?.toLowerCase());
                      if (matchedPatient) {
                        handleQuickCallPatient(matchedPatient);
                      } else {
                        setDialTo(selectedCall.caller_name || '');
                        setDialName(selectedCall.caller_name || '');
                        setActiveTab('dialer');
                      }
                      setSelectedCall(null);
                    }}
                    className="w-full bg-primary hover:bg-primary/95 text-white font-semibold py-2.5 rounded-xl transition-all shadow-sm flex items-center justify-center gap-1.5 text-sm"
                  >
                    <PhoneOutgoingIcon className="size-4" />
                    Re-engage Outbound call to {selectedCall.caller_name}
                  </button>
                )}
                <button
                  onClick={() => setSelectedCall(null)}
                  className="w-full border border-border/80 hover:bg-muted text-foreground font-semibold py-2.5 rounded-xl transition-all text-sm"
                >
                  Close panel
                </button>
              </div>
            </div>
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
