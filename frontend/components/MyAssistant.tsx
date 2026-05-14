"use client";

import { AssistantRuntimeProvider, useEdgeRuntime } from "@assistant-ui/react";

import { AssistantWorkspace } from "@/components/assistant/AssistantWorkspace";

export function MyAssistant() {
  const runtime = useEdgeRuntime({
    api: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/chat",
    unstable_AISDKInterop: true,
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <AssistantWorkspace />
    </AssistantRuntimeProvider>
  );
}
