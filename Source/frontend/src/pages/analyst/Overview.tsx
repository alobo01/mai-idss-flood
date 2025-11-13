
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function AnalystOverview() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Analytical Map</h1>
      <Card>
        <CardHeader>
          <CardTitle>Multi-layer Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-96 bg-muted rounded-lg flex items-center justify-center">
            <p className="text-muted-foreground">Analytical layers will be implemented here</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}