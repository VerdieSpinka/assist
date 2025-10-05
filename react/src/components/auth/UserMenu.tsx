import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { useConfigs } from '@/contexts/configs';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { PointsDisplay } from './PointsDisplay';
import { Sparkles } from 'lucide-react'; // Impor ikon

export function UserMenu() {
  const { authStatus, logout } = useAuth();
  const { setShowLoginDialog, setShowProfileSettingsDialog } = useConfigs();
  const { t } = useTranslation();

  const handleLogout = async () => {
    await logout();
  };

  if (authStatus.status === 'logged_in' && authStatus.user_info) {
    const { username, image_url, credits, role } = authStatus.user_info;
    const initials = username ? username.substring(0, 2).toUpperCase() : 'U';

    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="relative p-0 h-auto rounded-full">
            <PointsDisplay>
              <Avatar className="h-8 w-8">
                <AvatarImage src={image_url} alt={username} />
                <AvatarFallback>{initials}</AvatarFallback>
              </Avatar>
            </PointsDisplay>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>{t('common:auth.myAccount')}</DropdownMenuLabel>
          <DropdownMenuItem disabled>{username}</DropdownMenuItem>
          
          {/* Tampilkan sisa kredit untuk user non-admin */}
          {role !== 'admin' && (
            <DropdownMenuItem disabled className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-yellow-500" />
              <span>
                {t('common:auth.creditsLeft', 'Image Credits: {{count}}', { count: credits })}
              </span>
            </DropdownMenuItem>
          )}

          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setShowProfileSettingsDialog(true)}>
            {t('common:auth.profileSettings', 'Profile Settings')}
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleLogout}>
            {t('common:auth.logout')}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    );
  }

  return (
    <Button variant="outline" onClick={() => setShowLoginDialog(true)}>
      {t('common:auth.login')}
    </Button>
  );
}