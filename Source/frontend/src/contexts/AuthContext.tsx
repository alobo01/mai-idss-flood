import { ReactNode, createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { Role, SystemUser, UserStatus } from '@/types';
import { getRolePermissions } from '@/lib/permissions';

interface UserInput {
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  role: Role;
  department: string;
  phone?: string;
  location?: string;
  status: UserStatus;
  password?: string;
}

interface AuthContextValue {
  users: SystemUser[];
  currentUser: SystemUser | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<SystemUser>;
  logout: () => void;
  addUser: (input: UserInput) => Promise<SystemUser>;
  updateUser: (id: string, updates: Partial<UserInput>) => Promise<SystemUser>;
  deleteUser: (id: string) => Promise<void>;
  resetPassword: (id: string) => Promise<string>;
}

const USERS_STORAGE_KEY = 'flood-prediction-users';
const CURRENT_USER_KEY = 'flood-prediction-current-user';
const DEFAULT_TEMP_PASSWORD = 'ChangeMe123!';

const DEFAULT_ADMIN_USERNAME = import.meta.env.VITE_DEFAULT_ADMIN_USERNAME || 'admin';
const DEFAULT_ADMIN_PASSWORD = import.meta.env.VITE_DEFAULT_ADMIN_PASSWORD || 'admin';

const isBrowser = () => typeof window !== 'undefined';

const generateUserId = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return `USR-${crypto.randomUUID().slice(0, 8).toUpperCase()}`;
  }
  return `USR-${Math.random().toString(36).slice(2, 10).toUpperCase()}`;
};

const generateTempPassword = () => `Reset-${Math.random().toString(36).slice(-6)}`;

const createDefaultAdmin = (): SystemUser => ({
  id: generateUserId(),
  username: DEFAULT_ADMIN_USERNAME,
  password: DEFAULT_ADMIN_PASSWORD,
  email: 'admin@flood.local',
  firstName: 'System',
  lastName: 'Administrator',
  role: 'Administrator',
  department: 'System Administration',
  phone: '+1-555-0101',
  location: 'HQ',
  status: 'active',
  lastLogin: null,
  zones: ['Z1N', 'Z1S', 'Z2', 'Z3', 'Z4', 'ZC'],
  permissions: getRolePermissions('Administrator'),
  createdAt: new Date().toISOString(),
});

const readUsersFromStorage = (): SystemUser[] => {
  if (!isBrowser()) {
    return [];
  }

  const raw = window.localStorage.getItem(USERS_STORAGE_KEY);
  if (!raw) {
    return [];
  }

  try {
    return JSON.parse(raw) as SystemUser[];
  } catch {
    return [];
  }
};

const ensureSeedUsers = (): SystemUser[] => {
  const existing = readUsersFromStorage();
  if (existing.length > 0) {
    return existing;
  }

  const seed = createDefaultAdmin();
  if (isBrowser()) {
    window.localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify([seed]));
  }
  return [seed];
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [users, setUsers] = useState<SystemUser[]>(() => ensureSeedUsers());

  const [currentUser, setCurrentUser] = useState<SystemUser | null>(() => {
    if (!isBrowser()) {
      return null;
    }
    const storedId = window.localStorage.getItem(CURRENT_USER_KEY);
    if (!storedId) {
      return null;
    }
    const existingUsers = ensureSeedUsers();
    return existingUsers.find((user) => user.id === storedId) || null;
  });

  useEffect(() => {
    if (!isBrowser()) {
      return;
    }
    window.localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(users));
  }, [users]);

  useEffect(() => {
    if (!isBrowser()) {
      return;
    }

    if (currentUser) {
      window.localStorage.setItem(CURRENT_USER_KEY, currentUser.id);
    } else {
      window.localStorage.removeItem(CURRENT_USER_KEY);
    }
  }, [currentUser]);

  useEffect(() => {
    if (!currentUser) {
      return;
    }

    const latest = users.find((user) => user.id === currentUser.id);
    if (latest && latest !== currentUser) {
      setCurrentUser(latest);
    }
  }, [users, currentUser]);

  const login = useCallback(
    async (username: string, password: string) => {
      const normalized = username.trim().toLowerCase();
      const user = users.find((u) => u.username.toLowerCase() === normalized);

      if (!user || user.password !== password) {
        throw new Error('Invalid username or password');
      }

      if (user.status !== 'active') {
        throw new Error('This account is not active');
      }

      const now = new Date().toISOString();
      const updatedUser = { ...user, lastLogin: now };
      setUsers((prev) => prev.map((u) => (u.id === user.id ? updatedUser : u)));
      setCurrentUser(updatedUser);
      return updatedUser;
    },
    [users]
  );

  const logout = useCallback(() => {
    setCurrentUser(null);
  }, []);

  const addUser = useCallback(async (input: UserInput) => {
    const username = input.username.trim();
    const email = input.email.trim().toLowerCase();

    if (users.some((user) => user.username.toLowerCase() === username.toLowerCase())) {
      throw new Error('Username already exists');
    }

    if (users.some((user) => user.email.toLowerCase() === email)) {
      throw new Error('Email already exists');
    }

    const now = new Date().toISOString();
    const newUser: SystemUser = {
      id: generateUserId(),
      username,
      password: input.password?.trim() || DEFAULT_TEMP_PASSWORD,
      email,
      firstName: input.firstName.trim(),
      lastName: input.lastName.trim(),
      role: input.role,
      department: input.department.trim(),
      phone: input.phone || '',
      location: input.location || '',
      status: input.status,
      lastLogin: null,
      zones: input.role === 'Administrator' ? ['Z1N', 'Z1S', 'Z2', 'Z3', 'Z4', 'ZC'] : [],
      permissions: getRolePermissions(input.role),
      createdAt: now,
    };

    setUsers((prev) => [...prev, newUser]);
    return newUser;
  }, [users]);

  const updateUser = useCallback(
    async (id: string, updates: Partial<UserInput>) => {
      const existingUser = users.find((user) => user.id === id);
      if (!existingUser) {
        throw new Error('User not found');
      }

      const username = updates.username?.trim();
      if (
        username &&
        username.toLowerCase() !== existingUser.username.toLowerCase() &&
        users.some((user) => user.username.toLowerCase() === username.toLowerCase())
      ) {
        throw new Error('Username already exists');
      }

      const email = updates.email?.trim().toLowerCase();
      if (
        email &&
        email !== existingUser.email.toLowerCase() &&
        users.some((user) => user.email.toLowerCase() === email)
      ) {
        throw new Error('Email already exists');
      }

      const now = new Date().toISOString();
      const updatedUser: SystemUser = {
        ...existingUser,
        ...updates,
        username: username || existingUser.username,
        email: email || existingUser.email,
        role: updates.role || existingUser.role,
        department: updates.department ? updates.department.trim() : existingUser.department,
        phone: updates.phone ?? existingUser.phone,
        location: updates.location ?? existingUser.location,
        status: updates.status || existingUser.status,
        permissions: getRolePermissions(updates.role || existingUser.role),
        updatedAt: now,
      };

      setUsers((prev) => prev.map((user) => (user.id === id ? updatedUser : user)));
      return updatedUser;
    },
    [users]
  );

  const deleteUser = useCallback(
    async (id: string) => {
      const user = users.find((u) => u.id === id);
      if (!user) {
        throw new Error('User not found');
      }

      if (user.role === 'Administrator') {
        const totalAdmins = users.filter((u) => u.role === 'Administrator' && u.id !== id).length;
        if (totalAdmins < 1) {
          throw new Error('Cannot delete the last administrator');
        }
      }

      setUsers((prev) => prev.filter((u) => u.id !== id));

      if (currentUser?.id === id) {
        setCurrentUser(null);
      }
    },
    [users, currentUser]
  );

  const resetPassword = useCallback(
    async (id: string) => {
      const user = users.find((u) => u.id === id);
      if (!user) {
        throw new Error('User not found');
      }

      const tempPassword = generateTempPassword();
      setUsers((prev) =>
        prev.map((existing) =>
          existing.id === id ? { ...existing, password: tempPassword, updatedAt: new Date().toISOString() } : existing
        )
      );

      return tempPassword;
    },
    [users]
  );

  const value: AuthContextValue = useMemo(
    () => ({
      users,
      currentUser,
      isAuthenticated: Boolean(currentUser),
      login,
      logout,
      addUser,
      updateUser,
      deleteUser,
      resetPassword,
    }),
    [users, currentUser, login, logout, addUser, updateUser, deleteUser, resetPassword]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
