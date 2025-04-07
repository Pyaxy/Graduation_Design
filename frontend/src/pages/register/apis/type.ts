export interface RegisterRequestData {
  /** 邮箱 */
  email: string
  /** 密码 */
  password: string
  /** 学号/工号 */
  user_id: string
  /** 姓名 */
  name: string
  /** 学校 */
  school: string
}

export type RegisterResponseData = ApiResponseData<null>
