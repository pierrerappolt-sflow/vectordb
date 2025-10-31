"use client";

import { EventLog } from "@/lib/api-client";
import { formatRelativeDate } from "@/lib/format-date";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Clock, Copy, Database, FileText, X } from "lucide-react";
import { useState } from "react";

interface EventDetailModalProps {
  event: EventLog;
  onClose: () => void;
}

export function EventDetailModal({ event, onClose }: EventDetailModalProps) {
  const [copied, setCopied] = useState(false);

  const getAggregateIcon = (aggregateType: string) => {
    if (aggregateType === "Library") return Database;
    if (aggregateType === "Document") return FileText;
    return Clock;
  };

  const copyPayload = () => {
    navigator.clipboard.writeText(JSON.stringify(event.payload, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const Icon = getAggregateIcon(event.aggregate_type);

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <Icon className="h-5 w-5 text-muted-foreground" />
              <div>
                <DialogTitle className="text-xl">{event.event_type}</DialogTitle>
                <div className="mt-1 flex items-center gap-2">
                  <Badge variant="outline">{event.aggregate_type}</Badge>
                  <Badge variant="secondary" className="font-mono text-xs">
                    {event.id}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6">
          {/* Metadata section */}
          <div className="space-y-3 rounded-lg border p-4">
            <h3 className="text-sm font-semibold">Event Metadata</h3>
            <div className="grid gap-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Aggregate ID:</span>
                <span className="font-mono text-xs">{event.aggregate_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Occurred At:</span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatRelativeDate(event.occurred_at)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Created At:</span>
                <span>{formatRelativeDate(event.created_at)}</span>
              </div>
            </div>
          </div>

          {/* Payload section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Event Payload</h3>
              <Button variant="ghost" size="sm" onClick={copyPayload} className="h-8">
                <Copy className="mr-2 h-3 w-3" />
                {copied ? "Copied!" : "Copy JSON"}
              </Button>
            </div>

            <ScrollArea className="h-[300px] rounded-lg border">
              <pre className="p-4 text-xs">
                <code>{JSON.stringify(event.payload, null, 2)}</code>
              </pre>
            </ScrollArea>
          </div>

          {/* Close button */}
          <div className="flex justify-end">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
