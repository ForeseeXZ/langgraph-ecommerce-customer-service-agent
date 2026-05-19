/* eslint-disable @typescript-eslint/no-explicit-any */
import { ProgressStepper } from "@/components/assistant/ProgressStepper";

const STATUS_COLORS: Record<string, string> = {
  待支付: "bg-slate-100 text-slate-700",
  待发货: "bg-amber-50 text-amber-700",
  已发货: "bg-blue-50 text-blue-700",
  运输中: "bg-cyan-50 text-cyan-700",
  派送中: "bg-blue-50 text-blue-700",
  已签收: "bg-emerald-50 text-emerald-700",
  已完成: "bg-emerald-50 text-emerald-700",
  退款成功: "bg-rose-50 text-rose-700",
  退款中: "bg-rose-50 text-rose-700",
};

export function OrderCard({ data }: { data: any }) {
  const order = data?.order ?? {};
  const customer = data?.customer ?? {};
  const payment = data?.payment ?? {};
  const items: any[] = data?.items ?? [];
  const shipment = data?.shipment ?? {};
  const events: any[] = data?.shipment_events ?? [];
  const orderId = order.order_id ?? shipment.order_id;

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white text-sm shadow-md shadow-slate-200/70">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 bg-[linear-gradient(90deg,#f8fafc,#ecfeff)] px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-950">{orderId ?? "订单详情"}</span>
          {statusBadge(order.order_status ?? shipment.delivery_status)}
        </div>
      </div>

      <div className="space-y-3 px-4 py-3">
        {customer.customer_name ? (
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span>{customer.customer_name}</span>
            {customer.member_level ? (
              <span className="rounded bg-amber-50 px-1.5 py-0.5 text-amber-700">
                {customer.member_level}
              </span>
            ) : null}
            {customer.phone_last4 ? <span>尾号 {customer.phone_last4}</span> : null}
          </div>
        ) : null}

        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
          <InfoRow label="支付" value={payment.payment_status} />
          <InfoRow label="金额" value={payment.paid_amount ? `¥${payment.paid_amount}` : undefined} />
          <InfoRow label="方式" value={payment.payment_method} />
          <InfoRow label="售后" value={order.after_sales_status} />
        </div>

        {items.length > 0 ? (
          <div>
            <div className="mb-1.5 text-xs font-semibold text-slate-500">商品明细</div>
            <div className="space-y-1.5">
              {items.map((item: any, i: number) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded bg-slate-50 px-3 py-2"
                >
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium text-slate-900">
                      {item.product_name || item.product_name_snapshot}
                    </div>
                    <div className="text-xs text-slate-500">
                      {item.sku_snapshot || item.sku_id} x {item.quantity || 1}
                    </div>
                  </div>
                  <div className="shrink-0 pl-3 text-right text-sm text-slate-900">
                    ¥{item.unit_price}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {shipment.tracking_no || shipment.shipping_company || shipment.estimated_delivery ? (
          <div className="grid gap-2 rounded bg-slate-50 px-3 py-2 text-xs sm:grid-cols-3">
            <ShipmentField label="物流" value={shipment.shipping_company} />
            <ShipmentField label="单号" value={shipment.tracking_no} />
            <ShipmentField label="预计" value={shipment.estimated_delivery || "-"} />
          </div>
        ) : null}

        {events.length > 0 ? (
          <div>
            <div className="mb-1 text-xs font-semibold text-slate-500">物流轨迹</div>
            <ProgressStepper events={events} />
          </div>
        ) : null}
      </div>
    </div>
  );
}

function statusBadge(status: string | undefined) {
  if (!status) return null;
  const cls = STATUS_COLORS[status] || "bg-slate-100 text-slate-700";
  return <span className={`rounded-md px-2 py-1 text-xs font-medium ${cls}`}>{status}</span>;
}

function InfoRow({ label, value }: { label: string; value?: string | number }) {
  if (!value && value !== 0) return null;
  return (
    <div className="flex gap-2">
      <span className="shrink-0 text-slate-500">{label}</span>
      <span className="font-medium text-slate-900">{value}</span>
    </div>
  );
}

function ShipmentField({ label, value }: { label: string; value?: string }) {
  return (
    <div className="min-w-0">
      <span className="text-slate-500">{label} </span>
      <span className="break-words font-medium text-slate-900">{value || "-"}</span>
    </div>
  );
}
