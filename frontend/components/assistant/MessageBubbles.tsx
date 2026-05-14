"use client";

import { MessagePrimitive } from "@assistant-ui/react";
import { makeMarkdownText } from "@assistant-ui/react-markdown";

const MarkdownText = makeMarkdownText();

export function UserMessage() {
  return (
    <MessagePrimitive.Root className="flex justify-end">
      <div className="max-w-[82%] rounded-lg rounded-br-sm bg-[linear-gradient(135deg,#0f172a,#155e75)] px-4 py-3 text-sm leading-6 text-white shadow-md shadow-slate-300">
        <MessagePrimitive.Content components={{ Text: MarkdownText }} />
      </div>
    </MessagePrimitive.Root>
  );
}

export function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="flex items-start gap-3">
      <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-950 text-xs font-semibold text-cyan-200 shadow-sm">
        枢
      </div>
      <div className="max-w-[90%] space-y-3">
        <div className="rounded-lg rounded-tl-sm bg-white px-4 py-3 text-sm leading-6 text-slate-900 shadow-sm ring-1 ring-slate-200">
          <MessagePrimitive.Content components={{ Text: MarkdownText }} />
        </div>
      </div>
    </MessagePrimitive.Root>
  );
}
