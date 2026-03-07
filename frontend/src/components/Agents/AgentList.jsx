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
    <div className="card-surface p-6 flex flex-col gap-5 hover-glow-violet transition-all duration-300 group">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 transition-all ${agent.is_active ? 'bg-violet-500/15' : 'bg-white/[0.05]'}`}>
            <Bot className={`w-5 h-5 ${agent.is_active ? 'text-violet-400' : 'text-zinc-600'}`} />
          </div>
          <div>
            <h3 className="font-heading font-bold text-white text-sm leading-tight">{agent.name}</h3>
            <p className="text-[10px] text-zinc-600 mt-0.5">{agent.llm_model}</p>
          </div>
        </div>
        <span className={agent.is_active ? 'badge-active' : 'badge-inactive'}>
          {agent.is_active ? 'Live' : 'Off'}
        </span>
      </div>

      {/* Description */}
      <p className="text-[12px] text-zinc-600 line-clamp-2 leading-relaxed flex-1">
        {agent.description || 'Inbound AI agent ready to handle customer calls 24/7.'}
      </p>

      {/* Meta row */}
      <div className="grid grid-cols-2 gap-2">
        <div className="p-2.5 rounded-lg bg-white/[0.03] border border-white/[0.05]">
          <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-700 block mb-0.5">Voice</span>
          <p className="text-[11px] font-semibold text-zinc-400 truncate">{agent.tts_voice}</p>
        </div>
        <div className="p-2.5 rounded-lg bg-white/[0.03] border border-white/[0.05]">
          <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-700 block mb-0.5">Number</span>
          <p className="text-[11px] font-semibold text-zinc-400 truncate font-mono-ui">{agent.signalwire_phone_number || '—'}</p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-white/[0.05]">
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => toggleAgentStatus(agent.id, agent.is_active)}
            disabled={loading}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold transition-all border ${agent.is_active
                ? 'text-amber-400 border-amber-500/20 bg-amber-500/10 hover:bg-amber-500/20'
                : 'text-violet-400 border-violet-500/20 bg-violet-500/10 hover:bg-violet-500/20'
              }`}
          >
            {agent.is_active ? <><Pause className="w-3 h-3" /> Pause</> : <><Play className="w-3 h-3" /> Deploy</>}
          </button>
          <button onClick={() => duplicateAgent(agent.id)} disabled={loading} className="p-2 rounded-lg text-zinc-600 hover:text-zinc-300 hover:bg-white/[0.05] transition-all">
            <Copy className="w-3.5 h-3.5" />
          </button>
        </div>
        <div className="flex items-center gap-1">
          <Link to={`/agents/${agent.id}`} className="p-2 rounded-lg text-zinc-600 hover:text-zinc-300 hover:bg-white/[0.05] transition-all">
            <Edit className="w-3.5 h-3.5" />
          </Link>
          <button onClick={() => deleteAgent(agent.id)} disabled={loading} className="p-2 rounded-lg text-zinc-600 hover:text-rose-400 hover:bg-rose-500/10 transition-all">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );

  if (loading && agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
        <div className="w-12 h-12 rounded-2xl bg-violet-500/10 flex items-center justify-center animate-pulse-slow">
          <Bot className="w-6 h-6 text-violet-400" />
        </div>
        <p className="text-sm font-semibold text-zinc-500">Loading agents…</p>
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
    <div className="space-y-7 animate-reveal">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-heading font-bold text-white tracking-tight">AI Agents</h1>
          <p className="text-sm text-zinc-600 mt-0.5">Deploy and manage your inbound AI workforce.</p>
        </div>
        <Link to="/agents/new" className="btn-primary self-start sm:self-auto" disabled={loading}>
          <Plus className="w-4 h-4" />
          New Agent
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600" />
          <input
            placeholder="Search agents…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-input pl-9 h-10 w-full"
            disabled={loading}
          />
        </div>
        <div className="flex items-center gap-1 p-1 rounded-xl border border-white/[0.06] bg-white/[0.03]">
          {[['all', `All (${agents.length})`], ['active', `Live (${agents.filter(a => a.is_active).length})`], ['inactive', `Off (${agents.filter(a => !a.is_active).length})`]].map(([key, label]) => (
            <button
              key={key}
              onClick={() => setFilterStatus(key)}
              disabled={loading}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${filterStatus === key
                  ? 'bg-violet-600 text-white'
                  : 'text-zinc-500 hover:text-zinc-200 hover:bg-white/[0.05]'
                }`}
            >{label}</button>
          ))}
        </div>
      </div>

      {/* Agents Grid */}
      {filteredAgents.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredAgents.map((agent, i) => (
            <div key={agent.id} className="animate-reveal" style={{ animationDelay: `${i * 50}ms` }}>
              <AgentCard agent={agent} />
            </div>
          ))}
        </div>
      ) : (
        <div className="card-surface flex flex-col items-center justify-center py-20 text-center">
          <div className="w-14 h-14 rounded-2xl bg-violet-500/10 flex items-center justify-center mb-4 animate-float">
            <Bot className="w-7 h-7 text-violet-400" />
          </div>
          <h3 className="font-heading font-bold text-white text-lg mb-1">
            {searchQuery || filterStatus !== 'all' ? 'No matches' : 'No agents yet'}
          </h3>
          <p className="text-[13px] text-zinc-600 mb-6 max-w-sm">Deploy your first AI agent to start automating inbound calls.</p>
          {(!searchQuery && filterStatus === 'all') && (
            <Link to="/agents/new" className="btn-primary" disabled={loading}>
              <Plus className="w-4 h-4" /> Deploy First Agent
            </Link>
          )}
        </div>
      )}
    </div>
  );
};

export default AgentList;
