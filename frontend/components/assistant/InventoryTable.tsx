/* eslint-disable @typescript-eslint/no-explicit-any */
export function InventoryTable({ data }: { data: any }) {
  const products: any[] = data?.products ?? [];
  if (products.length === 0) return null;

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white text-sm shadow-md shadow-slate-200/70">
      <div className="border-b border-slate-100 bg-[linear-gradient(90deg,#f8fafc,#ecfeff)] px-4 py-3 font-semibold text-slate-950">
        商品库存查询
      </div>
      {products.map((prod: any, pi: number) => {
        const product = prod.product ?? {};
        const skus: any[] = prod.skus ?? [];

        return (
          <div key={pi} className="border-t border-slate-100 first:border-t-0">
            <div className="flex flex-wrap items-center gap-2 bg-slate-50 px-4 py-2 text-xs text-slate-600">
              <span className="font-medium text-slate-900">{product.product_name}</span>
              <span>{product.product_id}</span>
              {product.category ? (
                <span className="rounded bg-slate-200 px-1.5 py-0.5">{product.category}</span>
              ) : null}
              <span>{product.brand}</span>
              {product.status === "缺货" ? (
                <span className="rounded bg-rose-50 px-1.5 py-0.5 font-medium text-rose-700">
                  缺货
                </span>
              ) : null}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50/50 text-left text-slate-500">
                    <th className="px-4 py-2 font-medium">SKU</th>
                    <th className="px-2 py-2 font-medium">颜色</th>
                    <th className="px-2 py-2 font-medium">规格</th>
                    <th className="px-2 py-2 font-medium">价格</th>
                    <th className="px-2 py-2 font-medium">仓库</th>
                    <th className="px-2 py-2 text-right font-medium">可用</th>
                    <th className="px-2 py-2 text-right font-medium">锁定</th>
                    <th className="px-2 py-2 text-right font-medium">安全</th>
                    <th className="px-4 py-2 font-medium">补货时间</th>
                  </tr>
                </thead>
                <tbody>
                  {skus.flatMap((skuEntry: any) => {
                    const sku = skuEntry.sku ?? {};
                    const inventory: any[] = skuEntry.inventory ?? [];
                    const rowSpan = Math.max(inventory.length, 1);
                    const rows = inventory.length > 0 ? inventory : [{}];

                    return rows.map((inv: any, ii: number) => {
                      const lowStock = Number(inv.available_stock ?? 0) < Number(inv.safety_stock ?? 0);

                      return (
                        <tr
                          key={`${sku.sku_id}-${ii}`}
                          className="border-b border-slate-50 hover:bg-slate-50/50"
                        >
                          {ii === 0 ? (
                            <>
                              <td className="px-4 py-2 font-mono text-slate-900" rowSpan={rowSpan}>
                                {sku.sku_id}
                              </td>
                              <td className="px-2 py-2 text-slate-900" rowSpan={rowSpan}>
                                {sku.color || "-"}
                              </td>
                              <td className="px-2 py-2 text-slate-900" rowSpan={rowSpan}>
                                {sku.size_or_version || "-"}
                              </td>
                              <td className="px-2 py-2 text-slate-900" rowSpan={rowSpan}>
                                ¥{sku.price}
                              </td>
                            </>
                          ) : null}
                          <td className="px-2 py-2 text-slate-900">{inv.warehouse_name || "-"}</td>
                          <td
                            className={`px-2 py-2 text-right font-mono ${
                              lowStock ? "font-bold text-rose-600" : "text-slate-900"
                            }`}
                          >
                            {inv.available_stock ?? "-"}
                          </td>
                          <td className="px-2 py-2 text-right font-mono text-slate-900">
                            {inv.locked_stock ?? "-"}
                          </td>
                          <td className="px-2 py-2 text-right font-mono text-slate-500">
                            {inv.safety_stock ?? "-"}
                          </td>
                          <td className="px-4 py-2 text-slate-900">{inv.restock_eta || "-"}</td>
                        </tr>
                      );
                    });
                  })}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
}
