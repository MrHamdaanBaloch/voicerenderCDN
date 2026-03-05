import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import {
  Bot,
  Plus,
  Search,
  MoreHorizontal,
  Edit,
  Trash2,
  Phone,
  Play,
  Pause,
  Copy,
  ArrowUpRight,
  Filter
} from 'lucide-react';
import api from '../../services/api';
import { useToast } from '../../hooks/use-toast';
import { getErrorMessage } from '../../lib/utils';

const AgentList = () => {
  const [agents, setAgents] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { toast } = useToast();

  const fetchAgents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.agents.getAgents();
      setAgents(response.data);
    } catch (err) {
      console.error("Failed to fetch agents:", err);
      const errorMessage = getErrorMessage(err, "Failed to load agents.");
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = (agent.name?.toLowerCase() || '').includes(searchQuery.toLowerCase()) ||
      (agent.description?.toLowerCase() || '').includes(searchQuery.toLowerCase());
    const matchesStatus = filterStatus === 'all' ||
      (filterStatus === 'active' && agent.is_active) ||
      (filterStatus === 'inactive' && !agent.is_active);

    return matchesSearch && matchesStatus;
  });

  const toggleAgentStatus = async (agentId, currentStatus) => {
    setLoading(true);
    try {
      await api.agents.updateAgent(agentId, { is_active: !currentStatus });
      toast({
        title: "Agent Status Updated",
        description: `Agent ${!currentStatus ? 'activated' : 'deactivated'} successfully.`,
      });
      fetchAgents();
    } catch (err) {
      console.error("Failed to toggle agent status:", err);
      toast({
        title: "Error",
        description: getErrorMessage(err, "Failed to update agent status."),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const deleteAgent = async (agentId) => {
    if (window.confirm('Are you sure you want to delete this agent? This action cannot be undone.')) {
      setLoading(true);
      try {
        await api.agents.deleteAgent(agentId);
        toast({
          title: "Agent Deleted",
          description: "Agent removed successfully.",
        });
        fetchAgents();
      } catch (err) {
        console.error("Failed to delete agent:", err);
        toast({
          title: "Error",
          description: getErrorMessage(err, "Failed to delete agent."),
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    }
  };

  const duplicateAgent = async (agentId) => {
    setLoading(true);
    try {
      const agentToDuplicate = agents.find(a => a.id === agentId);
      if (agentToDuplicate) {
        const newAgentData = {
          name: `${agentToDuplicate.name} (Copy)`,
          description: agentToDuplicate.description,
          llm_model: agentToDuplicate.llm_model,
          tts_model: agentToDuplicate.tts_model,
          tts_voice: agentToDuplicate.tts_voice,
          deepgram_model: agentToDuplicate.deepgram_model,
          system_prompt: agentToDuplicate.system_prompt,
          deepgram_config: agentToDuplicate.deepgram_config,
          silence_timeout_seconds: agentToDuplicate.silence_timeout_seconds,
          silence_prompt_text: agentToDuplicate.silence_prompt_text,
          is_active: false,
          signalwire_phone_number: null
        };
        await api.agents.createAgent(newAgentData);
        toast({
          title: "Agent Duplicated",
          description: "Agent duplicated successfully. It is currently inactive.",
        });
        fetchAgents();
      }
    } catch (err) {
      console.error("Failed to duplicate agent:", err);
      toast({
        title: "Error",
        description: getErrorMessage(err, "Failed to duplicate agent."),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const AgentCard = ({ agent }) => (
    <Card className="relative group overflow-hidden border-0 shadow-xl bg-white rounded-[2.5rem] hover:-translate-y-2 transition-all duration-300">
      <CardHeader className="pb-4 pt-8 px-8">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-4">
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all ${agent.is_active
              ? 'bg-brand-violet text-white shadow-[0_10px_15px_-5px_rgba(108,99,255,0.4)]'
              : 'bg-gray-100 text-gray-400'
              }`}>
              <Bot className="w-8 h-8" />
            </div>
            <div>
              <CardTitle className="text-xl font-bold text-brand-black">{agent.name}</CardTitle>
              <div className="flex items-center space-x-2 mt-1">
                <Badge
                  className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 border-0 ${agent.is_active
                    ? 'bg-emerald-500/10 text-emerald-600'
                    : 'bg-gray-200 text-gray-500'
                    }`}
                >
                  {agent.is_active ? 'Active' : 'Standby'}
                </Badge>
                {agent.signalwire_phone_number && (
                  <div className="flex items-center text-[10px] font-bold text-brand-violet bg-brand-violet/5 px-2 py-0.5 rounded-full">
                    <Phone className="w-3 h-3 mr-1" />
                    {agent.signalwire_phone_number}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="px-8 pb-8 pt-0">
        <p className="text-gray-500 text-sm mb-6 line-clamp-2 font-medium">
          {agent.description || "High-performance AI agent configured for semantic conversation and outcome optimization."}
        </p>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="p-3 bg-gray-50 rounded-2xl border border-gray-100">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest block mb-1">Intelligence</span>
            <p className="text-xs font-bold text-brand-black truncate">{agent.llm_model}</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-2xl border border-gray-100">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest block mb-1">Vocal Profile</span>
            <p className="text-xs font-bold text-brand-black truncate">{agent.tts_voice}</p>
          </div>
        </div>

        <div className="flex items-center justify-between pt-6 border-t border-gray-100">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => toggleAgentStatus(agent.id, agent.is_active)}
              className={`rounded-xl h-10 px-4 font-bold transition-all shadow-sm ${agent.is_active
                ? 'text-orange-500 border-orange-100 hover:bg-orange-50 hover:border-orange-200'
                : 'text-brand-violet border-brand-violet/20 hover:bg-brand-violet/5 hover:border-brand-violet/40'}`}
              disabled={loading}
            >
              {agent.is_active ? (
                <>
                  <Pause className="w-4 h-4 mr-2" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Deploy
                </>
              )}
            </Button>

            <Button
              variant="ghost"
              size="icon"
              onClick={() => duplicateAgent(agent.id)}
              className="h-10 w-10 text-gray-400 hover:text-brand-violet hover:bg-brand-violet/5 rounded-xl transition-all"
              disabled={loading}
            >
              <Copy className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex items-center space-x-1">
            <Button variant="ghost" size="icon" className="h-10 w-10 text-gray-400 hover:text-brand-black hover:bg-gray-100 rounded-xl transition-all" asChild disabled={loading}>
              <Link to={`/agents/${agent.id}`}>
                <Edit className="w-4 h-4" />
              </Link>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => deleteAgent(agent.id)}
              className="h-10 w-10 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all"
              disabled={loading}
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (loading && agents.length === 0) {
    return (
      <div className="p-6 flex flex-col items-center justify-center h-[60vh]">
        <div className="w-16 h-16 bg-brand-violet/10 rounded-3xl flex items-center justify-center animate-pulse mb-4">
          <Bot className="w-8 h-8 text-brand-violet animate-bounce" />
        </div>
        <p className="text-white font-bold tracking-tight animate-pulse underline decoration-brand-violet decoration-2 underline-offset-4">Syncing Agent Registry...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 flex flex-col items-center justify-center h-[60vh] text-center">
        <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mb-6">
          <XCircle className="w-10 h-10 text-red-500" />
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">Registry Offline</h1>
        <p className="text-gray-400 mb-8 max-w-md">{error}</p>
        <Button onClick={fetchAgents} className="bg-brand-violet hover:bg-brand-violet/90 rounded-xl px-8 h-12 font-bold">
          Reconnect to Grid
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-reveal">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Agent Registry</h1>
          <p className="text-gray-400 font-medium">Configure and manage your high-performance AI workforce.</p>
        </div>
        <Button asChild className="h-12 px-6 bg-brand-violet hover:bg-brand-violet/90 text-white rounded-2xl shadow-lg shadow-brand-violet/20 font-bold transition-all active:scale-[0.98]" disabled={loading}>
          <Link to="/agents/new" className="flex items-center">
            <Plus className="w-5 h-5 mr-3" />
            Initialize Agent
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="relative flex-1 group">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500 group-focus-within:text-brand-violet transition-colors" />
          <Input
            placeholder="Search registry for agents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-14 pl-12 bg-white/5 border-white/10 text-white placeholder:text-gray-500 rounded-2xl focus:border-brand-violet focus:ring-brand-violet transition-all"
            disabled={loading}
          />
        </div>

        <div className="flex items-center p-1.5 bg-white/5 border border-white/10 rounded-2xl space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setFilterStatus('all')}
            className={`rounded-xl px-4 h-10 font-bold transition-all ${filterStatus === 'all' ? 'bg-white text-brand-black shadow-lg' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
            disabled={loading}
          >
            All Units <span className="ml-2 opacity-50">{agents.length}</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setFilterStatus('active')}
            className={`rounded-xl px-4 h-10 font-bold transition-all ${filterStatus === 'active' ? 'bg-brand-violet text-white shadow-lg' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
            disabled={loading}
          >
            Deployed <span className="ml-2 opacity-50">{agents.filter(a => a.is_active).length}</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setFilterStatus('inactive')}
            className={`rounded-xl px-4 h-10 font-bold transition-all ${filterStatus === 'inactive' ? 'bg-white text-brand-black shadow-lg' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
            disabled={loading}
          >
            Standby <span className="ml-2 opacity-50">{agents.filter(a => !a.is_active).length}</span>
          </Button>
        </div>
      </div>

      {/* Agents Grid */}
      {filteredAgents.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
          {filteredAgents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20 bg-white/5 border border-dashed border-white/10 rounded-[3rem] text-center px-6">
          <div className="w-20 h-20 bg-white/5 rounded-[2rem] flex items-center justify-center mb-6">
            <Bot className="w-10 h-10 text-gray-500" />
          </div>
          <h3 className="text-2xl font-bold text-white mb-2">
            {searchQuery || filterStatus !== 'all' ? 'Agent Not Found' : 'Registry Empty'}
          </h3>
          <p className="text-gray-400 mb-8 max-w-sm">
            {searchQuery || filterStatus !== 'all'
              ? 'No neural units match your current filter parameters. Try expanding your search.'
              : 'Secure your competitive advantage by initializing your first AI sales agent today.'
            }
          </p>
          {(!searchQuery && filterStatus === 'all') && (
            <Button asChild className="h-14 px-10 bg-brand-violet hover:bg-brand-violet/90 text-white rounded-2xl shadow-xl shadow-brand-violet/20 font-bold text-lg" disabled={loading}>
              <Link to="/agents/new">
                <Plus className="w-6 h-6 mr-3" />
                Initialize First Agent
              </Link>
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export default AgentList;
