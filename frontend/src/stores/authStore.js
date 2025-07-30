import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authAPI } from '../lib/api';

const useAuthStore = create(
  persist(
    (set, get) => ({
      // State
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),
      clearError: () => set({ error: null }),

      // Login action
      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authAPI.login({ email, password });
          const { access_token, refresh_token, user } = response.data;

          // Store tokens in localStorage
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);

          set({
            user,
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });

          return { success: true };
        } catch (error) {
          const errorMessage = error.response?.data?.error || 'Login failed';
          set({ isLoading: false, error: errorMessage });
          return { success: false, error: errorMessage };
        }
      },

      // Register action
      register: async (userData) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authAPI.register(userData);
          const { user } = response.data;

          set({
            isLoading: false,
            error: null,
          });

          return { success: true, user };
        } catch (error) {
          const errorMessage = error.response?.data?.error || 'Registration failed';
          set({ isLoading: false, error: errorMessage });
          return { success: false, error: errorMessage };
        }
      },

      // Logout action
      logout: async () => {
        const { refreshToken } = get();
        
        try {
          if (refreshToken) {
            await authAPI.logout(refreshToken);
          }
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          // Clear tokens from localStorage
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');

          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            error: null,
          });
        }
      },

      // Get current user
      getCurrentUser: async () => {
        set({ isLoading: true });
        try {
          const response = await authAPI.getCurrentUser();
          const user = response.data;

          set({
            user,
            isLoading: false,
          });

          return { success: true, user };
        } catch (error) {
          set({ isLoading: false });
          return { success: false, error: error.response?.data?.error };
        }
      },

      // Change password
      changePassword: async (currentPassword, newPassword) => {
        set({ isLoading: true, error: null });
        try {
          await authAPI.changePassword({
            current_password: currentPassword,
            new_password: newPassword,
          });

          set({ isLoading: false });
          return { success: true };
        } catch (error) {
          const errorMessage = error.response?.data?.error || 'Password change failed';
          set({ isLoading: false, error: errorMessage });
          return { success: false, error: errorMessage };
        }
      },

      // Initialize auth state from localStorage
      initializeAuth: () => {
        const accessToken = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');

        if (accessToken && refreshToken) {
          set({
            accessToken,
            refreshToken,
            isAuthenticated: true,
          });

          // Get current user info
          get().getCurrentUser();
        }
      },

      // Update user profile
      updateProfile: (userData) => {
        set((state) => ({
          user: { ...state.user, ...userData },
        }));
      },

      // Check if user has specific role
      hasRole: (roleName) => {
        const { user } = get();
        return user?.roles?.includes(roleName) || false;
      },

      // Check if user has specific permission
      hasPermission: (permission) => {
        const { user } = get();
        if (!user?.roles) return false;

        // Admin has all permissions
        if (user.roles.includes('admin')) return true;

        // Check specific permissions based on roles
        const rolePermissions = {
          user: ['profile:read', 'profile:update', 'llm:use', 'analytics:view'],
          analyst: ['profile:read', 'profile:update', 'analytics:create', 'analytics:read', 'analytics:update', 'analytics:delete', 'reports:create', 'reports:read', 'reports:update', 'reports:delete'],
          admin: ['*'], // All permissions
        };

        return user.roles.some(role => {
          const permissions = rolePermissions[role] || [];
          return permissions.includes('*') || permissions.includes(permission);
        });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export default useAuthStore;

