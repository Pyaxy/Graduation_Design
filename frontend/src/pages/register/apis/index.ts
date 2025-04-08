import type * as Auth from "./type"
import { request } from "@/http/axios"

/** 注册接口 */
export function registerApi(data: Auth.RegisterRequestData) {
  return request<Auth.RegisterResponseData>({
    url: "/accounts/register/",
    method: "post",
    data
  })
}
