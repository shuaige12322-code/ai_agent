"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { MemoryStatsResponse } from "@/lib/types";

type StatsPanelProps = {
  userId: string;
};

export function StatsPanel({ userId }: StatsPanelProps) {
  const [stats, setStats] = useState<MemoryStatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadStats() {
    if (!userId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.getStats(userId);
      setStats(result);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load stats.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadStats();
  }, [userId]);

  const byType = stats?.memory_stats.by_type ?? {};

  return (
    <Card className="border-none bg-card/80 shadow-panel backdrop-blur">
      <CardHeader className="space-y-2">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-lg">User Stats</CardTitle>
          <Button variant="secondary" size="sm" onClick={() => void loadStats()} disabled={loading}>
            Refresh
          </Button>
        </div>
        <p className="text-sm text-muted-foreground">
          Monitor memory totals and current session length for the active user.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {error ? <p className="text-sm text-danger">{error}</p> : null}

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-3xl border bg-secondary/35 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Total Memories
            </p>
            <p className="mt-2 text-3xl font-semibold">
              {stats?.memory_stats.total_memories ?? 0}
            </p>
          </div>
          <div className="rounded-3xl border bg-secondary/35 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Conversation Length
            </p>
            <p className="mt-2 text-3xl font-semibold">
              {stats?.conversation_length ?? 0}
            </p>
          </div>
        </div>

        <div className="rounded-3xl border bg-secondary/35 p-4">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Memory Types
          </p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(byType).map(([type, count]) => (
              <Badge key={type} variant="secondary">
                {type}: {count}
              </Badge>
            ))}
            {Object.keys(byType).length === 0 ? (
              <p className="text-sm text-muted-foreground">No memory statistics yet.</p>
            ) : null}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
