"use client";

import { ThreadPrimitive, useAssistantInstructions } from "@assistant-ui/react";

import {
  ASSISTANT_INSTRUCTIONS,
  EXAMPLE_QUESTIONS,
  TOOL_GROUPS,
  WORKBENCH_METRICS,
} from "@/components/assistant/assistantData";
import { ComposerBar } from "@/components/assistant/ComposerBar";
import { AssistantMessage, UserMessage } from "@/components/assistant/MessageBubbles";
import { ToolUIs } from "@/components/assistant/ToolUIs";

export function AssistantWorkspace() {
  useAssistantInstructions(ASSISTANT_INSTRUCTIONS);

  return (
    <>
      <ToolUIs />
      <div className="grid min-h-[calc(100dvh-2rem)] grid-rows-[auto_1fr] gap-4 lg:grid-cols-[306px_minmax(0,1fr)] lg:grid-rows-1">
        <WorkbenchSidebar />
        <ThreadPanel />
      </div>
    </>
  );
}

function WorkbenchSidebar() {
  return (
    <aside className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl shadow-slate-300/30">
      <div className="bg-slate-950 px-5 py-5 text-white">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-cyan-400 text-base font-bold text-slate-950 shadow-lg shadow-cyan-500/20">
            枢
          </div>
          <div>
            <div className="text-xs font-semibold uppercase text-cyan-200">AstraCare Command</div>
            <h1 className="mt-1 text-xl font-semibold">天枢售后智能中枢</h1>
          </div>
        </div>
        <p className="mt-4 text-sm leading-6 text-slate-300">
          面向中文电商售后的多工具 Agent，连接订单事实、售后决策与 RAG 政策知识库。
        </p>
        <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
          <div className="rounded-lg border border-white/10 bg-white/10 px-2 py-2">
            <div className="font-semibold text-cyan-200">8+</div>
            <div className="mt-1 text-slate-300">工具</div>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/10 px-2 py-2">
            <div className="font-semibold text-emerald-200">20k</div>
            <div className="mt-1 text-slate-300">订单</div>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/10 px-2 py-2">
            <div className="font-semibold text-amber-200">RAG</div>
            <div className="mt-1 text-slate-300">政策</div>
          </div>
        </div>
      </div>

      <div className="space-y-4 px-5 py-4">
        <section>
          <h2 className="text-xs font-semibold uppercase text-slate-500">运行画像</h2>
          <div className="mt-3 space-y-2">
            {WORKBENCH_METRICS.map((metric) => (
              <div
                key={metric.label}
                className="rounded-lg border border-slate-200 bg-[linear-gradient(135deg,#ffffff,#f8fafc)] px-3 py-2 shadow-sm"
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs text-slate-500">{metric.label}</span>
                  <span className="text-sm font-semibold text-slate-950">{metric.value}</span>
                </div>
                <p className="mt-1 text-xs text-slate-500">{metric.detail}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-xs font-semibold uppercase text-slate-500">工具覆盖</h2>
          <div className="mt-3 space-y-3">
            {TOOL_GROUPS.map((group) => (
              <div key={group.title}>
                <div className="text-sm font-medium text-slate-900">{group.title}</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {group.items.map((item) => (
                    <span
                      key={item}
                      className="rounded-md border border-cyan-100 bg-cyan-50 px-2 py-1 text-xs font-medium text-cyan-800"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-3 shadow-sm">
          <h2 className="text-sm font-semibold text-amber-950">数据提示</h2>
          <p className="mt-1 text-xs leading-5 text-amber-900">
            新数据库使用数字 SKU，例如 377。旧的 SKU2001 这类编号只适合旧 JSON 样例。
          </p>
        </section>
      </div>
    </aside>
  );
}

function ThreadPanel() {
  return (
    <section className="min-h-0 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-xl shadow-slate-300/30">
      <ThreadPrimitive.Root className="flex h-full min-h-[680px] flex-col">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 bg-[linear-gradient(90deg,#ffffff_0%,#ecfeff_55%,#fff7ed_100%)] px-5 py-4">
          <div>
            <div className="text-xs font-semibold uppercase text-cyan-700">Decision Console</div>
            <h2 className="mt-1 text-lg font-semibold text-slate-950">智能售后决策会话</h2>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="rounded-md bg-emerald-50 px-2 py-1 font-medium text-emerald-700">
              SQLite 已接入
            </span>
            <span className="rounded-md bg-cyan-50 px-2 py-1 font-medium text-cyan-700">
              RAG 政策检索
            </span>
          </div>
        </div>

        <ThreadPrimitive.Viewport className="flex-1 space-y-4 overflow-y-auto bg-[linear-gradient(180deg,#f8fafc_0%,#f1f5f9_100%)] px-4 py-5 md:px-6">
          <ThreadPrimitive.Empty>
            <EmptyState />
          </ThreadPrimitive.Empty>

          <ThreadPrimitive.Messages
            components={{
              UserMessage,
              AssistantMessage,
            }}
          />
        </ThreadPrimitive.Viewport>

        <ComposerBar />
      </ThreadPrimitive.Root>
    </section>
  );
}

function EmptyState() {
  return (
    <div className="space-y-5">
      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="border-l-4 border-cyan-500 px-5 py-4">
          <div className="text-xs font-semibold uppercase text-cyan-700">Scenario Launcher</div>
          <h3 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
            选择一个售后场景，启动决策链路
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            样例覆盖订单物流、手机号校验、库存、退款资格、RAG 政策和工单闭环。
          </p>
        </div>
        <div className="grid border-t border-slate-100 bg-slate-50 text-xs text-slate-600 md:grid-cols-3">
          <div className="px-5 py-3">
            <span className="font-semibold text-slate-950">Step 1</span> 查询事实
          </div>
          <div className="border-t border-slate-100 px-5 py-3 md:border-l md:border-t-0">
            <span className="font-semibold text-slate-950">Step 2</span> 解释政策
          </div>
          <div className="border-t border-slate-100 px-5 py-3 md:border-l md:border-t-0">
            <span className="font-semibold text-slate-950">Step 3</span> 创建工单
          </div>
        </div>
      </div>

      <div className="grid gap-2 md:grid-cols-2">
        {EXAMPLE_QUESTIONS.map((question) => (
          <ThreadPrimitive.Suggestion
            key={question}
            prompt={question}
            method="replace"
            autoSend
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-sm leading-5 text-slate-700 shadow-sm transition hover:border-cyan-300 hover:bg-cyan-50 hover:text-cyan-950"
          >
            {question}
          </ThreadPrimitive.Suggestion>
        ))}
      </div>
    </div>
  );
}
