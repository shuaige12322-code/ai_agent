"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import type { MemoryRecord } from "@/lib/types";
import { ConversationPanel } from "@/components/chat/conversation-panel";

type MemoryPanelProps = {
  userId: string;
};

export function MemoryPanel({ userId }: MemoryPanelProps) {
  const [memoryType, setMemoryType] = useState("user_preferences");
  const [content, setContent] = useState("");
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadMemories() {
    if (!userId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.getMemories(userId);
      setMemories(result.memories);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load memories.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadMemories();
  }, [userId]);

  async function handleAddMemory() {
    if (!content.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.addMemory({
        user_id: userId,
        memory_type: memoryType,
        content,
      });
      setContent("");
      await loadMemories();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Failed to add memory.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-[680px] flex-col gap-4">
      <Card className="border-none bg-card/80 shadow-panel backdrop-blur">
        <CardHeader className="space-y-2">
          <CardTitle className="text-lg">Memory Console</CardTitle>
          <p className="text-sm text-muted-foreground">
            Inspect and inject durable memories for the active user.
          </p>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="grid gap-2">
            <Label htmlFor="memory-type">Memory Type</Label>
            <Input
              id="memory-type"
              value={memoryType}
              onChange={(event) => setMemoryType(event.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="memory-content">Memory Content</Label>
            <Textarea
              id="memory-content"
              value={content}
              onChange={(event) => setContent(event.target.value)}
              placeholder="User prefers concise Python examples..."
            />
          </div>
          <div className="flex gap-2">
            <Button onClick={() => void handleAddMemory()} disabled={submitting}>
              {submitting ? "Saving..." : "Add Memory"}
            </Button>
            <Button variant="secondary" onClick={() => void loadMemories()} disabled={loading}>
              Refresh
            </Button>
          </div>

          {error ? <p className="text-sm text-danger">{error}</p> : null}

          <ScrollArea className="h-[320px] rounded-3xl border bg-secondary/35 p-3">
            <div className="space-y-3">
              {memories.map((memory, index) => (
                <div key={`${memory.memory_type}-${index}`} className="rounded-2xl bg-card p-4 shadow-sm">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <Badge variant="secondary">{memory.memory_type}</Badge>
                  </div>
                  <p className="text-sm leading-6">{memory.content}</p>
                </div>
              ))}
              {!loading && memories.length === 0 ? (
                <p className="p-3 text-sm text-muted-foreground">No memories found for this user yet.</p>
              ) : null}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      <ConversationPanel userId={userId} />
    </div>
  );
}
