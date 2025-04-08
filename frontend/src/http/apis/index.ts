import type * as Refresh from "./type"
import { request } from "../axios"

export function refreshTokenApi(data: Refresh.RefreshTokenRequestData) {
  return request<Refresh.RefreshTokenResponseData>({
    url: "/accounts/refresh/",
    method: "post",
    data
  })
}
