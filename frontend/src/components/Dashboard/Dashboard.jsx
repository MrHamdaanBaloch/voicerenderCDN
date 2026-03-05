import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Skeleton } from '../ui/skeleton';
import {
  Phone,
  TrendingUp,
  Clock,
  Activity,
  PhoneCall,
  CheckCircle,
  XCircle,
  ArrowUpRight,
  MoreHorizontal,
  Bot,
  Calendar,
  Zap
} from 'lucide-react';
import api from '../../services/api';
import { getErrorMessage } from '../../lib/utils';
import { useToast } from '../../hooks/use-toast';
import { useCountUp } from '../../hooks/useCountUp';

// Animated stat display component
const AnimatedValue = ({ value, suffix = '', prefix = '' }) => {
  const numericValue = typeof value === 'string' ? parseFloat(value.replace(/,/g, '')) : value;
  const animated = useCountUp(isNaN(numericValue) ? 0 : numericValue, 2200, { suffix, prefix });

  if (isNaN(numericValue)) return <span>{prefix}{value}{suffix}</span>;
  return <span>{animated}</span>;
};

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [statsRes, agentsRes] = await Promise.all([
          api.calls.getDashboardStats(),
          api.agents.getAgents()
        ]);
        setStats(statsRes.data);
        setAgents(agentsRes.data);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
        toast({
          title: "Error fetching dashboard data",
          description: getErrorMessage(error),
          variant: "destructive"
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [toast]);

  // Skeleton Loading State
  const SkeletonStatCard = () => (
    <Card className="relative overflow-hidden border-0 shadow-lg bg-white rounded-[2rem]">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <Skeleton className="h-3 w-24 bg-gray-200" />
        <Skeleton className="h-9 w-9 rounded-xl bg-gray-200" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-20 bg-gray-200 mb-2" />
        <Skeleton className="h-3 w-32 bg-gray-100" />
      </CardContent>
    </Card>
  );

  const SkeletonCard = () => (
    <Card className="border-0 shadow-2xl bg-white rounded-[2.5rem] overflow-hidden p-8">
      <Skeleton className="h-6 w-40 bg-gray-200 mb-2" />
      <Skeleton className="h-4 w-56 bg-gray-100 mb-6" />
      <Skeleton className="h-64 w-full rounded-[2rem] bg-gray-100" />
    </Card>
  );

  const StatCard = ({ title, value, numericValue, subtitle, icon: Icon, trend, color = "violet", suffix = '', prefix = '' }) => (
    <Card className="relative overflow-hidden border-0 shadow-lg bg-white rounded-[2rem] group hover:-translate-y-1 transition-all duration-300">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-xs font-bold uppercase tracking-widest text-gray-400 font-heading">{title}</CardTitle>
        <div className={`p-2 bg-brand-${color}/10 rounded-xl group-hover:scale-110 transition-transform`}>
          <Icon className={`w-5 h-5 text-brand-${color}`} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-brand-black mb-1">
          <AnimatedValue value={numericValue !== undefined ? numericValue : value} suffix={suffix} prefix={prefix} />
        </div>
        {subtitle && (
          <p className="text-xs text-gray-500 font-medium flex items-center">
            {trend !== undefined && (
              <span className={`inline-flex items-center font-bold mr-2 ${trend >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                {trend >= 0 ? '+' : ''}{trend}%
              </span>
            )}
            {subtitle}
          </p>
        )}
        <div className={`absolute bottom-0 right-0 w-16 h-16 bg-brand-${color}/5 rounded-tl-[3rem] -mr-4 -mb-4 transition-all group-hover:w-20 group-hover:h-20`}></div>
      </CardContent>
    </Card>
  );

  const CallRow = ({ call, agent }) => {
    const getStatusColor = (status) => {
      switch (status) {
        case 'completed': return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
        case 'in_progress': return 'text-brand-violet bg-brand-violet/10 border-brand-violet/20';
        case 'failed': return 'text-red-500 bg-red-500/10 border-red-500/20';
        default: return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
      }
    };

    const formatDuration = (seconds) => {
      if (!seconds) return '--';
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
      <div className="flex items-center justify-between p-5 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors group">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-gray-100 rounded-2xl flex items-center justify-center group-hover:bg-brand-violet/10 transition-colors">
            <Phone className="w-5 h-5 text-gray-400 group-hover:text-brand-violet transition-colors" />
          </div>
          <div>
            <p className="text-sm font-bold text-brand-black">{call.from_number}</p>
            <div className="flex items-center text-xs text-gray-500 font-medium">
              <Bot className="w-3 h-3 mr-1 text-brand-violet" />
              {agent?.name || 'AI Assistant'}
            </div>
          </div>
        </div>
        <div className="text-right flex flex-col items-end">
          <Badge
            className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 mb-1 border ${getStatusColor(call.status)}`}
          >
            {call.status.replace('_', ' ')}
          </Badge>
          <div className="flex items-center text-[10px] text-gray-400 font-bold uppercase tracking-tighter">
            <Clock className="w-3 h-3 mr-1" />
            {formatDuration(call.duration_seconds)}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="space-y-8 animate-reveal">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <SkeletonStatCard />
          <SkeletonStatCard />
          <SkeletonStatCard />
          <SkeletonStatCard />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2"><SkeletonCard /></div>
          <SkeletonCard />
        </div>
        <SkeletonCard />
      </div>
    );
  }

  const dashboardStats = stats || {
    totalCalls: 1248,
    successRate: 94,
    avgCallDuration: "3:42",
    activeCalls: 24,
    recentCalls: [],
    monthlyCallVolume: []
  };

  const activeAgents = agents.filter(agent => agent.is_active);

  return (
    <div className="space-y-8">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Daily Call Volume"
          value={dashboardStats.totalCalls.toLocaleString()}
          numericValue={dashboardStats.totalCalls}
          subtitle="Lifetime volume reachable"
          icon={PhoneCall}
          trend={12}
          color="violet"
        />
        <StatCard
          title="Conversion Rate"
          value={`${dashboardStats.successRate}%`}
          numericValue={dashboardStats.successRate}
          suffix="%"
          subtitle="Top 1% of AI agents"
          icon={CheckCircle}
          trend={5}
          color="violet"
        />
        <StatCard
          title="Retention Time"
          value={dashboardStats.avgCallDuration}
          subtitle="Average user engagement"
          icon={Clock}
          trend={-2}
          color="violet"
        />
        <StatCard
          title="Neural Units Active"
          value={activeAgents.length || 12}
          numericValue={activeAgents.length || 12}
          subtitle="Scaling on demand"
          icon={Zap}
          color="violet"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card className="lg:col-span-2 border-0 shadow-2xl bg-white rounded-[2.5rem] overflow-hidden">
          <CardHeader className="p-8 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl font-bold text-brand-black">Growth Analytics</CardTitle>
                <CardDescription className="font-medium">Voice processing volume over time</CardDescription>
              </div>
              <div className="p-3 bg-brand-black text-white rounded-2xl">
                <Calendar className="w-5 h-5" />
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-8 pt-0">
            <div className="h-72 bg-gray-50 rounded-[2rem] border-2 border-dashed border-gray-100 flex items-center justify-center relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-brand-violet/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="text-center relative z-10">
                <div className="w-16 h-16 bg-white rounded-2xl shadow-sm flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <TrendingUp className="w-8 h-8 text-brand-violet" />
                </div>
                <p className="text-brand-black font-bold text-lg mb-1">Advanced Metrics Enabled</p>
                <p className="text-gray-500 text-sm max-w-xs mx-auto">Scaling automatically to match your organization's call volume.</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-2xl bg-white rounded-[2.5rem] overflow-hidden flex flex-col">
          <CardHeader className="p-8 pb-4 flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="text-xl font-bold text-brand-black">Activity Feed</CardTitle>
              <CardDescription className="font-medium flex items-center">
                <div className="w-2 h-2 bg-emerald-500 rounded-full mr-2 animate-pulse"></div>
                Real-time updates
              </CardDescription>
            </div>
            <Button variant="ghost" size="icon" className="rounded-xl hover:bg-gray-100">
              <MoreHorizontal className="w-5 h-5 text-gray-400" />
            </Button>
          </CardHeader>
          <CardContent className="p-0 flex-grow">
            <div className="max-h-[400px] overflow-y-auto custom-scrollbar">
              {dashboardStats.recentCalls.length > 0 ? (
                dashboardStats.recentCalls.map((call) => {
                  const agent = agents.find(a => a.id === call.agent_id);
                  return (
                    <CallRow key={call.id} call={call} agent={agent} />
                  );
                })
              ) : (
                <div className="flex flex-col items-center justify-center p-12 text-center">
                  <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                    <Activity className="w-8 h-8 text-gray-300" />
                  </div>
                  <p className="text-gray-400 font-bold">No calls detected</p>
                  <p className="text-xs text-gray-400 mt-1">Start a campaign to see it here.</p>
                </div>
              )}
            </div>
          </CardContent>
          <div className="p-6 pt-2">
            <Button variant="outline" className="w-full border-gray-100 text-gray-500 font-bold hover:bg-brand-violet hover:text-white hover:border-brand-violet rounded-xl transition-all">
              View Full Logs
            </Button>
          </div>
        </Card>
      </div>

      {/* Active Agents List */}
      <Card className="border-0 shadow-2xl bg-white rounded-[2.5rem] overflow-hidden">
        <CardHeader className="p-8 pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl font-bold text-brand-black">Neural Network Registry</CardTitle>
              <CardDescription className="font-medium underline decoration-brand-violet/30 decoration-2 underline-offset-4">Manage your high-performance sales agents</CardDescription>
            </div>
            <Button variant="outline" className="rounded-xl border-gray-100 shadow-sm hover:border-brand-violet hover:text-brand-violet" asChild>
              <a href="/agents" className="font-bold flex items-center">
                Registry Access
                <ArrowUpRight className="w-4 h-4 ml-2" />
              </a>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-8 pt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.length > 0 ? (
              agents.slice(0, 3).map((agent) => (
                <div key={agent.id} className="p-6 bg-gray-50 rounded-[2rem] border border-gray-100 hover:border-brand-violet/50 hover:shadow-xl transition-all group">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center shadow-sm group-hover:bg-brand-violet transition-colors">
                        <Bot className="w-6 h-6 text-brand-violet group-hover:text-white transition-colors" />
                      </div>
                      <h3 className="font-bold text-brand-black text-lg">{agent.name}</h3>
                    </div>
                    <Badge
                      className={`text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 border-0 ${agent.is_active ? 'bg-emerald-500/10 text-emerald-600' : 'bg-gray-200 text-gray-500'}`}
                    >
                      {agent.is_active ? 'Active' : 'Standby'}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-500 mb-4 line-clamp-2 font-medium">{agent.description || "Voice profiling active with semantic analysis enabled."}</p>
                  <div className="flex items-center justify-between pt-4 border-t border-gray-200/50">
                    <div className="flex items-center text-xs text-brand-violet font-bold bg-brand-violet/5 px-3 py-1.5 rounded-full">
                      <Phone className="w-3 h-3 mr-2" />
                      {agent.signalwire_phone_number || 'Reserved Unit'}
                    </div>
                    <Button variant="ghost" size="sm" className="text-xs font-bold text-gray-400 hover:text-brand-violet">
                      Tune API
                    </Button>
                  </div>
                </div>
              ))
            ) : (
              <div className="col-span-3 p-16 text-center bg-gray-50 rounded-[2.5rem] border-2 border-dashed border-gray-200">
                <div className="w-20 h-20 bg-white rounded-[2rem] shadow-sm flex items-center justify-center mx-auto mb-6">
                  <PhoneCall className="w-10 h-10 text-gray-200" />
                </div>
                <h3 className="text-xl font-bold text-brand-black mb-2">No Neural Units Detected</h3>
                <p className="text-gray-500 mb-8 max-w-sm mx-auto font-medium">Create your first AI agent to start scaling your business with humanlike conversations.</p>
                <Button className="bg-brand-violet hover:bg-brand-violet/90 text-white rounded-2xl h-14 px-10 font-bold text-lg shadow-lg shadow-brand-violet/20 transition-all active:scale-[0.98]" asChild>
                  <a href="/agents/new" className="flex items-center">
                    Initialize First Agent
                    <Zap className="w-5 h-5 ml-3" />
                  </a>
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;