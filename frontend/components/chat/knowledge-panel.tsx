"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { StatsPanel } from "@/components/chat/stats-panel";
import { api } from "@/lib/api";

type KnowledgePanelProps = {
  userId: string;
};

export function KnowledgePanel({ userId }: KnowledgePanelProps) {
  const [source, setSource] = useState("manual-note");
  const [documents, setDocuments] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    const chunks = documents
      .split("\n---\n")
      .map((item) => item.trim())
      .filter(Boolean);

    if (chunks.length === 0) {
      setStatus("Please provide at least one document block.");
      return;
    }

    setSubmitting(true);
    setStatus(null);
    try {
      const metadataList = chunks.map(() => ({ source }));
      const result = await api.addKnowledge({
        user_id: userId,
        documents: chunks,
        metadata_list: metadataList,
      });
      setDocuments("");
      setStatus(`Stored ${result.count} document entries in Qdrant.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Failed to add knowledge.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-[680px] flex-col gap-4">
      <Card className="border-none bg-card/80 shadow-panel backdrop-blur">
        <CardHeader className="space-y-2">
          <div className="flex items-center justify-between gap-3">
            <CardTitle className="text-lg">Knowledge Intake</CardTitle>
            <Badge>Qdrant</Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Paste documents below. Separate multiple entries with a line containing only
            <code className="mx-1 rounded bg-secondary px-1 py-0.5">---</code>.
          </p>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="grid gap-2">
            <Label htmlFor="knowledge-source">Source Label</Label>
            <Input
              id="knowledge-source"
              value={source}
              onChange={(event) => setSource(event.target.value)}
              placeholder="engineering-notes"
            />
          </div>
          <div className="grid flex-1 gap-2">
            <Label htmlFor="knowledge-documents">Documents</Label>
            <Textarea
              id="knowledge-documents"
              value={documents}
              onChange={(event) => setDocuments(event.target.value)}
              className="min-h-[320px] flex-1"
              placeholder={"Paste one or more documents here.\n---\nEach separator becomes a new stored document."}
            />
          </div>
          <Button onClick={() => void handleSubmit()} disabled={submitting}>
            {submitting ? "Uploading..." : "Add Knowledge"}
          </Button>
          {status ? <p className="text-sm text-muted-foreground">{status}</p> : null}
        </CardContent>
      </Card>

      <StatsPanel userId={userId} />
    </div>
  );
}
