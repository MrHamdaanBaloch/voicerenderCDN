import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { 
  Phone, 
  TrendingUp, 
  Clock, 
  Activity,
  PhoneCall,
  CheckCircle,
  XCircle,
  ArrowUpRight,
  MoreHorizontal
} from 'lucide-react';
import { mockDashboardStats, mockAgents } from '../../data/mock';

const Dashboard = () => {
  const stats = mockDashboardStats;
  const activeAgents = mockAgents.filter(agent => agent.is_active);

  const StatCard = ({ title, value, subtitle, icon: Icon, trend, color = "emerald" }) => (
    <Card className="relative overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">{title}</CardTitle>
        <Icon className={`w-4 h-4 text-${color}-600`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-gray-900">{value}</div>
        {subtitle && (
          <p className="text-xs text-gray-500 mt-1">
            {trend && (
              <span className={`inline-flex items-center ${trend > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                <ArrowUpRight className="w-3 h-3 mr-1" />
                {Math.abs(trend)}%
              </span>
            )}
            {subtitle}
          </p>
        )}
      </CardContent>
    </Card>
  );

  const CallRow = ({ call, agent }) => {
    const getStatusColor = (status) => {
      switch (status) {
        case 'completed': return 'text-emerald-600 bg-emerald-50';
        case 'in_progress': return 'text-blue-600 bg-blue-50';
        case 'failed': return 'text-red-600 bg-red-50';
        default: return 'text-gray-600 bg-gray-50';
      }
    };

    const formatDuration = (seconds) => {
      if (!seconds) return '--';
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
      <div className="flex items-center justify-between p-4 border-b border-gray-100 last:border-b-0">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
            <Phone className="w-4 h-4 text-gray-600" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">{call.from_number}</p>
            <p className="text-xs text-gray-500">{agent?.name || 'Unknown Agent'}</p>
          </div>
        </div>
        <div className="text-right">
          <Badge 
            variant="secondary" 
            className={`text-xs mb-1 ${getStatusColor(call.status)}`}
          >
            {call.status.replace('_', ' ')}
          </Badge>
          <p className="text-xs text-gray-500">{formatDuration(call.duration_seconds)}</p>
        </div>
      </div>
    );
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Monitor your AI agents and call performance</p>
        </div>
        <div className="flex items-center space-x-3 mt-4 sm:mt-0">
          <Button variant="outline" size="sm">
            <Activity className="w-4 h-4 mr-2" />
            Live View
          </Button>
          <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700">
            <Phone className="w-4 h-4 mr-2" />
            Start Call
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Calls Today"
          value={stats.totalCalls.toLocaleString()}
          subtitle="from yesterday"
          icon={PhoneCall}
          trend={12.5}
        />
        <StatCard
          title="Success Rate"
          value={`${stats.successRate}%`}
          subtitle="this month"
          icon={CheckCircle}
          trend={2.1}
          color="emerald"
        />
        <StatCard
          title="Avg Call Duration"
          value={stats.avgCallDuration}
          subtitle="across all agents"
          icon={Clock}
          trend={-5.2}
          color="blue"
        />
        <StatCard
          title="Active Calls"
          value={stats.activeCalls}
          subtitle="right now"
          icon={Activity}
          color="orange"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Call Volume Chart Placeholder */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">Call Volume Trends</CardTitle>
            <CardDescription>Monthly call statistics over the past 7 months</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <TrendingUp className="w-12 h-12 text-emerald-600 mx-auto mb-2" />
                <p className="text-gray-600">Chart visualization would go here</p>
                <p className="text-sm text-gray-500 mt-1">Integration with charting library needed</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle className="text-lg">Recent Calls</CardTitle>
              <CardDescription>Latest call activity</CardDescription>
            </div>
            <Button variant="ghost" size="sm">
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-80 overflow-y-auto">
              {stats.recentCalls.map((call) => {
                const agent = mockAgents.find(a => a.id === call.agent_id);
                return (
                  <CallRow key={call.id} call={call} agent={agent} />
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Agents */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Active Agents</CardTitle>
              <CardDescription>Currently running AI agents</CardDescription>
            </div>
            <Button variant="outline" size="sm">View All</Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {activeAgents.map((agent) => (
              <div key={agent.id} className="p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-900">{agent.name}</h3>
                  <Badge 
                    variant="secondary" 
                    className={agent.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-gray-50 text-gray-700'}
                  >
                    {agent.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
                <p className="text-sm text-gray-600 mb-2 line-clamp-2">{agent.description}</p>
                <div className="flex items-center text-xs text-gray-500">
                  <Phone className="w-3 h-3 mr-1" />
                  {agent.signalwire_phone_number || 'No number assigned'}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;