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

export interface Dataset {
  id: number
  name: string
  description: string
  created_at: string
  updated_at: string
  data_metadata: {
    num_rows: number
    num_cols: number
    columns: string[]
    missing_values: Record<string, number>
  }
}

export interface DatasetQuota {
  count: number
  limit: number
  remaining: number
}

export interface ExampleResult {
  result: string
}
