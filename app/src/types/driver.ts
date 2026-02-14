export interface PriceHistory {
  price: number
  changed_at: string
  changed_by: string
}

export interface Driver {
  driver_id: string
  first_name: string
  last_name: string
  team_name: string
  nationality: string
  driver_number: number
  price: number
  status: 'active' | 'inactive' | 'reserve'
  price_history: PriceHistory[]
  created_at: string
  updated_at: string
}

export interface DriverCreate {
  first_name: string
  last_name: string
  team_name: string
  nationality: string
  driver_number: number
  price: number
  status?: string
}

export interface DriverUpdate {
  first_name?: string
  last_name?: string
  team_name?: string
  nationality?: string
  driver_number?: number
  price?: number
  status?: string
}
