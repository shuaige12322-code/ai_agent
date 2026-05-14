"use client";

import type { ReactNode } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
  type ChatModelRunResult,
} from "@assistant-ui/react";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

type RuntimeProviderProps = {
  children: ReactNode;
  userId: string;
  useRag: boolean;
  retrieveK: number;
};

type StreamEvent =
  | { event: "token"; data: { delta?: string } }
  | { event: "done"; data: { status?: string } }
  | { event: "error"; data: { detail?: string } };

function extractLatestUserText(messages: Parameters<ChatModelAdapter["run"]>[0]["messages"]) {
  return [...messages]
    .reverse()
    .find((message) => message.role === "user")
    ?.content.filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("\n")
    .trim();
}

function buildPayload(userId: string, latestText: string, useRag: boolean, retrieveK: number) {
  return {
    user_id: userId,
    message: latestText,
    use_rag: useRag,
    retrieve_k: retrieveK,
  };
}

function parseSseEvents(buffer: string) {
  const events: StreamEvent[] = [];
  const parts = buffer.split("\n\n");
  const remainder = parts.pop() ?? "";

  for (const part of parts) {
    const lines = part.split(/\r?\n/);
    let eventName = "message";
    const dataLines: string[] = [];

    for (const line of lines) {
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trim());
      }
    }

    if (!dataLines.length) continue;

    try {
      const data = JSON.parse(dataLines.join("\n")) as StreamEvent["data"];
      if (eventName === "token" || eventName === "done" || eventName === "error") {
        events.push({ event: eventName, data } as StreamEvent);
      }
    } catch {
      // Ignore malformed events and keep the stream alive.
    }
  }

  return { events, remainder };
}

async function* streamResponse(
  latestText: string,
  userId: string,
  useRag: boolean,
  retrieveK: number,
  abortSignal: AbortSignal,
): AsyncGenerator<ChatModelRunResult, void> {
  const response = await fetch(`${apiBaseUrl}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(buildPayload(userId, latestText, useRag, retrieveK)),
    signal: abortSignal,
  });

  if (!response.ok) {
    throw new Error(`Backend stream failed: ${response.status} ${response.statusText}`);
  }

  if (!response.body) {
    throw new Error("Streaming response body was not available.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let accumulatedText = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parsed = parseSseEvents(buffer);
    buffer = parsed.remainder;

    for (const event of parsed.events) {
      if (event.event === "token") {
        accumulatedText += event.data.delta ?? "";
        yield {
          content: [{ type: "text", text: accumulatedText }],
          status: { type: "running" },
        };
      } else if (event.event === "error") {
        throw new Error(event.data.detail || "Streaming request failed.");
      }
    }
  }

  buffer += decoder.decode();
  const parsed = parseSseEvents(buffer);
  for (const event of parsed.events) {
    if (event.event === "token") {
      accumulatedText += event.data.delta ?? "";
    } else if (event.event === "error") {
      throw new Error(event.data.detail || "Streaming request failed.");
    }
  }

  yield {
    content: [{ type: "text", text: accumulatedText }],
    status: { type: "complete", reason: "stop" },
  };
}

async function fetchResponse(
  latestText: string,
  userId: string,
  useRag: boolean,
  retrieveK: number,
  abortSignal: AbortSignal,
): Promise<ChatModelRunResult> {
  const response = await fetch(`${apiBaseUrl}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(buildPayload(userId, latestText, useRag, retrieveK)),
    signal: abortSignal,
  });

  if (!response.ok) {
    throw new Error(`Backend request failed: ${response.status} ${response.statusText}`);
  }

  const data = (await response.json()) as { response: string };
  return {
    content: [{ type: "text", text: data.response }],
    status: { type: "complete", reason: "stop" },
  };
}

export function RuntimeProvider({
  children,
  userId,
  useRag,
  retrieveK,
}: RuntimeProviderProps) {
  const modelAdapter: ChatModelAdapter = {
    async *run({ messages, abortSignal }) {
      const latestText = extractLatestUserText(messages);

      if (!latestText) {
        yield {
          content: [{ type: "text", text: "No user message was available to send." }],
          status: { type: "complete", reason: "stop" },
        };
        return;
      }

      try {
        yield* streamResponse(latestText, userId, useRag, retrieveK, abortSignal);
      } catch (error) {
        const fallback = await fetchResponse(
          latestText,
          userId,
          useRag,
          retrieveK,
          abortSignal,
        );

        if (error instanceof Error) {
          console.warn("Falling back to non-streaming chat response:", error.message);
        }

        yield fallback;
      }
    },
  };

  const runtime = useLocalRuntime(modelAdapter);
  return <AssistantRuntimeProvider runtime={runtime}>{children}</AssistantRuntimeProvider>;
}
