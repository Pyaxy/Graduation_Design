interface RefreshTokenRequestData {
  refresh: string
}

interface RefreshTokenData {
  access: string
  user_id: string
  role: string
  name: string
}

type RefreshTokenResponseData = ApiResponseData<RefreshTokenData>

export type { RefreshTokenRequestData, RefreshTokenResponseData }
