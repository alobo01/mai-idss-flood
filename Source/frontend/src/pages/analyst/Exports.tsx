
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function AnalystExports() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Export Tools</h1>
      <Card>
        <CardHeader>
          <CardTitle>Data & Image Exports</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-96 bg-muted rounded-lg flex items-center justify-center">
            <p className="text-muted-foreground">Export functionality will be implemented here</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}