"use client";

import { useMemo, useState } from "react";

import { ChatWorkspace } from "@/components/chat/chat-workspace";
import { KnowledgePanel } from "@/components/chat/knowledge-panel";
import { MemoryPanel } from "@/components/chat/memory-panel";
import { RuntimeProvider } from "@/components/chat/runtime-provider";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

export function ClientShell() {
  const [userId, setUserId] = useState(
    process.env.NEXT_PUBLIC_DEFAULT_USER_ID || "demo-user",
  );
  const [useRag, setUseRag] = useState(true);
  const [retrieveK, setRetrieveK] = useState("3");
  const numericRetrieveK = useMemo(() => {
    const parsed = Number.parseInt(retrieveK, 10);
    return Number.isNaN(parsed) ? 3 : Math.max(parsed, 1);
  }, [retrieveK]);

  return (
    <main className="mx-auto flex min-h-screen max-w-[1600px] flex-col gap-6 px-4 py-6 md:px-6">
      <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <Card className="border-none bg-card/80 shadow-panel backdrop-blur">
          <CardHeader className="space-y-3">
            <div className="flex items-center gap-3">
              <Badge>Next.js</Badge>
              <Badge variant="secondary">assistant-ui</Badge>
              <Badge variant="secondary">shadcn/ui style</Badge>
            </div>
            <CardTitle className="text-3xl font-semibold tracking-tight">
              AI Agent Console
            </CardTitle>
            <p className="max-w-3xl text-sm text-muted-foreground">
              A frontend shell for your FastAPI agent. It already maps to
              `/chat`, `/memory/{'{user_id}'}`, `/knowledge/add`, and `/stats/{'{user_id}'}`.
            </p>
          </CardHeader>
        </Card>

        <Card className="border-none bg-card/75 shadow-panel backdrop-blur">
          <CardHeader>
            <CardTitle className="text-lg">Session Controls</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-2">
              <Label htmlFor="user-id">User ID</Label>
              <Input
                id="user-id"
                value={userId}
                onChange={(event) => setUserId(event.target.value)}
                placeholder="demo-user"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="retrieve-k">Retrieve K</Label>
              <Input
                id="retrieve-k"
                value={retrieveK}
                onChange={(event) => setRetrieveK(event.target.value)}
                inputMode="numeric"
              />
            </div>
            <div className="col-span-full flex items-center justify-between rounded-2xl border bg-secondary/50 px-4 py-3">
              <div>
                <p className="font-medium">Use RAG</p>
                <p className="text-sm text-muted-foreground">
                  Toggle knowledge retrieval for the current session.
                </p>
              </div>
              <Switch checked={useRag} onCheckedChange={setUseRag} />
            </div>
            <div className="col-span-full rounded-2xl border bg-background/70 px-4 py-3 text-sm text-muted-foreground">
              The chat center talks to your current FastAPI `/chat` endpoint. The side
              panels map to memory, conversation, knowledge, and stats endpoints so the
              frontend is useful even before adding streaming.
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid-shell gap-4">
        <MemoryPanel userId={userId} />
        <RuntimeProvider userId={userId} useRag={useRag} retrieveK={numericRetrieveK}>
          <ChatWorkspace />
        </RuntimeProvider>
        <KnowledgePanel userId={userId} />
      </section>
    </main>
  );
}
