// 课程数据
export interface CourseData {
  // 课程 ID
  id: string
  // 课程名称
  name: string
  // 课程描述
  description: string
  // 教师
  teacher: {
    user_id: string
    name: string
    role: string
    role_display: string
  }
  // 学生列表
  students: {
    user_id: string
    name: string
    role: string
    role_display: string
  }[]
  // 课程码
  course_code: string
  // 课程状态
  status: "not_started" | "in_progress" | "completed"
  // 课程状态显示
  status_display: string
  // 创建时间
  created_at: string
  // 更新时间
  updated_at: string
  // 开始日期
  start_date: string
  // 结束日期
  end_date: string
}

// 创建或更新课程的请求数据
export interface CreateOrUpdateCourseRequestData {
  id?: string
  name: string
  description: string
  start_date: string
  end_date: string
}

export interface CourseListResponse {
  data: {
    count: number
    next: string | null
    previous: string | null
    results: CourseData[]
  }
  message: string
}

export interface CourseDetailResponse {
  data: CourseData
  message: string
}

// 加入课程的请求数据
export interface JoinCourseRequestData {
  course_code: string
}

// 退出课程的请求数据
export interface LeaveCourseRequestData {
  student_user_id: string
}

// 获取学生列表的响应数据
export interface GetStudentsResponse {
  data: {
    count: number
    next: string | null
    previous: string | null
    results: {
      user_id: string
      name: string
      role: string
      role_display: string
    }[]
  }
  message: string
}
