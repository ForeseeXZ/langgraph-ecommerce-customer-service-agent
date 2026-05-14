import type { ReactNode } from "react";

import type { Field } from "@/components/assistant/types";
import {
  hasDisplayValue,
  isRecord,
  parseToolResult,
  resolveField,
} from "@/components/assistant/toolResultUtils";

export function ToolResultCard({
  title,
  result,
  fields,
}: {
  title: string;
  result: unknown;
  fields: Field[];
}) {
  const payload = parseToolResult(result);
  const data = payload.data ?? {};
  const status = payload.status ?? "unknown";
  const message = payload.message ?? "工具调用已完成";
  const visibleFields = fields
    .map((field) => resolveField(field, data, payload))
    .filter((field) => hasDisplayValue(field.value));

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white text-sm text-slate-800 shadow-md shadow-slate-200/70">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 bg-[linear-gradient(90deg,#f8fafc,#ecfeff)] px-4 py-3">
        <div className="font-semibold text-slate-950">{title}</div>
        <span className={statusClassName(status)}>{status}</span>
      </div>
      <div className="px-4 py-3">
        <p className="leading-6 text-slate-600">{message}</p>
        {visibleFields.length > 0 ? (
          <dl className="mt-3 grid gap-x-4 gap-y-2 border-t border-slate-100 pt-3 md:grid-cols-2">
            {visibleFields.map((field) => (
              <div key={field.label} className="grid grid-cols-[88px_minmax(0,1fr)] gap-2">
                <dt className="text-slate-500">{field.label}</dt>
                <dd className="min-w-0 break-words font-medium text-slate-950">
                  {formatValue(field.value)}
                </dd>
              </div>
            ))}
          </dl>
        ) : null}
      </div>
    </div>
  );
}

function formatValue(value: unknown): ReactNode {
  if (typeof value === "boolean") return value ? "是" : "否";
  if (Array.isArray(value)) return value.join("、");
  if (isRecord(value)) return JSON.stringify(value);
  return value as ReactNode;
}

function statusClassName(status: string): string {
  const base = "rounded-md px-2 py-1 text-xs font-medium";
  if (status === "success") return `${base} bg-emerald-50 text-emerald-700`;
  if (status === "failed" || status === "forbidden") {
    return `${base} bg-rose-50 text-rose-700`;
  }
  if (status === "not_found") return `${base} bg-slate-100 text-slate-700`;
  if (status === "database_not_ready") return `${base} bg-amber-50 text-amber-700`;
  return `${base} bg-cyan-50 text-cyan-700`;
}
