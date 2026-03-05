import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import {
    BarChart3,
    Calendar,
    Download,
    Filter,
    TrendingUp,
    Clock,
    PhoneCall,
    CheckCircle,
    ChevronDown,
    ArrowUpRight,
    ArrowDownRight,
    Search,
    Zap,
    PieChart,
    Activity,
    ShieldCheck
} from 'lucide-react';

const Reports = () => {
    const [dateRange, setDateRange] = useState('Last 7 Days');

    const kpis = [
        {
            title: 'Success Rate',
            value: '94.2%',
            trend: '+2.4%',
            status: 'up',
            icon: CheckCircle,
            accent: 'brand-violet'
        },
        {
            title: 'Avg. Duration',
            value: '2m 45s',
            trend: '-12s',
            status: 'down',
            icon: Clock,
            accent: 'brand-violet'
        },
        {
            title: 'Total Minutes',
            value: '12,480',
            trend: '+15.2%',
            status: 'up',
            icon: PhoneCall,
            accent: 'brand-violet'
        },
        {
            title: 'Estimated ROI',
            value: '$4,250',
            trend: '+8.1%',
            status: 'up',
            icon: TrendingUp,
            accent: 'brand-violet'
        }
    ];

    return (
        <div className="space-y-10 animate-reveal">
            {/* Header section with filters */}
            <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-6">
                <div>
                    <h1 className="text-4xl font-bold text-white tracking-tighter">Performance Matrix</h1>
                    <p className="text-gray-400 font-medium mt-1">Algorithmic analysis of AI-human voice interactions.</p>
                </div>
                <div className="flex items-center gap-3 overflow-x-auto pb-2 xl:pb-0 scrollbar-hide">
                    <Button variant="ghost" className="h-12 bg-white/5 border border-white/10 text-white rounded-2xl hover:bg-white/10 transition-all font-bold px-6">
                        <Calendar className="w-4 h-4 mr-2 text-brand-violet" />
                        {dateRange}
                        <ChevronDown className="w-4 h-4 ml-2 opacity-50" />
                    </Button>
                    <Button variant="ghost" className="h-12 bg-white/5 border border-white/10 text-white rounded-2xl hover:bg-white/10 transition-all font-bold px-6">
                        <Filter className="w-4 h-4 mr-2 text-brand-violet" />
                        Filters
                    </Button>
                    <Button className="h-12 bg-brand-violet hover:bg-brand-violet/90 text-white rounded-2xl shadow-lg shadow-brand-violet/20 transition-all font-bold px-8">
                        <Download className="w-4 h-4 mr-2" />
                        Export Audit
                    </Button>
                </div>
            </div>

            {/* KPI Overlays */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                {kpis.map((kpi, index) => (
                    <Card key={index} className="overflow-hidden border-0 shadow-2xl bg-white rounded-[2.5rem] group hover:-translate-y-2 transition-all duration-300">
                        <CardContent className="p-8">
                            <div className="flex items-center justify-between mb-6">
                                <div className={`w-14 h-14 rounded-2xl bg-brand-violet/5 flex items-center justify-center text-brand-violet group-hover:scale-110 group-hover:bg-brand-violet group-hover:text-white transition-all`}>
                                    <kpi.icon className="w-7 h-7" />
                                </div>
                                <div className={`flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full ${kpi.status === 'up' ? 'text-emerald-600 bg-emerald-50' : 'text-amber-600 bg-amber-50'}`}>
                                    {kpi.status === 'up' ? <ArrowUpRight className="w-3 h-3 mr-1" /> : <ArrowDownRight className="w-3 h-3 mr-1" />}
                                    {kpi.trend}
                                </div>
                            </div>
                            <div className="space-y-1">
                                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">{kpi.title}</p>
                                <h2 className="text-3xl font-extrabold text-brand-black leading-tight tracking-tight">{kpi.value}</h2>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Charts section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                <Card className="border-0 shadow-2xl bg-white rounded-[3rem] overflow-hidden">
                    <CardHeader className="p-10 pb-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle className="text-2xl font-bold text-brand-black">Optimization Flow</CardTitle>
                                <CardDescription className="text-gray-500 font-medium">Daily resolution velocity</CardDescription>
                            </div>
                            <div className="w-12 h-12 bg-brand-violet/5 rounded-2xl flex items-center justify-center text-brand-violet">
                                <BarChart3 className="w-6 h-6" />
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent className="p-10 pt-16">
                        <div className="h-64 w-full flex items-end justify-between space-x-3 px-2">
                            {[60, 85, 45, 90, 75, 55, 95].map((height, i) => (
                                <div key={i} className="flex-1 flex flex-col items-center group relative">
                                    <div className="absolute -top-12 opacity-0 group-hover:opacity-100 transition-all scale-95 group-hover:scale-100 bg-brand-black text-white text-[10px] font-bold px-3 py-1.5 rounded-lg shadow-xl pointer-events-none z-10 whitespace-nowrap">
                                        {height}% Success
                                    </div>
                                    <div
                                        className="w-full bg-brand-violet/10 rounded-2xl transition-all duration-500 hover:bg-brand-violet relative overflow-hidden"
                                        style={{ height: `${height}%` }}
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-t from-black/5 to-transparent" />
                                    </div>
                                    <span className="text-[9px] text-gray-400 mt-4 font-bold uppercase tracking-widest">Day 0{i + 1}</span>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-0 shadow-2xl bg-white rounded-[3rem] overflow-hidden">
                    <CardHeader className="p-10 pb-6 border-b border-gray-100">
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle className="text-2xl font-bold text-brand-black">Unit Performance</CardTitle>
                                <CardDescription className="text-gray-500 font-medium tracking-tight">Leaderboard based on resolution accuracy</CardDescription>
                            </div>
                            <div className="w-12 h-12 bg-brand-violet/5 rounded-2xl flex items-center justify-center text-brand-violet">
                                <Zap className="w-6 h-6" />
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent className="p-0">
                        <div className="divide-y divide-gray-100 px-6">
                            {[
                                { name: 'Support Controller v2', handled: 1250, success: 98, avatar: 'SC' },
                                { name: 'Outreach Protocol', handled: 850, success: 82, avatar: 'OP' },
                                { name: 'Scheduler Unit', handled: 640, success: 91, avatar: 'SU' },
                            ].map((agent, i) => (
                                <div key={i} className="p-8 flex items-center justify-between hover:bg-gray-50/50 transition-all group rounded-[2rem] my-2">
                                    <div className="flex items-center space-x-6">
                                        <div className="w-14 h-14 rounded-[1.25rem] bg-brand-black flex items-center justify-center text-brand-violet font-black text-xs shadow-xl group-hover:scale-110 transition-transform">
                                            {agent.avatar}
                                        </div>
                                        <div>
                                            <p className="text-lg font-extrabold text-brand-black group-hover:text-brand-violet transition-colors">{agent.name}</p>
                                            <p className="text-sm text-gray-400 font-bold uppercase tracking-tight">{agent.handled} Operations</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-3xl font-black text-brand-black leading-none">{agent.success}%</p>
                                        <div className="mt-1 flex items-center justify-end text-[9px] font-black text-gray-300 uppercase tracking-widest">
                                            <Activity className="w-2.5 h-2.5 mr-1" />
                                            Efficacy
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Detailed Report Table */}
            <Card className="border-0 shadow-2xl bg-white rounded-[3rem] overflow-hidden">
                <CardHeader className="p-10 border-b border-gray-100">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                        <div>
                            <CardTitle className="text-2xl font-bold text-brand-black flex items-center">
                                <ShieldCheck className="w-7 h-7 mr-3 text-brand-violet" />
                                Transaction Logs
                            </CardTitle>
                            <CardDescription className="text-gray-500 font-medium">Verified event stream for auditing.</CardDescription>
                        </div>
                        <div className="relative group">
                            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-brand-violet" />
                            <input
                                type="text"
                                placeholder="Search archives..."
                                className="h-11 pl-10 pr-6 bg-gray-50 border border-gray-100 rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-violet focus:border-transparent outline-none transition-all w-64"
                            />
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="p-0">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="bg-gray-50/80">
                                    <th className="px-10 py-5 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Matrix ID</th>
                                    <th className="px-10 py-5 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Protocol</th>
                                    <th className="px-10 py-5 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Subject</th>
                                    <th className="px-10 py-5 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Runtime</th>
                                    <th className="px-10 py-5 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em]">Sentiment</th>
                                    <th className="px-10 py-5 text-[10px] font-bold text-gray-400 uppercase tracking-[0.2em] text-right">Access</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {[1, 2, 3, 4, 5].map((item) => (
                                    <tr key={item} className="hover:bg-brand-violet/[0.02] transition-colors group">
                                        <td className="px-10 py-6">
                                            <code className="text-xs font-bold font-mono text-brand-violet bg-brand-violet/5 px-2 py-1 rounded-lg">#XTR-892{item}</code>
                                        </td>
                                        <td className="px-10 py-6 font-bold text-brand-black">Support AI Elite</td>
                                        <td className="px-10 py-6 text-gray-500 font-mono text-xs">+1 (555) {item}23-4567</td>
                                        <td className="px-10 py-6 text-gray-400 font-bold text-xs uppercase">4m 2{item}s</td>
                                        <td className="px-10 py-6">
                                            <div className="flex items-center">
                                                <div className="w-2 h-2 rounded-full bg-emerald-500 mr-2 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                                                <span className="text-[10px] font-black uppercase text-gray-400 tracking-widest">Positive</span>
                                            </div>
                                        </td>
                                        <td className="px-10 py-6 text-right">
                                            <Button variant="ghost" className="h-10 px-6 text-brand-violet font-bold hover:bg-brand-violet hover:text-white rounded-xl transition-all">Details</Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default Reports;
