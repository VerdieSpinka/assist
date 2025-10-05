import {
	createContext,
	useContext,
	useEffect,
	useState,
	useCallback,
} from 'react';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import {
	AuthStatus,
	getAuthStatus,
	loginUser,
	registerUser,
	logoutUser, // Sekarang mengimpor fungsi yang benar
	UserInfo,
	RegisterPayload,
	ApiError,
} from '../api/auth';
import { useRefreshModels } from './configs';
import { updateJaazApiKey, clearJaazApiKey } from '../api/config';

interface AuthContextType {
	authStatus: AuthStatus;
	isLoading: boolean;
	login: (username: string, password: string) => Promise<void>;
	register: (payload: RegisterPayload) => Promise<void>;
	logout: () => Promise<void>;
	refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
	const { t } = useTranslation();
	const [authStatus, setAuthStatus] = useState<AuthStatus>({
		is_logged_in: false,
	}); // Diperbarui
	const [isLoading, setIsLoading] = useState(true);
	const refreshModels = useRefreshModels();

	const refreshAuth = useCallback(async () => {
		setIsLoading(true);
		try {
			const status = await getAuthStatus();
			if (status.tokenExpired) {
				toast.error(t('common:auth.authExpiredMessage'));
			}
			setAuthStatus(status);
		} catch (error) {
			console.error('Failed to refresh authentication status:', error);
			setAuthStatus({ is_logged_in: false });
		} finally {
			setIsLoading(false);
		}
	}, [t]);

	useEffect(() => {
		refreshAuth();
	}, [refreshAuth]);

	const handleLoginSuccess = async (userInfo: UserInfo, token: string) => {
		// saveAuthData sekarang dipanggil di dalam loginUser, jadi kita hapus di sini
		setAuthStatus({ is_logged_in: true, user_info: userInfo });
		await updateJaazApiKey(token);
		refreshModels();
		toast.success(t('common:auth.loginSuccessMessage'));
	};

	const login = async (username: string, password: string) => {
		const { access_token, user_info } = await loginUser(username, password);
		// loginUser sudah menangani penyimpanan token
		await handleLoginSuccess(user_info, access_token);
	};

	const register = async (payload: RegisterPayload) => {
		await registerUser(payload);
		// Otomatis login setelah registrasi
		const { access_token, user_info } = await loginUser(
			payload.username,
			payload.password,
		);
		await handleLoginSuccess(user_info, access_token);
	};

	const logout = async () => {
		logoutUser(); // Memanggil fungsi API yang sudah diperbaiki
		setAuthStatus({ is_logged_in: false });
		await clearJaazApiKey();
		refreshModels();
		toast.success(t('common:auth.logoutSuccessMessage'));
	};

	return (
		<AuthContext.Provider
			value={{ authStatus, isLoading, login, register, logout, refreshAuth }}
		>
			{children}
		</AuthContext.Provider>
	);
}

export function useAuth() {
	const context = useContext(AuthContext);
	if (context === undefined) {
		throw new Error('useAuth must be used within an AuthProvider');
	}
	return context;
}