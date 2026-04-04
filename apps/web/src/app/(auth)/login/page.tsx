"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiUrl } from "@/lib/api";

type AuthPublicOptions = { oidc_enabled: boolean; ldap_enabled: boolean };

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<"local" | "ldap">("local");
  const [authOptions, setAuthOptions] = useState<AuthPublicOptions | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(apiUrl("/api/v1/auth/public-options"))
      .then((r) => r.json())
      .then((data: AuthPublicOptions) => {
        if (!cancelled) setAuthOptions(data);
      })
      .catch(() => {
        if (!cancelled) setAuthOptions({ oidc_enabled: false, ldap_enabled: false });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function submitLocal(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(apiUrl("/api/v1/auth/login"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError((data as { detail?: string }).detail || "Login failed");
        return;
      }
      const token = (data as { access_token?: string }).access_token;
      if (token) {
        localStorage.setItem("token", token);
      }
      router.push("/dashboard");
      router.refresh();
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  }

  async function submitLdap(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(apiUrl("/api/v1/auth/ldap/login"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError((data as { detail?: string }).detail || "Login failed");
        return;
      }
      const token = (data as { access_token?: string }).access_token;
      if (token) {
        localStorage.setItem("token", token);
      }
      router.push("/dashboard");
      router.refresh();
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  }

  const oidc = authOptions?.oidc_enabled;
  const ldap = authOptions?.ldap_enabled;

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Cloud Nexus</CardTitle>
          <p className="text-sm text-muted-foreground">Sign in to the control plane</p>
        </CardHeader>
        <CardContent className="space-y-4">
          {oidc && (
            <Button
              type="button"
              variant="secondary"
              className="w-full"
              onClick={() => {
                window.location.href = apiUrl("/api/v1/auth/oidc/login");
              }}
            >
              Continue with OIDC
            </Button>
          )}

          {ldap && (
            <div className="flex rounded-md border p-0.5 text-sm">
              <button
                type="button"
                className={`flex-1 rounded px-2 py-1.5 ${mode === "local" ? "bg-background shadow-sm" : "text-muted-foreground"}`}
                onClick={() => {
                  setMode("local");
                  setError("");
                }}
              >
                Local
              </button>
              <button
                type="button"
                className={`flex-1 rounded px-2 py-1.5 ${mode === "ldap" ? "bg-background shadow-sm" : "text-muted-foreground"}`}
                onClick={() => {
                  setMode("ldap");
                  setError("");
                }}
              >
                Directory
              </button>
            </div>
          )}

          <form onSubmit={mode === "ldap" && ldap ? submitLdap : submitLocal} className="space-y-4">
            <div>
              <Label className="mb-2 block">Username</Label>
              <Input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
              />
            </div>
            <div>
              <Label className="mb-2 block">Password</Label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Signing in…" : mode === "ldap" && ldap ? "Sign in with directory" : "Sign in"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
