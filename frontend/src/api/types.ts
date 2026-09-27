export interface User {
  id: number
  email: string
  username: string
  created_at: string
  settings: Record<string, unknown>
}

export interface Token {
  access_token: string
  token_type: string
}

export interface Item {
  id: number
  owner_id: number
  title: string
  description: string
  created_at: string
  updated_at: string
}

export interface ItemList {
  items: Item[]
  total: number
}

export interface ExampleResult {
  result: string
}
