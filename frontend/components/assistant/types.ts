import type { ReactNode } from "react";

export type ToolPayload = {
  status?: string;
  message?: string;
  data?: unknown;
};

export type Field = {
  label: string;
  path?: string;
  value?: (data: unknown, payload: ToolPayload) => unknown;
};

export type ToolCardConfig = {
  toolName: string;
  title: string;
  fields: Field[];
};

export type MessageTextProps = {
  children?: ReactNode;
};
