export interface RegisterRequestData {
  /** 邮箱 */
  email: string
  /** 密码 */
  password: string
  /** 确认密码 */
  confirm_password: string
  /** 学号/工号 */
  user_id: string
  /** 姓名 */
  name: string
  /** 学校 */
  school: string
  /** 角色 */
  role: string | null
}

export type RegisterResponseData = ApiResponseData<null>
