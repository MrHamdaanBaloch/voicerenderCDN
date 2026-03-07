import React, { useState } from 'react';
import {
    BarChart3, Calendar, Download, Filter, TrendingUp, Clock,
    PhoneCall, CheckCircle, ChevronDown, ArrowUpRight, ArrowDownRight,
    Zap, Activity, ShieldCheck, Search
} from 'lucide-react';

const KPIS = [
    { title: 'Resolution Rate', value: '94.2%', trend: '+2.4%', up: true, icon: CheckCircle },
    { title: 'Avg Handle Time', value: '2m 45s', trend: '-12s', up: true, icon: Clock },
    { title: 'Total Call-Mins', value: '12,480', trend: '+15.2%', up: true, icon: PhoneCall },
    { title: 'Deflection Saves', value: '$4,250', trend: '+8.1%', up: true, icon: TrendingUp },
];

const BAR_HEIGHTS = [60, 85, 45, 90, 75, 55, 95];
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const TOP_AGENTS = [
    { name: 'Support AI — Sarah', handled: 1250, success: 98, avatar: 'SA' },
    { name: 'Reception Bot — Mike', handled: 850, success: 91, avatar: 'RM' },
    { name: 'Scheduler Unit', handled: 640, success: 88, avatar: 'SU' },
];

const Reports = () => {
    const [dateRange, setDateRange] = useState('Last 7 Days');

    return (
        <div className="space-y-8 animate-reveal">
            {/* ── Header ── */}
            <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-heading font-bold text-white tracking-tight">Analytics & Reports</h1>
                    <p className="text-sm text-zinc-600 mt-0.5">Performance analysis of all inbound AI interactions.</p>
                </div>
                <div className="flex items-center gap-2">
                    <button className="flex items-center gap-2 h-9 px-4 rounded-xl border border-white/[0.08] bg-white/[0.04] text-sm text-zinc-400 hover:text-white hover:bg-white/[0.07] transition-all font-medium">
                        <Calendar className="w-3.5 h-3.5 text-violet-400" />
                        {dateRange}
                        <ChevronDown className="w-3.5 h-3.5 opacity-50" />
                    </button>
                    <button className="flex items-center gap-2 h-9 px-4 rounded-xl border border-white/[0.08] bg-white/[0.04] text-sm text-zinc-400 hover:text-white transition-all font-medium">
                        <Filter className="w-3.5 h-3.5 text-violet-400" />
                        Filters
                    </button>
                    <button className="flex items-center gap-2 h-9 px-4 rounded-xl bg-violet-700 hover:bg-violet-600 text-white text-sm font-semibold transition-all shadow-glow-violet">
                        <Download className="w-3.5 h-3.5" />
                        Export
                    </button>
                </div>
            </div>

            {/* ── KPI Cards ── */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {KPIS.map((kpi, i) => (
                    <div key={i} className="stat-card group hover-glow-violet transition-all" style={{ animationDelay: `${i * 60}ms` }}>
                        <div className="flex items-center justify-between">
                            <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-zinc-600">{kpi.title}</span>
                            <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                                <kpi.icon className="w-4 h-4 text-violet-400" />
                            </div>
                        </div>
                        <div>
                            <div className="text-2xl font-heading font-bold text-white tracking-tight">{kpi.value}</div>
                            <div className={`flex items-center gap-1 text-[10px] font-bold mt-1 ${kpi.up ? 'text-emerald-400' : 'text-amber-400'}`}>
                                {kpi.up ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                                {kpi.trend} vs last period
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* ── Charts row ── */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Resolution flow bar chart */}
                <div className="card-surface p-6">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h3 className="font-heading font-bold text-white">Resolution Flow</h3>
                            <p className="text-xs text-zinc-600 mt-0.5">Daily FCR success rate</p>
                        </div>
                        <BarChart3 className="w-5 h-5 text-zinc-700" />
                    </div>
                    <div className="h-52 flex items-end gap-2">
                        {BAR_HEIGHTS.map((h, i) => (
                            <div key={i} className="flex-1 flex flex-col items-center gap-2 group relative">
                                <div
                                    className="absolute -top-10 hidden group-hover:flex items-center justify-center bg-zinc-800 text-white text-[10px] font-bold px-2 py-1 rounded-lg shadow-xl pointer-events-none whitespace-nowrap z-10"
                                >
                                    {h}% FCR
                                </div>
                                <div
                                    className="w-full rounded-t-md transition-all duration-500"
                                    style={{
                                        height: `${h}%`,
                                        background: `linear-gradient(to top, #7C3AED, rgba(167,139,250,${0.4 + h / 200}))`,
                                        opacity: 0.7 + h / 300
                                    }}
                                />
                                <span className="text-[9px] text-zinc-700 font-semibold">{DAYS[i]}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Agent leaderboard */}
                <div className="card-surface overflow-hidden">
                    <div className="flex items-center justify-between p-6 border-b border-white/[0.05]">
                        <div>
                            <h3 className="font-heading font-bold text-white">Agent Leaderboard</h3>
                            <p className="text-xs text-zinc-600 mt-0.5">By FCR accuracy</p>
                        </div>
                        <Zap className="w-4 h-4 text-zinc-700" />
                    </div>
                    <div className="divide-y divide-white/[0.04]">
                        {TOP_AGENTS.map((agent, i) => (
                            <div key={i} className="flex items-center gap-4 p-5 hover:bg-white/[0.02] transition-colors">
                                <div className="w-10 h-10 rounded-xl bg-violet-500/15 flex items-center justify-center text-[11px] font-black text-violet-400 shrink-0">
                                    {agent.avatar}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-semibold text-white truncate">{agent.name}</p>
                                    <p className="text-[11px] text-zinc-600">{agent.handled.toLocaleString()} calls handled</p>
                                </div>
                                <div className="text-right shrink-0">
                                    <p className="text-xl font-heading font-bold text-white">{agent.success}%</p>
                                    <p className="text-[9px] uppercase tracking-widest text-zinc-700 flex items-center gap-1 justify-end">
                                        <Activity className="w-2.5 h-2.5" /> FCR
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* ── Transaction log table ── */}
            <div className="card-surface overflow-hidden">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-6 border-b border-white/[0.05]">
                    <div className="flex items-center gap-2.5">
                        <ShieldCheck className="w-4 h-4 text-violet-400" />
                        <div>
                            <h3 className="font-heading font-bold text-white">Call Audit Log</h3>
                            <p className="text-xs text-zinc-600">Verified event stream for compliance.</p>
                        </div>
                    </div>
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-600" />
                        <input
                            type="text"
                            placeholder="Search logs..."
                            className="form-input pl-8 h-9 w-52 text-xs"
                        />
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-white/[0.02]">
                                {['Call ID', 'Agent', 'Caller', 'Duration', 'Sentiment', ''].map((h, i) => (
                                    <th key={i} className={`px-6 py-3 text-[9px] font-bold text-zinc-600 uppercase tracking-[0.15em] ${i === 5 ? 'text-right' : ''}`}>{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/[0.03]">
                            {[1, 2, 3, 4, 5].map((item) => (
                                <tr key={item} className="hover:bg-white/[0.02] transition-colors">
                                    <td className="px-6 py-4">
                                        <code className="text-[11px] font-bold font-mono-ui text-violet-400 bg-violet-500/10 px-2 py-0.5 rounded">
                                            #XTR-892{item}
                                        </code>
                                    </td>
                                    <td className="px-6 py-4 text-sm font-semibold text-white">Support AI — Sarah</td>
                                    <td className="px-6 py-4 text-[11px] text-zinc-500 font-mono-ui">+1 (555) {item}23-4567</td>
                                    <td className="px-6 py-4 text-[11px] text-zinc-600 font-semibold">4m 2{item}s</td>
                                    <td className="px-6 py-4">
                                        <span className="badge-active">Positive</span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button className="text-[11px] font-semibold text-violet-400 hover:text-violet-300 transition-colors">Details →</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Reports;
