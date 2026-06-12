export type Role = "trader" | "manager";

export const ALL_REGIONS = "All regions";

export interface Session {
  token: string;
  role: Role;
  region: string; // home / allotted region
  allowed_regions: string[];
}

export interface AuthState extends Session {
  activeRegion: string; // currently viewed region (manager can switch; trader fixed)
}
