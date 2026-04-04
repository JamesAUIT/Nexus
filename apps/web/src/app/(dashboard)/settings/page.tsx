"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch, apiUrl } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

type PlatformSettings = {
  api_version: string;
  demo_mode: boolean;
  cors_origins: string[];
  cors_enabled: boolean;
  trusted_proxy: boolean;
  log_json: boolean;
  production_refuse_insecure_defaults: boolean;
  auth_login_rate_limit: string;
  report_storage_dir: string;
  oidc_configured: boolean;
  ldap_configured: boolean;
  smtp_configured: boolean;
  haproxy_ssh_configured: boolean;
  automation_runner_configured: boolean;
};

type ConnectorHealth = {
  id: number;
  type: string;
  name: string;
  base_url: string | null;
  status: string;
  last_ok_at: string | null;
  last_error: string | null;
  data_freshness_minutes: number | null;
  sync_status: string | null;
  sync_last_run_at: string | null;
};

type ConnectorTypeOption = { type: string; label: string; config_hint: string };

const DEFAULT_CONFIG: Record<string, string> = {
  netbox: '{\n  "url": "https://netbox.example.com",\n  "token": "",\n  "verify_ssl": true\n}',
  proxmox: '{\n  "url": "https://pve.example.com:8006",\n  "user": "root@pam",\n  "password": "",\n  "verify_ssl": false\n}',
  vsphere: '{\n  "host": "vcenter.example.com",\n  "user": "",\n  "password": "",\n  "verify_ssl": true\n}',
  vyos: '{\n  "host": "router.example.com",\n  "user": "",\n  "password": "",\n  "port": 22\n}',
  ad: '{\n  "url": "ldaps://dc.example.com",\n  "bind_dn": "",\n  "bind_password": "",\n  "base_dn": "DC=example,DC=com"\n}',
};

function AddConnectorForm({ token }: { token: string | null }) {
  const queryClient = useQueryClient();
  const [type, setType] = useState<keyof typeof DEFAULT_CONFIG>("netbox");
  const [name, setName] = useState("");
  const [configJson, setConfigJson] = useState(DEFAULT_CONFIG.netbox);
  const [cron, setCron] = useState("0 */6 * * *");
  const [createJob, setCreateJob] = useState(true);
  const [formError, setFormError] = useState("");

  const { data: typeOptions = [] } = useQuery({
    queryKey: ["connector-types"],
    queryFn: () => apiFetch<ConnectorTypeOption[]>("/api/v1/connectors/types", { token }),
    enabled: !!token,
  });

  useEffect(() => {
    if (DEFAULT_CONFIG[type]) {
      setConfigJson(DEFAULT_CONFIG[type]);
    }
  }, [type]);

  const createMut = useMutation({
    mutationFn: async () => {
      let cfg: Record<string, unknown>;
      try {
        cfg = JSON.parse(configJson) as Record<string, unknown>;
      } catch {
        throw new Error("Config must be valid JSON");
      }
      return apiFetch<{ id: number }>("/api/v1/connectors", {
        method: "POST",
        token,
        body: JSON.stringify({
          type,
          name: name.trim(),
          config_plain: cfg,
          schedule_cron: cron.trim() || null,
          create_sync_job: createJob,
        }),
      });
    },
    onSuccess: () => {
      setFormError("");
      setName("");
      queryClient.invalidateQueries({ queryKey: ["connector-health"] });
      queryClient.invalidateQueries({ queryKey: ["sync-jobs"] });
    },
    onError: (e: unknown) => {
      setFormError(e instanceof Error ? e.message : "Failed to create connector");
    },
  });

  if (!token) return null;

  return (
    <div className="rounded-lg border bg-muted/20 p-4 space-y-4 mb-6">
      <div>
        <h3 className="text-sm font-medium">Add connector</h3>
        <p className="text-xs text-muted-foreground mt-1">
          Credentials are encrypted at rest. The API must reach the target network from its deployment.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="conn-type">Type</Label>
          <select
            id="conn-type"
            className={cn(
              "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
              "ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            )}
            value={type}
            onChange={(e) => setType(e.target.value as keyof typeof DEFAULT_CONFIG)}
          >
            {(typeOptions.length ? typeOptions : Object.keys(DEFAULT_CONFIG).map((t) => ({ type: t, label: t }))).map(
              (opt) => (
                <option key={opt.type} value={opt.type}>
                  {"label" in opt && opt.label ? opt.label : opt.type}
                </option>
              )
            )}
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="conn-name">Display name</Label>
          <Input
            id="conn-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="NetBox production"
            required
          />
        </div>
      </div>
      <div className="space-y-2">
        <Label htmlFor="conn-config">Config (JSON)</Label>
        <textarea
          id="conn-config"
          className={cn(
            "flex min-h-[160px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono",
            "ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          )}
          value={configJson}
          onChange={(e) => setConfigJson(e.target.value)}
          spellCheck={false}
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 items-end">
        <div className="space-y-2">
          <Label htmlFor="conn-cron">Schedule (cron)</Label>
          <Input
            id="conn-cron"
            value={cron}
            onChange={(e) => setCron(e.target.value)}
            disabled={!createJob}
            placeholder="0 */6 * * *"
          />
          <p className="text-xs text-muted-foreground">Used when sync job is created (default every 6 hours).</p>
        </div>
        <label className="flex items-center gap-2 text-sm cursor-pointer pb-2">
          <input
            type="checkbox"
            checked={createJob}
            onChange={(e) => setCreateJob(e.target.checked)}
            className="rounded border-input"
          />
          Create sync job
        </label>
      </div>
      {formError && <p className="text-sm text-destructive">{formError}</p>}
      <Button type="button" onClick={() => createMut.mutate()} disabled={createMut.isPending || !name.trim()}>
        {createMut.isPending ? "Saving…" : "Add connector"}
      </Button>
    </div>
  );
}

function BoolBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${
        ok ? "border-green-600/40 text-green-700 dark:text-green-400" : "border-muted-foreground/40 text-muted-foreground"
      }`}
    >
      {label}: {ok ? "yes" : "no"}
    </span>
  );
}

export default function SettingsPage() {
  const token = getToken();
  const {
    data: platform,
    isLoading: platformLoading,
    isError: platformError,
  } = useQuery({
    queryKey: ["platform-settings"],
    queryFn: () => apiFetch<PlatformSettings>("/api/v1/platform/settings", { token }),
    retry: false,
    enabled: !!token,
  });

  const { data: connectors = [], isLoading: connLoading } = useQuery({
    queryKey: ["connector-health"],
    queryFn: () => apiFetch<ConnectorHealth[]>("/api/v1/connectors/health", { token }),
    enabled: !!token,
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Connectors, authentication, and read-only platform configuration (Phase 3).
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Platform</CardTitle>
          <CardDescription>
            Values come from API environment variables. Edit deployment config and restart the API to change them.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!token && <p className="text-sm text-muted-foreground">Sign in to load platform settings.</p>}
          {token && platformLoading && <p className="text-sm text-muted-foreground">Loading platform settings…</p>}
          {token && platformError && (
            <p className="text-sm text-destructive">
              Could not load platform settings (requires <code className="text-xs">connectors:read</code> permission).
            </p>
          )}
          {platform && (
            <>
              <div className="flex flex-wrap gap-2">
                <BoolBadge ok={!platform.demo_mode} label="Production mode" />
                <BoolBadge ok={platform.cors_enabled} label="CORS" />
                <BoolBadge ok={platform.trusted_proxy} label="Trusted proxy" />
                <BoolBadge ok={platform.log_json} label="JSON logs" />
                <BoolBadge ok={platform.production_refuse_insecure_defaults} label="Refuse insecure defaults" />
              </div>
              <dl className="grid gap-2 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-muted-foreground">API version</dt>
                  <dd className="font-mono">{platform.api_version}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Login rate limit</dt>
                  <dd className="font-mono">{platform.auth_login_rate_limit}</dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-muted-foreground">Report storage</dt>
                  <dd className="font-mono break-all">{platform.report_storage_dir}</dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-muted-foreground">CORS origins</dt>
                  <dd className="font-mono text-xs break-all">
                    {platform.cors_origins.length ? platform.cors_origins.join(", ") : "(none — same-origin only)"}
                  </dd>
                </div>
              </dl>
              <div>
                <p className="text-sm font-medium mb-2">Integrations</p>
                <div className="flex flex-wrap gap-2">
                  <BoolBadge ok={platform.oidc_configured} label="OIDC" />
                  <BoolBadge ok={platform.ldap_configured} label="LDAP" />
                  <BoolBadge ok={platform.smtp_configured} label="SMTP" />
                  <BoolBadge ok={platform.haproxy_ssh_configured} label="HAProxy SSH" />
                  <BoolBadge ok={platform.automation_runner_configured} label="Automation secret" />
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Authentication</CardTitle>
          <CardDescription>
            Local accounts use the login form. OIDC and LDAP are configured on the API server.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            <strong>Local</strong> —{" "}
            <Link href="/login" className="text-primary underline underline-offset-4">
              Sign in
            </Link>{" "}
            with a Nexus user (e.g. break-glass admin).
          </p>
          <p>
            <strong>OIDC</strong> — when enabled, use &quot;Continue with OIDC&quot; on the login page (redirects to your IdP).
          </p>
          <p>
            <strong>LDAP</strong> — when enabled, use &quot;Directory sign-in&quot; on the login page. Users must already exist in Nexus
            (provisioned); LDAP verifies the password.
          </p>
          <p className="text-muted-foreground">
            OIDC callback currently returns tokens for mapping in a full deployment; see API docs at{" "}
            <code className="text-xs">{apiUrl("/docs")}</code>.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Connectors</CardTitle>
            <CardDescription>Inventory sync sources and last health from the control plane.</CardDescription>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link href="/sync-jobs">Sync jobs</Link>
          </Button>
        </CardHeader>
        <CardContent>
          {!token && <p className="text-sm text-muted-foreground">Sign in to view connectors.</p>}
          <AddConnectorForm token={token} />
          {token && connLoading && <p className="text-sm text-muted-foreground">Loading connectors…</p>}
          {token && !connLoading && connectors.length === 0 && (
            <p className="text-sm text-muted-foreground mb-4">No connectors yet. Add one above (requires connectors:write).</p>
          )}
          {token && !connLoading && connectors.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Base URL</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last sync</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {connectors.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium">{c.name}</TableCell>
                    <TableCell>{c.type}</TableCell>
                    <TableCell className="max-w-[200px] truncate font-mono text-xs">{c.base_url ?? "—"}</TableCell>
                    <TableCell>
                      <span
                        className={
                          c.status === "healthy"
                            ? "text-green-700 dark:text-green-400"
                            : c.status === "unhealthy"
                              ? "text-destructive"
                              : "text-muted-foreground"
                        }
                      >
                        {c.status}
                      </span>
                      {c.last_error ? (
                        <span className="block text-xs text-muted-foreground truncate max-w-xs" title={c.last_error}>
                          {c.last_error}
                        </span>
                      ) : null}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-xs">
                      {c.sync_last_run_at ?? "—"}
                      {c.sync_status ? ` (${c.sync_status})` : ""}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
