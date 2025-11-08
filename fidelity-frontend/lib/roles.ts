import type { Role } from './api-types';

export const ADMIN_ROLES: Role[] = [
  'ADMIN',
  'GLOBAL_ADMIN',
  'CUSTOMER_ADMIN',
  'FRANCHISE_MANAGER',
  'STORE_MANAGER',
];

export function isAdminRole(role: Role | null | undefined) {
  if (!role) {
    return false;
  }
  return ADMIN_ROLES.includes(role);
}

