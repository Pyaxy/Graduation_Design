import type { CourseDetailResponse, CourseListResponse, GetStudentsResponse, JoinCourseRequestData, LeaveCourseRequestData } from "./type"
import { request } from "@/http/axios"

// 获取课程列表
export function getCourseList(params: {
  page: number
  page_size: number
  search?: string
  status?: string
}) {
  return request<CourseListResponse>({
    url: "/courses/",
    method: "get",
    params
  })
}

// 获取课程详情
export function getCourseDetail(id: string) {
  return request<CourseDetailResponse>({
    url: `/courses/${id}/`,
    method: "get"
  })
}

// 创建课程
export function createCourse(data: FormData) {
  return request<CourseDetailResponse>({
    url: "/courses/",
    method: "post",
    data,
    headers: {
      "Content-Type": "multipart/form-data"
    }
  })
}

// 更新课程
export function updateCourse(id: string, data: FormData) {
  return request<CourseDetailResponse>({
    url: `/courses/${id}/`,
    method: "put",
    data,
    headers: {
      "Content-Type": "multipart/form-data"
    }
  })
}
// 删除课程
export function deleteCourse(id: string) {
  return request<CourseDetailResponse>({
    url: `/courses/${id}/`,
    method: "delete"
  })
}

// 加入课程
export function joinCourse(data: JoinCourseRequestData) {
  return request<CourseDetailResponse>({
    url: "/courses/join/",
    method: "post",
    data
  })
}

// 退出课程
export function leaveCourse(id: string, data?: LeaveCourseRequestData) {
  return request<CourseDetailResponse>({
    url: `/courses/${id}/leave/`,
    method: "post",
    data
  })
}

// 获取学生列表
export function getStudents(id: string, params?: {
  page: number
  page_size: number
  student_search?: string
}) {
  return request<GetStudentsResponse>({
    url: `/courses/${id}/students/`,
    method: "get",
    params
  })
}
