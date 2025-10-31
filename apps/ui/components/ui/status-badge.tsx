import * as React from "react";
import { cn } from "@/lib/utils";

export type StatusVariant =
  | "success"
  | "completed"
  | "processing"
  | "running"
  | "pending"
  | "waiting"
  | "failed"
  | "error"
  | "cancelled"
  | "unknown";

interface StatusBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  status: string;
  variant?: StatusVariant;
}

/**
 * Get status variant from status string
 */
function getStatusVariant(status: string): StatusVariant {
  const normalized = status.toLowerCase().trim();

  // Success states
  if (normalized.includes("complete") || normalized.includes("success")) {
    return "completed";
  }

  // Processing states
  if (
    normalized.includes("processing") ||
    normalized.includes("running") ||
    normalized.includes("in_progress") ||
    normalized.includes("active")
  ) {
    return "processing";
  }

  // Pending states
  if (
    normalized.includes("pending") ||
    normalized.includes("waiting") ||
    normalized.includes("queued")
  ) {
    return "pending";
  }

  // Failed states
  if (
    normalized.includes("fail") ||
    normalized.includes("error") ||
    normalized.includes("reject")
  ) {
    return "failed";
  }

  // Cancelled states
  if (normalized.includes("cancel") || normalized.includes("abort")) {
    return "cancelled";
  }

  return "unknown";
}

/**
 * Get CSS classes for status variant
 */
function getStatusClasses(variant: StatusVariant): string {
  switch (variant) {
    case "completed":
    case "success":
      return "bg-green-500/10 text-green-700 dark:text-green-400";

    case "processing":
    case "running":
      return "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400";

    case "pending":
    case "waiting":
      return "bg-blue-500/10 text-blue-700 dark:text-blue-400";

    case "failed":
    case "error":
      return "bg-red-500/10 text-red-700 dark:text-red-400";

    case "cancelled":
      return "bg-gray-500/10 text-gray-700 dark:text-gray-400";

    case "unknown":
    default:
      return "bg-gray-500/10 text-gray-700 dark:text-gray-400";
  }
}

/**
 * StatusBadge - Reusable status badge component
 *
 * Automatically colorizes status based on common status keywords:
 * - Green: completed, success
 * - Yellow: processing, running, active
 * - Blue: pending, waiting, queued
 * - Red: failed, error, rejected
 * - Gray: cancelled, unknown
 *
 * @example
 * <StatusBadge status="COMPLETED" />
 * <StatusBadge status="processing" />
 * <StatusBadge status="failed" variant="failed" /> // Force variant
 */
export function StatusBadge({
  status,
  variant,
  className,
  ...props
}: StatusBadgeProps) {
  const resolvedVariant = variant ?? getStatusVariant(status);
  const variantClasses = getStatusClasses(resolvedVariant);

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-1 text-xs font-medium",
        variantClasses,
        className
      )}
      {...props}
    >
      {status}
    </span>
  );
}
