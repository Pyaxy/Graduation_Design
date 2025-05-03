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
  // 最大小组人数
  max_group_size: number
  // 最小小组人数
  min_group_size: number
  // 最大课题选择数
  max_subject_selections: number
}

// 创建或更新课程的请求数据
export interface CreateOrUpdateCourseRequestData {
  id?: string
  name: string
  description: string
  start_date: string
  end_date: string
  max_group_size: number
  min_group_size: number
  max_subject_selections: number
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

// 小组数据
export interface GroupData {
  // 小组 ID
  id: string
  // 小组名称
  name: string
  // 课程
  course: {
    id: string
    name: string
  }
  // 创建者
  creator: {
    user_id: string
    name: string
    role: string
    role_display: string
  }
  // 成员列表
  students: {
    user_id: string
    name: string
    role: string
    role_display: string
  }[]
  // 创建时间
  created_at: string
  // 更新时间
  updated_at: string
  // 提交状态
  submission: {
    is_submitted: boolean
    version_id: string | null
  }
}

// 获取小组列表的响应数据
export interface GetGroupsListResponse {
  data: {
    count: number
    next: string | null
    previous: string | null
    results: GroupData[]
  }
  message: string
}

// 加入小组的请求数据
export interface JoinGroupRequestData {
  group_id: string
}

// 退出小组的请求数据
export interface LeaveGroupRequestData {
  student_user_id: string
}

// 创建小组的请求数据
export interface CreateGroupRequestData {
  course: string
}

// 创建小组的响应数据
export interface CreateGroupResponse {
  data: null
  message: string
}

// 课题数据
export interface SubjectData {
  id: string
  title: string
  description: string
  description_file: string | null
  description_file_url: string | null
  creator: {
    user_id: string
    name: string
    role: string
    role_display: string
  }
  languages: string[]
  status: "PENDING" | "APPROVED" | "REJECTED"
  status_display: string
  is_public: boolean
  public_status: "NOT_APPLIED" | "PENDING" | "APPROVED" | "REJECTED"
  public_status_display: string
  version: number
  created_at: string
  updated_at: string
}

// 获取课题列表的响应数据
export interface SubjectListResponse {
  data: {
    count: number
    next: string | null
    previous: string | null
    results: {
      id: string
      subject: SubjectData
      subject_type: "PRIVATE" | "PUBLIC"
      created_at: string
      updated_at: string
    }[]
  }
  message: string
}

// 添加课题到课程的响应数据
export interface AddSubjectToCourseResponse {
  data: {
    success: {
      count: number
      ids: string[]
    }
    failed: {
      count: number
      details: {
        id: string
        reason: string
      }[]
    }
  }
  message: string
}
