"use client";

import { ComposerPrimitive } from "@assistant-ui/react";

export function ComposerBar() {
  return (
    <div className="border-t border-slate-200 bg-white px-4 py-4 md:px-5">
      <ComposerPrimitive.Root className="rounded-lg border border-cyan-100 bg-[linear-gradient(180deg,#f8fafc,#ecfeff)] p-2 shadow-inner">
        <ComposerPrimitive.Input
          rows={3}
          placeholder="请输入售后问题，例如：帮我查一下订单 SO20260514000023 的物流状态"
          className="min-h-[88px] w-full resize-none bg-transparent px-3 py-3 text-sm leading-6 text-slate-900 outline-none placeholder:text-slate-400"
        />
        <div className="mt-2 flex flex-col gap-3 px-2 pb-1 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs leading-5 text-slate-500">
            工具优先查询，政策解释来自 RAG 知识库。
          </p>
          <ComposerPrimitive.Send className="inline-flex h-9 items-center justify-center rounded-lg bg-slate-950 px-4 text-sm font-medium text-cyan-100 shadow-sm transition hover:bg-cyan-800 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-white">
            发送
          </ComposerPrimitive.Send>
        </div>
      </ComposerPrimitive.Root>
    </div>
  );
}
