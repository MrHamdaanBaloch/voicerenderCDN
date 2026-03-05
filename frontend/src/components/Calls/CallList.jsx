import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import {
  Search,
  PhoneCall,
  Clock,
  CalendarDays,
  Bot,
  User,
  ArrowUpRight,
  Activity,
  History
} from 'lucide-react';
import api from '../../services/api';
import { useToast } from '../../hooks/use-toast';

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
      console.error("Failed to fetch calls:", err);
      setError("Failed to load calls histories from the cloud.");
      toast({
        title: "Error",
        description: "Failed to load calls.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchCalls();
  }, [fetchCalls]);

  const filteredCalls = calls.filter(call => {
    const searchLower = searchQuery.toLowerCase();
    return (
      (call.from_number?.toLowerCase() || '').includes(searchLower) ||
      (call.to_number?.toLowerCase() || '').includes(searchLower) ||
      (call.status?.toLowerCase() || '').includes(searchLower) ||
      (call.agent?.name?.toLowerCase() || '').includes(searchLower)
    );
  });

  const formatDuration = (seconds) => {
    if (seconds === null || seconds === undefined) return '0s';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return minutes > 0 ? `${minutes}m ${remainingSeconds}s` : `${remainingSeconds}s`;
  };

  const CallCard = ({ call }) => (
    <Card className="relative group overflow-hidden border-0 shadow-xl bg-white rounded-[2.5rem] hover:-translate-y-2 transition-all duration-300">
      <CardHeader className="pb-4 pt-8 px-8">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-4">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all ${call.status === 'completed'
                ? 'bg-brand-violet/5 text-brand-violet'
                : 'bg-emerald-500/10 text-emerald-600'
              }`}>
              <PhoneCall className="w-6 h-6" />
            </div>
            <div>
              <CardTitle className="text-lg font-bold text-brand-black">
                {call.from_number || 'Incoming...'}
              </CardTitle>
              <div className="flex items-center space-x-2 mt-1">
                <Badge
                  className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 border-0 ${call.status === 'completed' ? 'bg-brand-violet/10 text-brand-violet' :
                      call.status === 'in_progress' ? 'bg-emerald-500/10 text-emerald-600' :
                        'bg-gray-200 text-gray-500'
                    }`}
                >
                  {call.status?.replace('_', ' ') || 'unknown'}
                </Badge>
              </div>
            </div>
          </div>
          <div className="flex items-center text-[10px] font-bold text-gray-400 bg-gray-50 px-2.5 py-1 rounded-full border border-gray-100">
            <CalendarDays className="w-3 h-3 mr-1.5" />
            {new Date(call.start_time).toLocaleDateString()}
          </div>
        </div>
      </CardHeader>
      <CardContent className="px-8 pb-8 pt-0 space-y-4">
        <div className="grid grid-cols-2 gap-3 mt-2">
          <div className="flex flex-col p-3 bg-gray-50 rounded-2xl border border-gray-100">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Controller</span>
            <div className="flex items-center text-xs font-bold text-brand-black truncate">
              <Bot className="w-3 h-3 mr-1.5 text-brand-violet" />
              {call.agent?.name || 'Automator'}
            </div>
          </div>
          <div className="flex flex-col p-3 bg-gray-50 rounded-2xl border border-gray-100">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-1">Duration</span>
            <div className="flex items-center text-xs font-bold text-brand-black">
              <Clock className="w-3 h-3 mr-1.5 text-brand-violet" />
              {formatDuration(call.duration_seconds)}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-6 border-t border-gray-100">
          <div className="flex items-center space-x-2 text-xs font-bold text-gray-400">
            <User className="w-3 h-3" />
            <span>Target: {call.to_number || 'N/A'}</span>
          </div>
          <Button variant="ghost" size="sm" className="h-10 px-4 rounded-xl font-bold bg-brand-violet/5 text-brand-violet hover:bg-brand-violet hover:text-white transition-all" asChild>
            <Link to={`/calls/${call.id}`}>
              Logs <ArrowUpRight className="w-4 h-4 ml-1.5" />
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  if (loading && calls.length === 0) {
    return (
      <div className="p-6 flex flex-col items-center justify-center h-[60vh]">
        <div className="w-16 h-16 bg-white/5 rounded-3xl flex items-center justify-center animate-pulse mb-4 border border-white/10">
          <History className="w-8 h-8 text-brand-violet animate-spin-slow" />
        </div>
        <p className="text-white font-bold tracking-tight animate-pulse underline decoration-brand-violet decoration-2 underline-offset-4">Syncing Transmission Logs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 flex flex-col items-center justify-center h-[60vh] text-center">
        <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mb-6">
          <Activity className="w-10 h-10 text-red-500" />
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">Sync Interrupted</h1>
        <p className="text-gray-400 mb-8 max-w-md">{error}</p>
        <Button onClick={fetchCalls} className="bg-brand-violet hover:bg-brand-violet/90 rounded-xl px-8 h-12 font-bold transition-all">
          Retry Sync
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-reveal">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">Transmission Archive</h1>
        <p className="text-gray-400 font-medium">Detailed audit trail for all AI-governed communications.</p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 group">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500 group-focus-within:text-brand-violet transition-colors" />
          <Input
            placeholder="Search transcripts by number, status or agent..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-14 pl-12 bg-white/5 border-white/10 text-white placeholder:text-gray-500 rounded-2xl focus:border-brand-violet focus:ring-brand-violet transition-all"
            disabled={loading}
          />
        </div>
      </div>

      {/* Calls Grid */}
      {filteredCalls.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
          {filteredCalls.map((call) => (
            <CallCard key={call.id} call={call} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20 bg-white/5 border border-dashed border-white/10 rounded-[3rem] text-center px-6">
          <div className="w-20 h-20 bg-white/5 rounded-[2rem] flex items-center justify-center mb-6">
            <History className="w-10 h-10 text-gray-500" />
          </div>
          <h3 className="text-2xl font-bold text-white mb-2">
            {searchQuery ? 'Record Not Found' : 'Archive Clear'}
          </h3>
          <p className="text-gray-400 mb-8 max-w-sm">
            {searchQuery
              ? 'No transmission matches your query. Try broadening your search parameters.'
              : 'Data streams will propagate here as soon as your agents begin their cycles.'
            }
          </p>
        </div>
      )}
    </div>
  );
};

export default CallList;
