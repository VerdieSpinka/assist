import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '../ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { useAuth } from '../../contexts/AuthContext';
import { useConfigs } from '../../contexts/configs';
import { ApiError } from '../../api/auth';

export function LoginDialog() {
  const { login, register } = useAuth();
  const { showLoginDialog: open, setShowLoginDialog } = useConfigs();
  const { t } = useTranslation();
  
  const [view, setView] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const resetForm = () => {
    setUsername('');
    setEmail('');
    setPassword('');
    setError('');
    setIsLoading(false);
  };

  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) {
      resetForm();
      setView('login');
    }
    setShowLoginDialog(isOpen);
  }

  const handleLogin = async () => {
    if (!username || !password) {
      setError(t('common:auth.fillAllFields'));
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      await login(username, password);
      handleOpenChange(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('common:error'));
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleRegister = async () => {
    if (!username || !email || !password) {
      setError(t('common:auth.fillAllFields'));
      return;
    }
    if (password.length < 8) {
      setError(t('common:auth.passwordTooShort'));
      return;
    }
    if (new TextEncoder().encode(password).length > 72) {
      setError(t('common:auth.passwordTooLong'));
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      await register({ username, email, password });
      handleOpenChange(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('common:error'));
    } finally {
      setIsLoading(false);
    }
  };

  // ... (sisa JSX tetap sama)
  // ... (pastikan untuk menerjemahkan string hardcoded seperti "Register" dan "Login")

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        {view === 'login' ? (
          <>
            <DialogHeader>
              <DialogTitle>{t('common:auth.login')}</DialogTitle>
              <DialogDescription>Enter your credentials to access your account.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <Label htmlFor="login-username">Username</Label>
                <Input id="login-username" value={username} onChange={(e) => setUsername(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleLogin()} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="login-password">Password</Label>
                <Input id="login-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleLogin()} />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button onClick={handleLogin} disabled={isLoading} className="w-full">
                {isLoading ? t('common:buttons.loading') : t('common:auth.login')}
              </Button>
              <p className="text-center text-sm text-muted-foreground">
                Don't have an account?{' '}
                <button onClick={() => { setView('register'); resetForm(); }} className="underline font-medium text-primary">
                  Register
                </button>
              </p>
            </div>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>Register</DialogTitle>
              <DialogDescription>Create a new account to get started.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <Label htmlFor="register-username">Username</Label>
                <Input id="register-username" value={username} onChange={(e) => setUsername(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleRegister()} />
              </div>
               <div className="space-y-2">
                <Label htmlFor="register-email">Email</Label>
                <Input id="register-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleRegister()} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="register-password">Password</Label>
                <Input id="register-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleRegister()} />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button onClick={handleRegister} disabled={isLoading} className="w-full">
                {isLoading ? t('common:buttons.loading') : 'Register'}
              </Button>
               <p className="text-center text-sm text-muted-foreground">
                Already have an account?{' '}
                <button onClick={() => { setView('login'); resetForm(); }} className="underline font-medium text-primary">
                  Login
                </button>
              </p>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}