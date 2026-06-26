export type Role = "trader" | "manager";

export interface Session {
  token: string;
  trader_id: string;
  name: string;
  team: string;
  role: Role;
}

export interface Trader {
  id: string;
  name: string;
  team: string;
  role: string;
}

export type AuthState = Session;
