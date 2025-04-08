// 课程数据
export interface SubjectData {
  // 课程 ID
  id: number
  // 课程标题
  title: string
  // 课程描述
  description: string
  // 课程描述文件
  description_file: string
  // 课程描述文件 URL
  description_file_url: string
  // 创建者
  creator: {
    user_id: string
    name: string
    role: string
    role_display: string
  }
  // 最大学生数
  max_students: number
  // 课程状态
  status: "PENDING" | "APPROVED" | "REJECTED"
  // 课程状态显示
  status_display: string
  // 审核者
  reviewer: {
    user_id: string
    name: string
    role_display: string
  } | null
  // 审核备注
  review_comments: string | null
  // 创建时间
  created_at: string
  // 更新时间
  updated_at: string
}

export interface CreateOrUpdateSubjectRequestData {
  // 课程 ID
  id?: number
  // 课程标题
  title: string
  // 课程描述
  description: string
  // 课程描述文件
  description_file?: File
  // 最大学生数
  max_students: number
}

export interface SubjectListResponse {
  data: {
    count: number
    next: string | null
    previous: string | null
    results: SubjectData[]
  }
  message: string
}

export interface SubjectDetailResponse {
  data: SubjectData
  message: string
}
