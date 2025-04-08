export interface LoginRequestData {
  /** 邮箱 */
  email: string
  /** 密码 */
  password: string
}

export interface LoginData {
  access: string
  refresh: string
  user_id: string
  role: string
  name: string
}

export type LoginResponseData = ApiResponseData<LoginData>
