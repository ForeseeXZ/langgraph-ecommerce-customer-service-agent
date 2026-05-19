/* eslint-disable @typescript-eslint/no-explicit-any */
export function RefundCard({ data }: { data: any }) {
  if (!data) return null;

  const eligible = data.eligible;
  const orderStatus = data.order_status;
  const reason = data.reason;
  const suggestedAction = data.suggested_next_action;

  const actionLabels: Record<string, string> = {
    create_after_sales_ticket: "创建售后工单",
    query_after_sales_ticket: "查询现有工单",
    manual_review: "人工审核",
    none: "无法继续",
  };

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white text-sm shadow-md shadow-slate-200/70">
      <div className="flex items-center justify-between border-b border-slate-100 bg-[linear-gradient(90deg,#f8fafc,#ecfeff)] px-4 py-3">
        <span className="font-semibold text-slate-950">退款资格预判断</span>
        <span
          className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-semibold ${
            eligible ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"
          }`}
        >
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              eligible ? "bg-emerald-500" : "bg-rose-500"
            }`}
          />
          {eligible ? "可继续" : "不可继续"}
        </span>
      </div>

      <div className="space-y-3 px-4 py-3">
        <div className="flex flex-wrap gap-2">
          <StatusChip label="订单状态" value={orderStatus} />
          {data.days_since_signed !== undefined && data.days_since_signed !== null ? (
            <StatusChip label="签收天数" value={`${data.days_since_signed} 天`} />
          ) : null}
          <StatusChip label="售后状态" value={data.after_sales_status} />
          <StatusChip
            label="建议动作"
            value={suggestedAction ? actionLabels[suggestedAction] || suggestedAction : undefined}
          />
        </div>

        {reason ? (
          <div className="rounded bg-slate-50 px-3 py-2 text-sm leading-6 text-slate-700">
            {reason}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function StatusChip({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return (
    <span className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-600">
      <span className="text-slate-400">{label} </span>
      <span className="font-medium text-slate-900">{value}</span>
    </span>
  );
}
