/* eslint-disable @typescript-eslint/no-explicit-any */
import type { ReactNode } from "react";

import { ProgressStepper } from "@/components/assistant/ProgressStepper";

const PRIORITY_COLORS: Record<string, string> = {
  紧急: "bg-rose-50 text-rose-700",
  高: "bg-orange-50 text-orange-700",
  中: "bg-cyan-50 text-cyan-700",
  低: "bg-slate-100 text-slate-600",
};

export function TicketCard({ data }: { data: any }) {
  if (!data) return null;

  const bundles: any[] = data.tickets ?? (data.ticket ? [data] : []);
  if (bundles.length === 0) return null;

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white text-sm shadow-md shadow-slate-200/70">
      <div className="border-b border-slate-100 bg-[linear-gradient(90deg,#f8fafc,#ecfeff)] px-4 py-3 font-semibold text-slate-950">
        售后工单
      </div>
      {bundles.map((bundle: any, bi: number) => {
        const ticket = bundle.ticket ?? bundle;
        const events: any[] = bundle.events ?? [];
        const refunds: any[] = bundle.refunds ?? [];
        const exchanges: any[] = bundle.exchanges ?? [];
        const compensations: any[] = bundle.compensations ?? [];
        const attachments: any[] = bundle.attachments ?? [];

        return (
          <div key={bi} className="border-t border-slate-100 first:border-t-0">
            <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold text-slate-950">{ticket.ticket_id}</span>
                {priorityBadge(ticket.priority)}
                <StatusBadge status={ticket.status} />
              </div>
              {ticket.sla ? <span className="text-xs text-slate-500">{ticket.sla}</span> : null}
            </div>

            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 px-4 pb-2 text-sm">
              <InfoRow label="订单号" value={ticket.order_id} />
              <InfoRow label="问题类型" value={ticket.issue_type} />
              <InfoRow label="状态" value={ticket.status} />
              <InfoRow label="处理组" value={ticket.assigned_to} />
              <InfoRow label="联系电话" value={ticket.contact_phone} />
              <InfoRow label="客户" value={ticket.customer_name} />
            </div>

            {ticket.description ? (
              <div className="mx-4 mb-2 rounded bg-slate-50 px-3 py-2 text-xs leading-5 text-slate-600">
                {ticket.description}
              </div>
            ) : null}

            <RecordList
              title="退款记录"
              records={refunds}
              render={(rf: any, ri: number) => (
                <div
                  key={ri}
                  className="mb-1 grid grid-cols-[1fr_auto_auto] items-center gap-3 rounded bg-rose-50 px-3 py-1.5 text-xs sm:grid-cols-[1fr_auto_auto_auto]"
                >
                  <span className="text-rose-800">{rf.refund_method || "原路退回"}</span>
                  <span className="font-semibold text-rose-900">¥{rf.refund_amount}</span>
                  <span className="text-rose-600">{rf.refund_status}</span>
                  <span className="hidden text-rose-500 sm:inline">{rf.completed_at || rf.requested_at}</span>
                </div>
              )}
            />

            <RecordList
              title="换货记录"
              records={exchanges}
              render={(ex: any, ei: number) => (
                <div key={ei} className="mb-1 rounded bg-blue-50 px-3 py-1.5 text-xs text-blue-800">
                  {ex.sku_id} -&gt; {ex.replacement_sku_id} ({ex.exchange_status})
                </div>
              )}
            />

            <RecordList
              title="补偿记录"
              records={compensations}
              render={(cp: any, ci: number) => (
                <div key={ci} className="mb-1 rounded bg-amber-50 px-3 py-1.5 text-xs text-amber-800">
                  {cp.compensation_type} - ¥{cp.compensation_amount}
                </div>
              )}
            />

            {attachments.length > 0 ? (
              <div className="mx-4 mb-2 text-xs text-slate-500">
                附件：{attachments.map((a: any) => a.file_name || a.file_url).join("、")}
              </div>
            ) : null}

            {events.length > 0 ? (
              <div className="px-4 pb-3">
                <div className="mb-1 text-xs font-semibold text-slate-500">流转记录</div>
                <ProgressStepper events={events} />
              </div>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

function priorityBadge(priority: string | undefined) {
  if (!priority) return null;
  const cls = PRIORITY_COLORS[priority] || "bg-slate-100 text-slate-700";
  return <span className={`rounded-md px-2 py-0.5 text-xs font-medium ${cls}`}>{priority}</span>;
}

function StatusBadge({ status }: { status?: string }) {
  if (!status) return null;

  const colors: Record<string, string> = {
    已创建: "bg-slate-100 text-slate-700",
    待补充凭证: "bg-amber-50 text-amber-700",
    审核中: "bg-blue-50 text-blue-700",
    待寄回: "bg-purple-50 text-purple-700",
    仓库验收中: "bg-cyan-50 text-cyan-700",
    退款中: "bg-rose-50 text-rose-700",
    换货处理中: "bg-orange-50 text-orange-700",
    已完成: "bg-emerald-50 text-emerald-700",
    已关闭: "bg-slate-100 text-slate-500",
  };
  const cls = colors[status] || "bg-slate-100 text-slate-700";

  return <span className={`rounded-md px-2 py-0.5 text-xs font-medium ${cls}`}>{status}</span>;
}

function InfoRow({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return (
    <div className="flex gap-2 text-xs">
      <span className="shrink-0 text-slate-500">{label}</span>
      <span className="min-w-0 break-words font-medium text-slate-900">{value}</span>
    </div>
  );
}

function RecordList({
  title,
  records,
  render,
}: {
  title: string;
  records: any[];
  render: (record: any, index: number) => ReactNode;
}) {
  if (records.length === 0) return null;

  return (
    <div className="mx-4 mb-2">
      <div className="mb-1 text-xs font-semibold text-slate-500">{title}</div>
      {records.map(render)}
    </div>
  );
}
