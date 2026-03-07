import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Skeleton } from '../ui/skeleton';
import {
  Phone, Clock, Activity, PhoneCall, CheckCircle, ArrowUpRight,
  Bot, Zap, TrendingUp, Users, AlertCircle, BarChart3, Plus
} from 'lucide-react';
import api from '../../services/api';
import { getErrorMessage } from '../../lib/utils';
import { useToast } from '../../hooks/use-toast';
import { useCountUp } from '../../hooks/useCountUp';

/* ── Animated number ── */
const AnimatedValue = ({ value, suffix = '', prefix = '' }) => {
  const num = typeof value === 'string' ? parseFloat(value.replace(/,/g, '')) : value;
  const animated = useCountUp(isNaN(num) ? 0 : num, 2200, { suffix, prefix });
  if (isNaN(num)) return <span>{prefix}{value}{suffix}</span>;
  return <span>{animated}</span>;
};

/* ── KPI Stat Card ── */
const StatCard = ({ title, value, numericValue, subtitle, icon: Icon, trend, colorClass = 'text-violet-400', bgClass = 'bg-violet-500/10', suffix = '', prefix = '', delay = 0 }) => (
  <div
    className="stat-card hover-glow-violet transition-all duration-300 group"
    style={{ animationDelay: `${delay}ms` }}
  >
    <div className="flex items-center justify-between">
      <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-zinc-600">{title}</span>
      <div className={`w-8 h-8 rounded-lg ${bgClass} flex items-center justify-center group-hover:scale-110 transition-transform`}>
        <Icon className={`w-4 h-4 ${colorClass}`} />
      </div>
    </div>
    <div className="mt-1">
      <div className="text-3xl font-heading font-bold text-white tracking-tight">
        <AnimatedValue value={numericValue !== undefined ? numericValue : value} suffix={suffix} prefix={prefix} />
      </div>
      {subtitle && (
        <p className="text-[11px] text-zinc-600 mt-1 flex items-center gap-1.5">
          {trend !== undefined && (
            <span className={`font-bold ${trend >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
            </span>
          )}
          {subtitle}
        </p>
      )}
    </div>
  </div>
);

/* ── Skeleton ── */
const SkeletonStatCard = () => (
  <div className="stat-card space-y-3">
    <div className="flex justify-between">
      <div className="h-2.5 w-24 rounded bg-white/[0.06] animate-shimmer" />
      <div className="h-8 w-8 rounded-lg bg-white/[0.04] animate-shimmer" />
    </div>
    <div className="h-8 w-28 rounded bg-white/[0.06] animate-shimmer" />
    <div className="h-2.5 w-36 rounded bg-white/[0.04] animate-shimmer" />
  </div>
);

/* ── Call status badge ── */
const statusConfig = {
  completed: { label: 'Completed', className: 'badge-active' },
  in_progress: { label: 'Live', className: 'badge-alert' },
  failed: { label: 'Failed', className: 'badge-inactive' },
};

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const fetch = async () => {
      try {
        const [sR, aR] = await Promise.all([api.calls.getDashboardStats(), api.agents.getAgents()]);
        setStats(sR.data);
        setAgents(aR.data);
      } catch (err) {
        toast({ title: 'Error loading dashboard', description: getErrorMessage(err), variant: 'destructive' });
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [toast]);

  const dash = stats || { totalCalls: 0, successRate: 0, avgCallDuration: '0:00', activeCalls: 0, recentCalls: [], monthlyCallVolume: [] };
  const activeAgents = agents.filter(a => a.is_active);

  if (loading) {
    return (
      <div className="space-y-6 animate-reveal">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <SkeletonStatCard key={i} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 stat-card h-72 animate-shimmer" />
          <div className="stat-card h-72 animate-shimmer" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* ── Page Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white tracking-tight">Operations Overview</h1>
          <p className="text-sm text-zinc-600 mt-1">Your inbound AI infrastructure at a glance</p>
        </div>
        <Link
          to="/agents/new"
          className="btn-primary self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          New Agent
        </Link>
      </div>

      {/* ── KPI Stats ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Calls Handled"
          value={dash.totalCalls.toLocaleString()}
          numericValue={dash.totalCalls}
          subtitle="vs. last 30 days"
          icon={PhoneCall}
          trend={12}
          delay={0}
        />
        <StatCard
          title="Resolution Rate"
          value={`${dash.successRate}%`}
          numericValue={dash.successRate}
          suffix="%"
          subtitle="First Contact Resolution"
          icon={CheckCircle}
          trend={5}
          colorClass="text-emerald-400"
          bgClass="bg-emerald-500/10"
          delay={80}
        />
        <StatCard
          title="Avg Handle Time"
          value={dash.avgCallDuration}
          subtitle="Per inbound interaction"
          icon={Clock}
          trend={-2}
          colorClass="text-amber-400"
          bgClass="bg-amber-500/10"
          delay={160}
        />
        <StatCard
          title="Active AI Agents"
          value={activeAgents.length}
          numericValue={activeAgents.length}
          subtitle="Live & answering calls"
          icon={Zap}
          colorClass="text-violet-400"
          bgClass="bg-violet-500/10"
          delay={240}
        />
      </div>

      {/* ── Middle Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Call Volume Placeholder */}
        <div className="lg:col-span-2 card-surface p-6 animate-reveal-delay-1">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="font-heading font-bold text-white">Call Volume</h3>
              <p className="text-xs text-zinc-600 mt-0.5">30-day inbound traffic</p>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] font-semibold text-zinc-600">
              <BarChart3 className="w-3.5 h-3.5" />
              Last 30 days
            </div>
          </div>
          <div className="h-52 rounded-xl border border-white/[0.05] bg-white/[0.02] flex items-center justify-center relative overflow-hidden">
            {/* Simulated bar chart aesthetic */}
            <div className="absolute bottom-0 left-0 right-0 flex items-end gap-1.5 px-6 pb-0 h-full">
              {[35, 62, 45, 78, 55, 90, 67, 84, 72, 95, 80, 65, 88, 75, 60, 92, 70, 85, 45, 78, 63, 88, 72, 95, 80, 70, 88, 92, 76, 84].map((h, i) => (
                <div
                  key={i}
                  className="flex-1 rounded-t-sm transition-all"
                  style={{
                    height: `${h}%`,
                    background: i === 29
                      ? 'linear-gradient(to top, #7C3AED, #A78BFA)'
                      : `rgba(124,58,237,${0.1 + (h / 100) * 0.25})`,
                  }}
                />
              ))}
            </div>
            <div className="relative text-[11px] text-zinc-700 font-medium">Live data connects once calls begin</div>
          </div>
        </div>

        {/* Recent Calls Feed */}
        <div className="card-surface flex flex-col animate-reveal-delay-2">
          <div className="flex items-center justify-between p-5 border-b border-white/[0.04]">
            <div>
              <h3 className="font-heading font-bold text-white text-sm">Live Feed</h3>
              <p className="text-[11px] text-zinc-600 mt-0.5 flex items-center gap-1.5">
                <span className="dot-live" /> Real-time
              </p>
            </div>
            <Link to="/calls" className="text-[11px] text-violet-400 hover:text-violet-300 font-semibold flex items-center gap-1 transition-colors">
              All calls <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-hide">
            {dash.recentCalls.length > 0 ? (
              dash.recentCalls.map((call) => {
                const agent = agents.find(a => a.id === call.agent_id);
                const sc = statusConfig[call.status] || statusConfig.failed;
                const mins = call.duration_seconds ? `${Math.floor(call.duration_seconds / 60)}:${String(call.duration_seconds % 60).padStart(2, '0')}` : '—';
                return (
                  <div key={call.id} className="flex items-center gap-3 py-3 px-5 border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                    <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center shrink-0">
                      <Phone className="w-3.5 h-3.5 text-violet-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-white truncate font-mono-ui">{call.from_number}</p>
                      <p className="text-[10px] text-zinc-600 flex items-center gap-1">
                        <Bot className="w-2.5 h-2.5" />{agent?.name || 'AI Agent'}
                      </p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className={sc.className}>{sc.label}</span>
                      <p className="text-[10px] text-zinc-700 mt-1 font-mono-ui">{mins}</p>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="flex flex-col items-center justify-center h-full py-16 text-center px-6">
                <div className="w-12 h-12 rounded-2xl bg-white/[0.04] flex items-center justify-center mb-3">
                  <Activity className="w-5 h-5 text-zinc-700" />
                </div>
                <p className="text-sm font-semibold text-zinc-500">No calls yet</p>
                <p className="text-[11px] text-zinc-700 mt-1">Inbound calls will appear here in real-time</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── AI Agents Grid ── */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-heading font-bold text-white">AI Agents</h3>
            <p className="text-xs text-zinc-600 mt-0.5">Deployed inbound assistants</p>
          </div>
          <Link to="/agents" className="text-[11px] text-violet-400 hover:text-violet-300 font-semibold flex items-center gap-1 transition-colors">
            Manage <ArrowUpRight className="w-3 h-3" />
          </Link>
        </div>

        {agents.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.slice(0, 6).map((agent, i) => (
              <Link key={agent.id} to={`/agents/${agent.id}/edit`}>
                <div
                  className="card-surface p-5 flex flex-col gap-4 group cursor-pointer animate-reveal"
                  style={{ animationDelay: `${i * 60}ms` }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-violet-500/10 flex items-center justify-center group-hover:bg-violet-500/20 transition-colors">
                        <Bot className="w-4.5 h-4.5 text-violet-400" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-white leading-tight">{agent.name}</p>
                        <p className="text-[10px] text-zinc-600">{agent.llm_model}</p>
                      </div>
                    </div>
                    <span className={agent.is_active ? 'badge-active' : 'badge-inactive'}>
                      {agent.is_active ? 'Live' : 'Off'}
                    </span>
                  </div>
                  {agent.description && (
                    <p className="text-[11px] text-zinc-600 line-clamp-2 leading-relaxed">{agent.description}</p>
                  )}
                  <div className="flex items-center gap-2 font-mono-ui text-[10px] text-zinc-700 pt-3 border-t border-white/[0.04]">
                    <Phone className="w-3 h-3 text-violet-700" />
                    {agent.signalwire_phone_number || 'No number assigned'}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="card-surface flex flex-col items-center justify-center py-20 px-6 text-center">
            <div className="w-16 h-16 rounded-2xl bg-violet-500/10 flex items-center justify-center mb-4 animate-float">
              <Zap className="w-8 h-8 text-violet-400" />
            </div>
            <h3 className="font-heading font-bold text-white text-lg mb-2">No agents yet</h3>
            <p className="text-[13px] text-zinc-600 mb-6 max-w-sm leading-relaxed">
              Deploy your first AI agent to start automating inbound calls — your receptionist who never sleeps.
            </p>
            <Link to="/agents/new" className="btn-primary">
              <Plus className="w-4 h-4" />
              Deploy First Agent
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;