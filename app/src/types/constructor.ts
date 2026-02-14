export interface PriceHistory {
  price: number
  changed_at: string
  changed_by: string
}

export interface Constructor {
  constructor_id: string
  name: string
  full_name: string
  nationality: string
  price: number
  status: 'active' | 'inactive'
  price_history: PriceHistory[]
  created_at: string
  updated_at: string
}

export interface ConstructorCreate {
  name: string
  full_name: string
  nationality: string
  price: number
  status?: string
}

export interface ConstructorUpdate {
  name?: string
  full_name?: string
  nationality?: string
  price?: number
  status?: string
}
