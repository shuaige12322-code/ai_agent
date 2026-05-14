"use client";

import {
  ComposerPrimitive,
  MessagePrimitive,
  MessagePartPrimitive,
  ThreadPrimitive,
} from "@assistant-ui/react";
import { ArrowUpIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export function ChatWorkspace() {
  return (
    <Card className="border-none bg-card/80 shadow-panel backdrop-blur">
      <ThreadPrimitive.Root className="flex h-[calc(100vh-240px)] min-h-[680px] flex-col">
        <ThreadPrimitive.Viewport className="flex flex-1 flex-col overflow-y-auto px-5 py-5">
          <ThreadPrimitive.Empty>
            <EmptyState />
          </ThreadPrimitive.Empty>

          <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-5">
            <ThreadPrimitive.Messages
              components={{
                UserMessage,
                AssistantMessage,
              }}
            />
          </div>
        </ThreadPrimitive.Viewport>

        <div className="border-t bg-background/70 px-5 py-4 backdrop-blur">
          <div className="mx-auto flex w-full max-w-4xl items-end gap-3 rounded-[28px] border bg-card p-3 shadow-sm">
            <ComposerPrimitive.Input
              rows={1}
              autoFocus
              placeholder="Ask about code, memories, or knowledge documents..."
              className="max-h-40 min-h-[52px] flex-1 resize-none bg-transparent px-2 py-3 text-sm outline-none placeholder:text-muted-foreground"
            />
            <ComposerPrimitive.Send asChild>
              <Button size="icon" className="h-12 w-12 rounded-full">
                <ArrowUpIcon className="h-4 w-4" />
              </Button>
            </ComposerPrimitive.Send>
          </div>
        </div>
      </ThreadPrimitive.Root>
    </Card>
  );
}

function EmptyState() {
  return (
    <div className="mx-auto flex h-full w-full max-w-4xl flex-1 flex-col justify-center gap-5 rounded-[32px] border border-dashed bg-secondary/30 p-8">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
        Agent Session
      </p>
      <h2 className="max-w-2xl text-4xl font-semibold leading-tight">
        Ask the agent, inspect memory, and feed fresh knowledge without leaving the thread.
      </h2>
      <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
        This shell is wired for your current FastAPI backend. It uses assistant-ui&apos;s
        local runtime today and is shaped so you can upgrade the backend to a streaming
        LangGraph transport later without redesigning the interface.
      </p>
    </div>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="flex justify-end">
      <div className="max-w-[82%] rounded-[28px] bg-primary px-5 py-4 text-sm text-primary-foreground">
        <MessagePrimitive.Parts components={{ Text: UserTextPart }} />
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="flex justify-start">
      <div className="max-w-[86%] rounded-[28px] border bg-card px-5 py-4 text-sm shadow-sm">
        <MessagePrimitive.Parts components={{ Text: AssistantTextPart }} />
      </div>
    </MessagePrimitive.Root>
  );
}

function UserTextPart() {
  return <MessagePartPrimitive.Text component="p" className="whitespace-pre-wrap leading-7" />;
}

function AssistantTextPart() {
  return <MessagePartPrimitive.Text component="p" className="whitespace-pre-wrap leading-7" />;
}
