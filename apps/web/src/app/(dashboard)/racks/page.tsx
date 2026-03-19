"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type Rack = { id: number; site_id: number; name: string; netbox_rack_id: number | null };

export default function RacksPage() {
  const { data: racks = [], isLoading } = useQuery({
    queryKey: ["racks"],
    queryFn: () => apiFetch<Rack[]>("/api/v1/racks", { token: getToken() }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Racks</h1>
      <Card>
        <CardHeader>
          <CardTitle>Racks</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Site ID</TableHead>
                  <TableHead>NetBox Rack ID</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {racks.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-medium">{r.name}</TableCell>
                    <TableCell>{r.site_id}</TableCell>
                    <TableCell>{r.netbox_rack_id ?? "—"}</TableCell>
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
