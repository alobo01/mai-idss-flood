import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Radio,
  Phone,
  MessageSquare,
  Send,
  Users,
  Clock,
  CheckCircle,
  AlertTriangle,
  Plus,
  Search
} from 'lucide-react';
import { useCommunications, useSendCommunication } from '@/hooks/useApiData';
import type { Communication } from '@/types';
import { format } from 'date-fns';
import { useQueryClient } from '@tanstack/react-query';

interface CommunicationsPanelProps {
  className?: string;
  maxHeight?: string;
}

const channelColors: Record<string, string> = {
  'radio': 'bg-blue-100 text-blue-800 border-blue-200',
  'phone': 'bg-green-100 text-green-800 border-green-200',
  'sms': 'bg-purple-100 text-purple-800 border-purple-200',
  'email': 'bg-orange-100 text-orange-800 border-orange-200',
  'dispatch': 'bg-red-100 text-red-800 border-red-200',
};

const channelIcons: Record<string, React.ReactNode> = {
  'radio': <Radio className="h-4 w-4" />,
  'phone': <Phone className="h-4 w-4" />,
  'sms': <MessageSquare className="h-4 w-4" />,
  'email': <MessageSquare className="h-4 w-4" />,
  'dispatch': <Send className="h-4 w-4" />,
};

export function CommunicationsPanel({
  className = '',
  maxHeight = '600px'
}: CommunicationsPanelProps) {
  const [filter, setFilter] = useState<{
    channel?: string;
    sender?: string;
  }>({});

  const [showNewMessage, setShowNewMessage] = useState(false);
  const [newMessage, setNewMessage] = useState({
    channel: 'radio',
    from: 'Coordinator',
    text: '',
  });

  const { data: communications = [], isLoading, error } = useCommunications();
  const { sendCommunication } = useSendCommunication();
  const queryClient = useQueryClient();

  // Filter communications
  const filteredCommunications = communications.filter(comm => {
    if (filter.channel && comm.channel !== filter.channel) {
      return false;
    }
    if (filter.sender && !comm.from.toLowerCase().includes(filter.sender.toLowerCase())) {
      return false;
    }
    return true;
  });

  // Sort by timestamp (newest first)
  const sortedCommunications = [...filteredCommunications].sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  const handleSendMessage = async () => {
    if (!newMessage.text.trim()) return;

    try {
      await sendCommunication(newMessage);
      queryClient.invalidateQueries({ queryKey: ['communications'] });
      setNewMessage(prev => ({ ...prev, text: '' }));
      setShowNewMessage(false);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  // Get unique channels for filtering
  const uniqueChannels = Array.from(new Set(communications.map(c => c.channel)));

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MessageSquare className="h-5 w-5" />
            <span>Communications</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <Clock className="h-6 w-6 animate-spin mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">Loading communications...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MessageSquare className="h-5 w-5" />
            <span>Communications</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-red-600 py-4">
            <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
            <p>Error loading communications. Please try again.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <MessageSquare className="h-5 w-5" />
            <span>Communications</span>
            <Badge variant="secondary" className="ml-2">
              {sortedCommunications.length} messages
            </Badge>
          </CardTitle>

          <div className="flex items-center space-x-2">
            {/* Channel Filter */}
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <Search className="h-4 w-4" />
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Filter Communications</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Channel</label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      <Button
                        variant={!filter.channel ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setFilter(prev => ({ ...prev, channel: undefined }))}
                      >
                        All Channels
                      </Button>
                      {uniqueChannels.map((channel) => (
                        <Button
                          key={channel}
                          variant={filter.channel === channel ? 'default' : 'outline'}
                          size="sm"
                          onClick={() =>
                            setFilter(prev => ({
                              ...prev,
                              channel: prev.channel === channel ? undefined : channel
                            }))
                          }
                        >
                          {channel}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium">Sender</label>
                    <input
                      type="text"
                      placeholder="Filter by sender name..."
                      value={filter.sender || ''}
                      onChange={(e) => setFilter(prev => ({ ...prev, sender: e.target.value }))}
                      className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  </div>

                  {(filter.channel || filter.sender) && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setFilter({})}
                      className="w-full"
                    >
                      Clear Filters
                    </Button>
                  )}
                </div>
              </DialogContent>
            </Dialog>

            {/* New Message */}
            <Dialog open={showNewMessage} onOpenChange={setShowNewMessage}>
              <DialogTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <Plus className="h-4 w-4" />
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>New Message</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Channel</label>
                    <select
                      value={newMessage.channel}
                      onChange={(e) => setNewMessage(prev => ({ ...prev, channel: e.target.value }))}
                      className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                    >
                      <option value="radio">Radio</option>
                      <option value="phone">Phone</option>
                      <option value="sms">SMS</option>
                      <option value="email">Email</option>
                      <option value="dispatch">Dispatch</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-sm font-medium">From</label>
                    <input
                      type="text"
                      value={newMessage.from}
                      onChange={(e) => setNewMessage(prev => ({ ...prev, from: e.target.value }))}
                      className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium">Message</label>
                    <textarea
                      value={newMessage.text}
                      onChange={(e) => setNewMessage(prev => ({ ...prev, text: e.target.value }))}
                      placeholder="Enter your message..."
                      rows={4}
                      className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  </div>

                  <Button
                    onClick={handleSendMessage}
                    disabled={!newMessage.text.trim()}
                    className="w-full"
                  >
                    Send Message
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <ScrollArea className="pr-4" style={{ maxHeight }}>
          {sortedCommunications.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No communications found</p>
              <p className="text-sm mt-1">Try adjusting your filters or send a new message</p>
            </div>
          ) : (
            <div className="space-y-4">
              {sortedCommunications.map((comm) => (
                <CommunicationItem key={comm.id} communication={comm} />
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

// Individual Communication Item Component
function CommunicationItem({ communication }: { communication: Communication }) {
  const isRecent = (Date.now() - new Date(communication.timestamp).getTime()) < 5 * 60 * 1000; // Less than 5 minutes

  return (
    <div className="relative pl-6 pb-4 border-l-2 border-gray-200">
      {/* Timeline dot */}
      <div className={`absolute -left-2 top-2 w-4 h-4 rounded-full border-2 bg-white ${
        isRecent ? 'border-green-500' : 'border-gray-300'
      }`}>
        <div className={`w-2 h-2 rounded-full mx-auto mt-0.5 ${
          isRecent ? 'bg-green-500' : 'bg-gray-300'
        }`} />
      </div>

      {/* Message content */}
      <div className="rounded-lg border p-3 bg-white hover:bg-gray-50 transition-colors">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center space-x-2">
            {channelIcons[communication.channel] || <MessageSquare className="h-4 w-4" />}
            <Badge
              variant="outline"
              className={`${channelColors[communication.channel] || 'bg-gray-100 text-gray-800 border-gray-200'}`}
            >
              {communication.channel}
            </Badge>
            <span className="font-medium text-sm">{communication.from}</span>
            {isRecent && (
              <Badge variant="secondary" className="text-xs">
                <CheckCircle className="h-3 w-3 mr-1" />
                New
              </Badge>
            )}
          </div>

          <div className="text-xs text-muted-foreground">
            {format(new Date(communication.timestamp), 'MMM d, HH:mm:ss')}
          </div>
        </div>

        <p className="text-sm">{communication.text}</p>
      </div>
    </div>
  );
}