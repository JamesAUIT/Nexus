"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/hooks/useAuthToken";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type Datastore = { id: number; name: string; type: string | null };
type Volume = { id: number; datastore_id: number; name: string; capacity_bytes: number | null };

export default function StoragePage() {
  const { data: datastores = [] } = useQuery({
    queryKey: ["datastores"],
    queryFn: () => apiFetch<Datastore[]>("/api/v1/storage/datastores", { token: getToken() }),
  });
  const { data: volumes = [] } = useQuery({
    queryKey: ["volumes"],
    queryFn: () => apiFetch<Volume[]>("/api/v1/storage/volumes", { token: getToken() }),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Storage</h1>
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Datastores</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {datastores.map((d) => (
                <TableRow key={d.id}>
                  <TableCell className="font-medium">{d.name}</TableCell>
                  <TableCell>{d.type ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Storage volumes</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Datastore ID</TableHead>
                <TableHead>Capacity (bytes)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {volumes.map((v) => (
                <TableRow key={v.id}>
                  <TableCell className="font-medium">{v.name}</TableCell>
                  <TableCell>{v.datastore_id}</TableCell>
                  <TableCell>{v.capacity_bytes != null ? v.capacity_bytes.toLocaleString() : "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
