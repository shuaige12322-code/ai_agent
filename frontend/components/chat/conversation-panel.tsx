"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/lib/api";
import type { ConversationMessage } from "@/lib/types";

type ConversationPanelProps = {
  userId: string;
};

export function ConversationPanel({ userId }: ConversationPanelProps) {
  const [history, setHistory] = useState<ConversationMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadHistory() {
    if (!userId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.getConversationHistory(userId);
      setHistory(result.history);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load history.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadHistory();
  }, [userId]);

  async function handleClear() {
    setClearing(true);
    setError(null);
    try {
      await api.clearConversation(userId);
      setHistory([]);
    } catch (clearError) {
      setError(clearError instanceof Error ? clearError.message : "Failed to clear history.");
    } finally {
      setClearing(false);
    }
  }

  return (
    <Card className="border-none bg-card/80 shadow-panel backdrop-blur">
      <CardHeader className="space-y-2">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-lg">Conversation History</CardTitle>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={() => void loadHistory()} disabled={loading}>
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={() => void handleClear()} disabled={clearing}>
              {clearing ? "Clearing..." : "Clear"}
            </Button>
          </div>
        </div>
        <p className="text-sm text-muted-foreground">
          Review the saved turn history for the current in-memory agent session.
        </p>
      </CardHeader>
      <CardContent>
        {error ? <p className="mb-3 text-sm text-danger">{error}</p> : null}
        <ScrollArea className="h-[280px] rounded-3xl border bg-secondary/35 p-3">
          <div className="space-y-3">
            {history.map((message, index) => (
              <div key={`${message.role}-${index}`} className="rounded-2xl bg-card p-4 shadow-sm">
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  {message.role}
                </p>
                <p className="text-sm leading-6">{message.content}</p>
              </div>
            ))}
            {!loading && history.length === 0 ? (
              <p className="p-3 text-sm text-muted-foreground">No conversation history yet.</p>
            ) : null}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
