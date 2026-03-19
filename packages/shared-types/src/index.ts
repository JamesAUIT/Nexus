// Shared types and enums for Cloud Nexus

export const CONNECTOR_TYPES = [
  "netbox",
  "proxmox",
  "vsphere",
  "pure",
  "idrac",
  "cohesity",
  "pbs",
  "vyos",
  "ad",
] as const;
export type ConnectorType = (typeof CONNECTOR_TYPES)[number];

export type RoleName = "admin" | "operator" | "viewer";
