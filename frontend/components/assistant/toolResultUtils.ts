import type { Field, ToolPayload } from "@/components/assistant/types";

export function parseToolResult(result: unknown): ToolPayload {
  if (typeof result === "string") {
    try {
      const parsed = JSON.parse(result);
      return isRecord(parsed) ? parsed : { data: parsed };
    } catch {
      return { message: result };
    }
  }

  if (isRecord(result)) {
    return result;
  }

  return {};
}

export function getPath(source: unknown, path: string): unknown {
  if (!path) return undefined;

  return path.split(".").reduce<unknown>((current, segment) => {
    if (current === undefined || current === null) return undefined;
    if (Array.isArray(current)) return current[Number(segment)];
    if (isRecord(current)) return current[segment];
    return undefined;
  }, source);
}

export function resolveField(field: Field, data: unknown, payload: ToolPayload) {
  return {
    label: field.label,
    value: field.value ? field.value(data, payload) : getPath(data, field.path ?? ""),
  };
}

export function arrayLength(source: unknown, path: string): number | undefined {
  const value = getPath(source, path);
  return Array.isArray(value) ? value.length : undefined;
}

export function skuSpec(source: unknown): string | undefined {
  const color = getPath(source, "products.0.skus.0.sku.color");
  const size = getPath(source, "products.0.skus.0.sku.size_or_version");
  return [color, size].filter(Boolean).join(" / ") || undefined;
}

export function inventoryTotal(source: unknown, field: string): number | undefined {
  const inventory = getPath(source, "products.0.skus.0.inventory");
  if (!Array.isArray(inventory)) return undefined;

  return inventory.reduce((total, item) => {
    const value = isRecord(item) ? Number(item[field] ?? 0) : 0;
    return total + value;
  }, 0);
}

export function firstRestockEta(source: unknown): string | undefined {
  const inventory = getPath(source, "products.0.skus.0.inventory");
  if (!Array.isArray(inventory)) return undefined;

  for (const item of inventory) {
    if (isRecord(item) && typeof item.restock_eta === "string" && item.restock_eta) {
      return item.restock_eta;
    }
  }

  return "暂无补货计划";
}

export function yesNo(value: unknown): string | undefined {
  if (typeof value !== "boolean") return undefined;
  return value ? "是" : "否";
}

export function hasDisplayValue(value: unknown): boolean {
  return value !== undefined && value !== null && value !== "";
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
