import { MyAssistant } from "@/components/MyAssistant";

export default function Home() {
  return (
    <main className="min-h-dvh bg-[radial-gradient(circle_at_top_left,_rgba(251,191,36,0.22),_transparent_30%),linear-gradient(180deg,#fffaf2_0%,#fffdf8_45%,#f8fafc_100%)] px-4 py-6 md:px-8">
      <div className="mx-auto flex min-h-[calc(100dvh-3rem)] w-full max-w-6xl flex-col gap-6">
        <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="text-sm font-medium uppercase tracking-[0.25em] text-amber-700">
              Assistant UI + LangGraph + FastAPI
            </div>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950 md:text-4xl">
              电商售后智能客服 Agent 演示系统
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              面向中文电商售后课程作业的完整 demo，覆盖订单查询、库存查询、退款规则和售后工单创建。
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm text-slate-700 md:w-[360px]">
            <div className="rounded-2xl bg-white/80 px-4 py-3 shadow-sm ring-1 ring-slate-200">
              <div className="text-xs text-slate-500">Agent 类型</div>
              <div className="mt-1 font-semibold">LangGraph ReAct</div>
            </div>
            <div className="rounded-2xl bg-white/80 px-4 py-3 shadow-sm ring-1 ring-slate-200">
              <div className="text-xs text-slate-500">模型接入</div>
              <div className="mt-1 font-semibold">OpenAI-compatible API</div>
            </div>
          </div>
        </header>
        <section className="min-h-0 flex-1">
          <MyAssistant />
        </section>
      </div>
    </main>
  );
}
