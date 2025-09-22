import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Search, PhoneCall, Clock, CalendarDays, Bot, User } from 'lucide-react';
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
      setError("Failed to load calls. Please try again.");
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
      call.from_number?.toLowerCase().includes(searchLower) ||
      call.to_number?.toLowerCase().includes(searchLower) ||
      call.status.toLowerCase().includes(searchLower) ||
      call.agent?.name?.toLowerCase().includes(searchLower) // Assuming agent name is available
    );
  });

  const formatDuration = (seconds) => {
    if (seconds === null || seconds === undefined) return 'N/A';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const CallCard = ({ call }) => (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center space-x-2">
            <PhoneCall className="w-5 h-5 text-blue-600" />
            <span>Call from {call.from_number || 'Unknown'}</span>
          </CardTitle>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            call.status === 'completed' ? 'bg-green-100 text-green-800' :
            call.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {call.status.replace('_', ' ')}
          </span>
        </div>
        <p className="text-sm text-gray-500 flex items-center space-x-1 mt-1">
          <CalendarDays className="w-3 h-3" />
          <span>{new Date(call.start_time).toLocaleString()}</span>
        </p>
      </CardHeader>
      <CardContent className="pt-0 space-y-2">
        <div className="flex items-center space-x-2 text-sm text-gray-700">
          <Bot className="w-4 h-4" />
          <span>Agent: {call.agent?.name || 'N/A'}</span> {/* Assuming agent object is nested */}
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-700">
          <User className="w-4 h-4" />
          <span>To: {call.to_number || 'N/A'}</span>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-700">
          <Clock className="w-4 h-4" />
          <span>Duration: {formatDuration(call.duration_seconds)}</span>
        </div>
        <div className="pt-4 border-t border-gray-100 flex justify-end">
          <Button variant="outline" size="sm" asChild>
            <Link to={`/calls/${call.id}`}>View Details</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  if (loading && calls.length === 0) {
    return (
      <div className="p-6 space-y-6 text-center">
        <h1 className="text-2xl font-bold text-gray-900">Call History</h1>
        <p>Loading calls...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 space-y-6 text-center text-red-600">
        <h1 className="text-2xl font-bold text-gray-900">Call History</h1>
        <p>{error}</p>
        <Button onClick={fetchCalls}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Call History</h1>
        <p className="text-gray-500 mt-1">Review past AI agent calls and transcripts</p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Search calls by number or status..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
            disabled={loading}
          />
        </div>
      </div>

      {/* Calls Grid */}
      {filteredCalls.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredCalls.map((call) => (
            <CallCard key={call.id} call={call} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <PhoneCall className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchQuery ? 'No matching calls found' : 'No calls recorded yet'}
          </h3>
          <p className="text-gray-500 mb-6">
            {searchQuery 
              ? 'Try adjusting your search to find what you\'re looking for.'
              : 'Once your agents start making or receiving calls, they will appear here.'
            }
          </p>
        </div>
      )}
    </div>
  );
};

export default CallList;
