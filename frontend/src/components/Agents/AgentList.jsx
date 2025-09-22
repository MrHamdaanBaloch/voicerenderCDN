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
  Copy
} from 'lucide-react';
import api from '../../services/api'; // Import the API service
import { useToast } from '../../hooks/use-toast'; // Import useToast

const AgentList = () => {
  const [agents, setAgents] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all'); // all, active, inactive
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
      setError("Failed to load agents. Please try again.");
      toast({
        title: "Error",
        description: "Failed to load agents.",
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
    const matchesSearch = agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         agent.description.toLowerCase().includes(searchQuery.toLowerCase());
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
      fetchAgents(); // Re-fetch agents to update the list
    } catch (err) {
      console.error("Failed to toggle agent status:", err);
      toast({
        title: "Error",
        description: "Failed to update agent status.",
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
        fetchAgents(); // Re-fetch agents to update the list
      } catch (err) {
        console.error("Failed to delete agent:", err);
        toast({
          title: "Error",
          description: "Failed to delete agent.",
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
          is_active: false, // Duplicates are inactive by default
          signalwire_phone_number: null // Phone number must be unique, so clear it
        };
        await api.agents.createAgent(newAgentData);
        toast({
          title: "Agent Duplicated",
          description: "Agent duplicated successfully. It is currently inactive.",
        });
        fetchAgents(); // Re-fetch agents to update the list
      }
    } catch (err) {
      console.error("Failed to duplicate agent:", err);
      toast({
        title: "Error",
        description: err.response?.data?.detail || "Failed to duplicate agent.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const AgentCard = ({ agent }) => (
    <Card className="relative group hover:shadow-md transition-shadow duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              agent.is_active 
                ? 'bg-emerald-100 text-emerald-600' 
                : 'bg-gray-100 text-gray-400'
            }`}>
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <CardTitle className="text-lg">{agent.name}</CardTitle>
              <div className="flex items-center space-x-2 mt-1">
                <Badge 
                  variant="secondary"
                  className={agent.is_active 
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                    : 'bg-gray-50 text-gray-600 border-gray-200'
                  }
                >
                  {agent.is_active ? 'Active' : 'Inactive'}
                </Badge>
                {agent.signalwire_phone_number && (
                  <Badge variant="outline" className="text-xs">
                    <Phone className="w-3 h-3 mr-1" />
                    {agent.signalwire_phone_number}
                  </Badge>
                )}
              </div>
            </div>
          </div>
          
          {/* Actions dropdown placeholder */}
          <div className="opacity-0 group-hover:opacity-100 transition-opacity">
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
          {agent.description}
        </p>
        
        <div className="grid grid-cols-2 gap-4 text-xs text-gray-500 mb-4">
          <div>
            <span className="font-medium">Model:</span>
            <p className="mt-1">{agent.llm_model}</p>
          </div>
          <div>
            <span className="font-medium">Voice:</span>
            <p className="mt-1">{agent.tts_voice}</p>
          </div>
        </div>
        
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => toggleAgentStatus(agent.id, agent.is_active)}
              className={agent.is_active ? 'text-orange-600 hover:text-orange-700' : 'text-emerald-600 hover:text-emerald-700'}
              disabled={loading}
            >
              {agent.is_active ? (
                <>
                  <Pause className="w-4 h-4 mr-1" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-1" />
                  Start
                </>
              )}
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={() => duplicateAgent(agent.id)}
              className="text-gray-600 hover:text-gray-700"
              disabled={loading}
            >
              <Copy className="w-4 h-4" />
            </Button>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm" asChild disabled={loading}>
              <Link to={`/agents/${agent.id}`}>
                <Edit className="w-4 h-4" />
              </Link>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => deleteAgent(agent.id)}
              className="text-red-600 hover:text-red-700"
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
      <div className="p-6 space-y-6 text-center">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Agents</h1>
            <p className="text-gray-500 mt-1">Manage your AI calling agents and configurations</p>
          </div>
          <Button asChild className="mt-4 sm:mt-0 bg-emerald-600 hover:bg-emerald-700" disabled>
            <Link to="/agents/new">
              <Plus className="w-4 h-4 mr-2" />
              Create Agent
            </Link>
          </Button>
        </div>
        <div className="flex items-center justify-center py-12">
          <p>Loading agents...</p> {/* Simple loading indicator */}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 space-y-6 text-center text-red-600">
        <h1 className="text-2xl font-bold text-gray-900">AI Agents</h1>
        <p>{error}</p>
        <Button onClick={fetchAgents}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Agents</h1>
          <p className="text-gray-500 mt-1">Manage your AI calling agents and configurations</p>
        </div>
        <Button asChild className="mt-4 sm:mt-0 bg-emerald-600 hover:bg-emerald-700" disabled={loading}>
          <Link to="/agents/new">
            <Plus className="w-4 h-4 mr-2" />
            Create Agent
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Search agents by name or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
            disabled={loading}
          />
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant={filterStatus === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterStatus('all')}
            disabled={loading}
          >
            All ({agents.length})
          </Button>
          <Button
            variant={filterStatus === 'active' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterStatus('active')}
            className={filterStatus === 'active' ? 'bg-emerald-600 hover:bg-emerald-700' : ''}
            disabled={loading}
          >
            Active ({agents.filter(a => a.is_active).length})
          </Button>
          <Button
            variant={filterStatus === 'inactive' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterStatus('inactive')}
            disabled={loading}
          >
            Inactive ({agents.filter(a => !a.is_active).length})
          </Button>
        </div>
      </div>

      {/* Agents Grid */}
      {filteredAgents.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredAgents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <Bot className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchQuery || filterStatus !== 'all' ? 'No agents found' : 'No agents created yet'}
          </h3>
          <p className="text-gray-500 mb-6">
            {searchQuery || filterStatus !== 'all' 
              ? 'Try adjusting your search or filters to find what you\'re looking for.'
              : 'Get started by creating your first AI calling agent.'
            }
          </p>
          {(!searchQuery && filterStatus === 'all') && (
            <Button asChild className="bg-emerald-600 hover:bg-emerald-700" disabled={loading}>
              <Link to="/agents/new">
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Agent
              </Link>
            </Button>
          )}
        </div>
      )}
    </div>
  );
};

export default AgentList;
