import { FormEvent, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useAppContext } from '@/contexts/AppContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ShieldCheck, AlertTriangle } from 'lucide-react';

export function LoginPage() {
  const { login } = useAuth();
  const { darkMode } = useAppContext();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login(username, password);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to login';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center px-4 ${darkMode ? 'bg-gray-950' : 'bg-gray-50'}`}>
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-2 text-center">
          <div className="flex items-center justify-center space-x-2 text-primary">
            <ShieldCheck className="h-8 w-8" />
            <CardTitle className="text-2xl">Flood Prediction Console</CardTitle>
          </div>
          <CardDescription>Sign in with your administrator or role-specific credentials.</CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <label className="text-sm font-medium">Username</label>
              <Input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="admin"
                autoComplete="username"
                required
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                required
                disabled={loading}
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>
          <p className="text-xs text-muted-foreground text-center mt-4">
            Default credentials: <span className="font-medium">admin / admin</span> (override via{' '}
            <code className="text-[11px] bg-muted px-1 py-0.5 rounded">VITE_DEFAULT_ADMIN_USERNAME</code> and{' '}
            <code className="text-[11px] bg-muted px-1 py-0.5 rounded">VITE_DEFAULT_ADMIN_PASSWORD</code>).
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
