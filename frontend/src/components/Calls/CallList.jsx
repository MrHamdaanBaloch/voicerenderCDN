import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Search, PhoneCall, Clock, CalendarDays, Bot, User, ArrowUpRight, Activity, History } from 'lucide-react';
import api from '../../services/api';
import { useToast } from '../../hooks/use-toast';

const statusMap = {
  completed: { label: 'Completed', cls: 'badge-active' },
  in_progress: { label: 'Live', cls: 'badge-alert' },
  failed: { label: 'Failed', cls: 'badge-inactive' },
};

const CallList = () => {
  const [calls, setCalls] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { toast } = useToast();

  const fetchCalls = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.calls.getCalls();
      setCalls(response.data);
    } catch (err) {
      setError('Failed to load call history.');
      toast({ title: 'Error', description: 'Failed to load calls.', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => { fetchCalls(); }, [fetchCalls]);

  const filteredCalls = calls.filter(call => {
    const q = searchQuery.toLowerCase();
    return (
      (call.from_number?.toLowerCase() || '').includes(q) ||
      (call.to_number?.toLowerCase() || '').includes(q) ||
      (call.status?.toLowerCase() || '').includes(q) ||
      (call.agent?.name?.toLowerCase() || '').includes(q)
    );
  });

  const fmt = (s) => {
    if (!s && s !== 0) return '—';
    const m = Math.floor(s / 60), r = s % 60;
    return m > 0 ? `${m}m ${r}s` : `${r}s`;
  };

  /* ── Call row ── */
  const CallRow = ({ call, idx }) => {
    const sc = statusMap[call.status] || statusMap.failed;
    return (
      <div
        className="flex items-center gap-4 p-4 border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors group animate-reveal"
        style={{ animationDelay: `${idx * 35}ms` }}
      >
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${call.status === 'completed' ? 'bg-emerald-500/10' : call.status === 'in_progress' ? 'bg-violet-500/15' : 'bg-white/[0.04]'
          }`}>
          <PhoneCall className={`w-4 h-4 ${call.status === 'completed' ? 'text-emerald-400' : call.status === 'in_progress' ? 'text-violet-400' : 'text-zinc-600'
            }`} />
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white font-mono-ui leading-tight">{call.from_number || 'Unknown'}</p>
          <div className="flex items-center gap-2 mt-0.5">
            <Bot className="w-3 h-3 text-zinc-700 shrink-0" />
            <span className="text-[11px] text-zinc-600 truncate">{call.agent?.name || 'AI Agent'}</span>
          </div>
        </div>

        <div className="hidden sm:flex flex-col items-end gap-1 shrink-0">
          <span className={sc.cls}>{sc.label}</span>
          <div className="flex items-center gap-1 text-[10px] text-zinc-700 font-mono-ui">
            <Clock className="w-2.5 h-2.5" />
            {fmt(call.duration_seconds)}
          </div>
        </div>

        <div className="hidden md:flex items-center gap-1 text-[10px] text-zinc-700 shrink-0">
          <CalendarDays className="w-3 h-3" />
          {call.start_time ? new Date(call.start_time).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '—'}
        </div>

        <Link
          to={`/calls/${call.id}`}
          className="flex items-center gap-1 text-[11px] font-semibold text-zinc-600 hover:text-violet-400 transition-colors shrink-0"
        >
          Detail <ArrowUpRight className="w-3 h-3" />
        </Link>
      </div>
    );
  };

  if (loading && calls.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
        <div className="w-12 h-12 rounded-2xl bg-violet-500/10 flex items-center justify-center animate-pulse-slow">
          <History className="w-6 h-6 text-violet-400" />
        </div>
        <p className="text-sm font-semibold text-zinc-500">Loading call history…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-4 text-center">
        <div className="w-12 h-12 rounded-2xl bg-rose-500/10 flex items-center justify-center">
          <Activity className="w-6 h-6 text-rose-400" />
        </div>
        <p className="font-bold text-white">Unable to load calls</p>
        <p className="text-sm text-zinc-600">{error}</p>
        <button onClick={fetchCalls} className="btn-primary mt-2">Retry</button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-reveal">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-heading font-bold text-white tracking-tight">Call History</h1>
        <p className="text-sm text-zinc-600 mt-0.5">Inbound call logs and transcripts from all agents.</p>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600" />
        <input
          placeholder="Search by number, agent, or status…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="form-input pl-9 h-10 w-full"
          disabled={loading}
        />
      </div>

      {/* Table */}
      {filteredCalls.length > 0 ? (
        <div className="card-surface overflow-hidden">
          {/* Column headers */}
          <div className="hidden sm:grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 px-4 py-2.5 border-b border-white/[0.06] text-[9px] font-bold uppercase tracking-[0.15em] text-zinc-700">
            <span>Caller</span>
            <span>Status</span>
            <span>Duration</span>
            <span>Date</span>
            <span />
          </div>
          {filteredCalls.map((call, i) => <CallRow key={call.id} call={call} idx={i} />)}
        </div>
      ) : (
        <div className="card-surface flex flex-col items-center justify-center py-20 text-center">
          <div className="w-14 h-14 rounded-2xl bg-white/[0.04] flex items-center justify-center mb-4 animate-float">
            <History className="w-6 h-6 text-zinc-700" />
          </div>
          <p className="font-bold text-white mb-1">{searchQuery ? 'No results' : 'No calls yet'}</p>
          <p className="text-[13px] text-zinc-600 max-w-xs">
            {searchQuery ? 'Try a different search.' : 'Inbound calls will appear here once your agents start receiving calls.'}
          </p>
        </div>
      )}
    </div>
  );
};

export default CallList;
