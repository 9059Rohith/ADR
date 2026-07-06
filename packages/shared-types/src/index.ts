/**
 * SentinelArena — Shared Types & Validation Schemas
 *
 * TypeScript interfaces and Zod schemas shared between all frontend
 * applications and the API gateway. Ensures type-safe API contracts.
 *
 * @module @sentinel/shared-types
 */

import { z } from "zod";

// ============================================================
// Enums
// ============================================================

export const UserRole = {
  FAN: "fan",
  VOLUNTEER: "volunteer",
  ORGANIZER: "organizer",
  ADMIN: "admin",
} as const;
export type UserRole = (typeof UserRole)[keyof typeof UserRole];

export const Locale = {
  EN: "en",
  HI: "hi",
  TA: "ta",
  TE: "te",
  ES: "es",
} as const;
export type Locale = (typeof Locale)[keyof typeof Locale];

export const LOCALE_LABELS: Record<Locale, string> = {
  en: "English",
  hi: "हिन्दी",
  ta: "தமிழ்",
  te: "తెలుగు",
  es: "Español",
};

export const ZoneSeverity = {
  NORMAL: "normal",
  WARNING: "warning",
  CRITICAL: "critical",
  EMERGENCY: "emergency",
} as const;
export type ZoneSeverity = (typeof ZoneSeverity)[keyof typeof ZoneSeverity];

export const IncidentStatus = {
  REPORTED: "reported",
  ACKNOWLEDGED: "acknowledged",
  IN_PROGRESS: "in_progress",
  RESOLVED: "resolved",
  CLOSED: "closed",
} as const;
export type IncidentStatus =
  (typeof IncidentStatus)[keyof typeof IncidentStatus];

export const DecisionStatus = {
  PENDING: "pending",
  APPROVED: "approved",
  REJECTED: "rejected",
  EDITED: "edited",
} as const;
export type DecisionStatus =
  (typeof DecisionStatus)[keyof typeof DecisionStatus];

// ============================================================
// Zod Schemas (Runtime Validation)
// ============================================================

export const ChatRequestSchema = z.object({
  message: z.string().min(1).max(2000),
  locale: z.enum(["en", "hi", "ta", "te", "es"]).default("en"),
  user_location_id: z.string().default("lobby-main"),
});
export type ChatRequest = z.infer<typeof ChatRequestSchema>;

export const ChatResponseSchema = z.object({
  response: z.string(),
  intent: z.string(),
  locale: z.string(),
  sources: z.array(z.string()).default([]),
  route_data: z.record(z.unknown()).nullable().optional(),
  density_data: z.array(z.record(z.unknown())).nullable().optional(),
});
export type ChatResponse = z.infer<typeof ChatResponseSchema>;

export const ZoneDensitySchema = z.object({
  zone_id: z.string(),
  zone_name: z.string(),
  current_density_pct: z.number(),
  ewma_density_pct: z.number(),
  trend_direction: z.enum(["rising", "falling", "stable"]),
  trend_rate_pct_per_min: z.number(),
  severity: z.enum(["normal", "warning", "critical", "emergency"]),
  projected_time_to_threshold_min: z.number().nullable(),
  current_count: z.number(),
  capacity: z.number(),
  timestamp: z.string(),
});
export type ZoneDensity = z.infer<typeof ZoneDensitySchema>;

export const CrowdOverviewSchema = z.object({
  zones: z.array(ZoneDensitySchema),
  overall_severity: z.string(),
  timestamp: z.string(),
});
export type CrowdOverview = z.infer<typeof CrowdOverviewSchema>;

export const NavigationRequestSchema = z.object({
  query: z.string().min(1).max(500),
  from_location_id: z.string().default("lobby-main"),
  to_location_id: z.string().nullable().optional(),
  avoid_stairs: z.boolean().default(false),
  wheelchair_accessible: z.boolean().default(false),
  avoid_congestion: z.boolean().default(false),
  locale: z.enum(["en", "hi", "ta", "te", "es"]).default("en"),
});
export type NavigationRequest = z.infer<typeof NavigationRequestSchema>;

export const RouteNodeSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.string(),
  floor: z.number(),
  x: z.number(),
  y: z.number(),
});
export type RouteNode = z.infer<typeof RouteNodeSchema>;

export const RouteStepSchema = z.object({
  from: z.string(),
  to: z.string(),
  distance_m: z.number(),
  accessibility: z.string(),
  floor_change: z.number(),
});
export type RouteStep = z.infer<typeof RouteStepSchema>;

export const RouteDataSchema = z.object({
  total_distance_meters: z.number(),
  total_distance_display: z.string(),
  estimated_time_seconds: z.number(),
  estimated_time_display: z.string(),
  is_accessible: z.boolean(),
  num_steps: z.number(),
  nodes: z.array(RouteNodeSchema),
  steps: z.array(RouteStepSchema),
});
export type RouteData = z.infer<typeof RouteDataSchema>;

export const IncidentCreateSchema = z.object({
  title: z.string().min(3).max(300),
  description: z.string().min(10).max(5000),
  severity: z.enum(["low", "medium", "high", "critical"]).default("medium"),
  zone_id: z.string().default("zone-a"),
  locale: z.enum(["en", "hi", "ta", "te", "es"]).default("en"),
});
export type IncidentCreate = z.infer<typeof IncidentCreateSchema>;

export const DecisionRequestSchema = z.object({
  query: z.string().min(1).max(2000),
  locale: z.enum(["en", "hi", "ta", "te", "es"]).default("en"),
});
export type DecisionRequest = z.infer<typeof DecisionRequestSchema>;

export const AuthResponseSchema = z.object({
  user_id: z.string(),
  email: z.string(),
  display_name: z.string(),
  role: z.string(),
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.string(),
  expires_in: z.number(),
});
export type AuthResponse = z.infer<typeof AuthResponseSchema>;

// ============================================================
// Severity Color Mapping
// ============================================================

export const SEVERITY_COLORS: Record<ZoneSeverity, string> = {
  normal: "#22c55e",
  warning: "#f59e0b",
  critical: "#f97316",
  emergency: "#ef4444",
};

export const SEVERITY_BG_COLORS: Record<ZoneSeverity, string> = {
  normal: "rgba(34, 197, 94, 0.15)",
  warning: "rgba(245, 158, 11, 0.15)",
  critical: "rgba(249, 115, 22, 0.15)",
  emergency: "rgba(239, 68, 68, 0.15)",
};
