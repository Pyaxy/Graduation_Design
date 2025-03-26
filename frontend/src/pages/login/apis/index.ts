import type * as Auth from "./type"
import { request } from "@/http/axios"

/** 登录接口并返回 Token */
export function loginApi(data: Auth.LoginRequestData) {
  return request<Auth.LoginResponseData>({
    url: "/accounts/login/",
    method: "post",
    data
  })
}
