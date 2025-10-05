import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import { useConfigs } from '@/contexts/configs';
import { ApiError } from '@/api/auth';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { Camera } from 'lucide-react';

export function ProfileSettingsDialog() {
  const { t } = useTranslation();
  const { authStatus, updateProfile, changePassword, updateProfilePicture } = useAuth();
  const { showProfileSettingsDialog, setShowProfileSettingsDialog } = useConfigs();
  
  const user = authStatus.user_info;

  // State for forms
  const [username, setUsername] = useState(user?.username || '');
  const [email, setEmail] = useState(user?.email || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  
  const [isProfileLoading, setIsProfileLoading] = useState(false);
  const [isPasswordLoading, setIsPasswordLoading] = useState(false);
  const [isAvatarLoading, setIsAvatarLoading] = useState(false);

  const [profileError, setProfileError] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (user) {
      setUsername(user.username);
      setEmail(user.email);
    }
  }, [user]);

  const handleProfileUpdate = async () => {
    if (!username.trim()) {
        setProfileError("Username cannot be empty.");
        return;
    }
    setIsProfileLoading(true);
    setProfileError('');
    try {
        await updateProfile({ username, email });
        toast.success("Profile updated successfully!");
        setShowProfileSettingsDialog(false);
    } catch (err) {
        setProfileError(err instanceof ApiError ? err.message : "An unknown error occurred.");
    } finally {
        setIsProfileLoading(false);
    }
  };

  const handlePasswordChange = async () => {
    if (!currentPassword || !newPassword) {
        setPasswordError("All password fields are required.");
        return;
    }
    setIsPasswordLoading(true);
    setPasswordError('');
    try {
        await changePassword({ current_password: currentPassword, new_password: newPassword });
        toast.success("Password changed successfully!");
        setCurrentPassword('');
        setNewPassword('');
        setShowProfileSettingsDialog(false);
    } catch (err) {
        setPasswordError(err instanceof ApiError ? err.message : "An unknown error occurred.");
    } finally {
        setIsPasswordLoading(false);
    }
  };

  const handleAvatarChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsAvatarLoading(true);
    try {
        await updateProfilePicture(file);
        toast.success("Profile picture updated!");
    } catch (err) {
        toast.error("Failed to update profile picture.", {
            description: err instanceof ApiError ? err.message : "An unknown error occurred."
        });
    } finally {
        setIsAvatarLoading(false);
    }
  };

  if (!user) return null;

  return (
    <Dialog open={showProfileSettingsDialog} onOpenChange={setShowProfileSettingsDialog}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Profile Settings</DialogTitle>
          <DialogDescription>Manage your account settings.</DialogDescription>
        </DialogHeader>
        
        <div className="py-4 space-y-6">
            {/* Avatar Section */}
            <div className="flex justify-center">
                <div className="relative group">
                    <Avatar className="w-24 h-24 text-4xl">
                        <AvatarImage src={user.image_url} alt={user.username} />
                        <AvatarFallback>{user.username.substring(0, 2).toUpperCase()}</AvatarFallback>
                    </Avatar>
                    <button 
                        className="absolute inset-0 bg-black/50 flex items-center justify-center rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isAvatarLoading}
                    >
                        {isAvatarLoading ? (
                           <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                           <Camera className="w-8 h-8 text-white" />
                        )}
                    </button>
                    <input 
                        type="file" 
                        ref={fileInputRef}
                        onChange={handleAvatarChange}
                        accept="image/png, image/jpeg, image/webp"
                        className="hidden"
                    />
                </div>
            </div>

            {/* Profile Info Form */}
            <div className="space-y-4">
                 <h3 className="font-semibold">Profile Information</h3>
                 <div className="space-y-2">
                    <Label htmlFor="username">Username</Label>
                    <Input id="username" value={username} onChange={(e) => setUsername(e.target.value)} />
                 </div>
                 <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} disabled />
                 </div>
                 {profileError && <p className="text-sm text-destructive">{profileError}</p>}
                 <Button onClick={handleProfileUpdate} disabled={isProfileLoading} className="w-full">
                    {isProfileLoading ? "Saving..." : "Save Profile Changes"}
                 </Button>
            </div>
            
            {/* Password Change Form */}
            <div className="space-y-4 pt-4 border-t">
                 <h3 className="font-semibold">Change Password</h3>
                 <div className="space-y-2">
                    <Label htmlFor="current-password">Current Password</Label>
                    <Input id="current-password" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
                 </div>
                 <div className="space-y-2">
                    <Label htmlFor="new-password">New Password</Label>
                    <Input id="new-password" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
                 </div>
                 {passwordError && <p className="text-sm text-destructive">{passwordError}</p>}
                 <Button onClick={handlePasswordChange} disabled={isPasswordLoading} className="w-full">
                    {isPasswordLoading ? "Changing..." : "Change Password"}
                 </Button>
            </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}```

#### **5. Integrasikan Dialog Baru dan Perbarui `UserMenu`**

Terakhir, kita perlu merender dialog baru di `App.tsx` dan menambahkan pemicu di `UserMenu.tsx`.

**File:** `assist-main/react/src/App.tsx`

**Kode yang Diperbarui:**
```typescript
// ... (imports)
import SettingsDialog from '@/components/settings/dialog'
import { LoginDialog } from '@/components/auth/LoginDialog'
import { ProfileSettingsDialog } from '@/components/auth/ProfileSettingsDialog' // Import baru
// ... (rest of the file)
function App() {
  const { theme } = useTheme()

  return (
    <ThemeProvider defaultTheme={theme} storageKey="vite-ui-theme">
      <PersistQueryClientProvider
        client={queryClient}
        persistOptions={{ persister }}
      >
        <AuthProvider>
          <ConfigsProvider>
            <div className="app-container">
              <RouterProvider router={router} />

              {/* ... (dialog yang ada) */}
              
              <LoginDialog />

              {/* Dialog Pengaturan Profil Baru */}
              <ProfileSettingsDialog />
            </div>
          </ConfigsProvider>
        </AuthProvider>
      </PersistQueryClientProvider>
      <Toaster position="bottom-center" richColors />
    </ThemeProvider>
  )
}

export default App