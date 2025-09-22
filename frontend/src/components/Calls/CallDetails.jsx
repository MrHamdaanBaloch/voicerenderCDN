import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { ArrowLeft, PhoneCall, Clock, CalendarDays, Bot, User, MessageSquareText, Download } from 'lucide-react';
import api from '../../services/api';
import { useToast } from '../../hooks/use-toast';

const CallDetails = () => {
  const { id } = useParams();
  const [call, setCall] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { toast } = useToast();

  const fetchCallDetails = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.calls.getCallDetails(id);
      setCall(response.data);
    } catch (err) {
      console.error("Failed to fetch call details:", err);
      setError("Failed to load call details. Please try again.");
      toast({
        title: "Error",
        description: "Failed to load call details.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [id, toast]);

  useEffect(() => {
    fetchCallDetails();
  }, [fetchCallDetails]);

  const formatDuration = (seconds) => {
    if (seconds === null || seconds === undefined) return 'N/A';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6 text-center">
        <h1 className="text-2xl font-bold text-gray-900">Call Details</h1>
        <p>Loading call details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 space-y-6 text-center text-red-600">
        <h1 className="text-2xl font-bold text-gray-900">Call Details</h1>
        <p>{error}</p>
        <Button onClick={fetchCallDetails}>Retry</Button>
      </div>
    );
  }

  if (!call) {
    return (
      <div className="p-6 space-y-6 text-center">
        <h1 className="text-2xl font-bold text-gray-900">Call Details</h1>
        <p>Call not found.</p>
        <Button asChild>
          <Link to="/calls">Back to Call History</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" asChild>
            <Link to="/calls">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Calls
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Call Details</h1>
            <p className="text-gray-500">Detailed information for call ID: {call.id}</p>
          </div>
        </div>
        {call.audio_url && (
          <Button asChild variant="outline">
            <a href={call.audio_url} download>
              <Download className="w-4 h-4 mr-2" />
              Download Audio
            </a>
          </Button>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <PhoneCall className="w-5 h-5 text-blue-600" />
            <span>Call Overview</span>
          </CardTitle>
          <CardDescription>Key information about this voice interaction.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="space-y-1">
            <p className="font-medium text-gray-700">From Number:</p>
            <p className="text-gray-900">{call.from_number || 'N/A'}</p>
          </div>
          <div className="space-y-1">
            <p className="font-medium text-gray-700">To Number:</p>
            <p className="text-gray-900">{call.to_number || 'N/A'}</p>
          </div>
          <div className="space-y-1">
            <p className="font-medium text-gray-700">Agent:</p>
            <p className="text-gray-900 flex items-center space-x-1">
              <Bot className="w-4 h-4" />
              <span>{call.agent?.name || 'N/A'}</span>
            </p>
          </div>
          <div className="space-y-1">
            <p className="font-medium text-gray-700">Status:</p>
            <p className={`text-gray-900 ${
              call.status === 'completed' ? 'text-green-600' :
              call.status === 'in_progress' ? 'text-yellow-600' :
              'text-gray-600'
            }`}>
              {call.status.replace('_', ' ')}
            </p>
          </div>
          <div className="space-y-1">
            <p className="font-medium text-gray-700">Start Time:</p>
            <p className="text-gray-900">{new Date(call.start_time).toLocaleString()}</p>
          </div>
          <div className="space-y-1">
            <p className="font-medium text-gray-700">End Time:</p>
            <p className="text-gray-900">{call.end_time ? new Date(call.end_time).toLocaleString() : 'In Progress'}</p>
          </div>
          <div className="space-y-1">
            <p className="font-medium text-gray-700">Duration:</p>
            <p className="text-gray-900">{formatDuration(call.duration_seconds)}</p>
          </div>
          <div className="space-y-1">
            <p className="font-medium text-gray-700">Organization ID:</p>
            <p className="text-gray-900">{call.organization_id}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MessageSquareText className="w-5 h-5" />
            <span>Transcript</span>
          </CardTitle>
          <CardDescription>Full conversation log.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {call.transcripts && call.transcripts.length > 0 ? (
            <div className="space-y-3">
              {call.transcripts.map((transcript, index) => (
                <div key={transcript.id || index} className={`flex ${transcript.speaker === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[70%] p-3 rounded-lg ${
                    transcript.speaker === 'user'
                      ? 'bg-blue-500 text-white rounded-br-none'
                      : 'bg-gray-200 text-gray-800 rounded-bl-none'
                  }`}>
                    <p className="font-medium text-xs mb-1">
                      {transcript.speaker === 'user' ? 'You' : 'Agent'}
                    </p>
                    <p className="text-sm">{transcript.text}</p>
                    <p className="text-xs text-right mt-1 opacity-75">
                      {new Date(transcript.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No transcript available for this call yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default CallDetails;
