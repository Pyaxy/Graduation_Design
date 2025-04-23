import type { AddSubjectToCourseResponse, CourseDetailResponse, CourseListResponse, CreateGroupRequestData, CreateGroupResponse, GetGroupsListResponse, GetStudentsResponse, JoinCourseRequestData, LeaveCourseRequestData, LeaveGroupRequestData, SubjectListResponse } from "./type"
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

// 获取小组列表
export function getGroupsList(params?: {
  page: number
  page_size: number
  course_id: string
}) {
  return request<GetGroupsListResponse>({
    url: `/groups/`,
    method: "get",
    params
  })
}

// 加入小组
export function joinGroup(groupId: string) {
  return request<GetGroupsListResponse>({
    url: `/groups/${groupId}/join/`,
    method: "post"
  })
}

// 退出小组
export function leaveGroup(groupId: string, data: LeaveGroupRequestData) {
  return request<GetGroupsListResponse>({
    url: `/groups/${groupId}/leave/`,
    method: "post",
    data
  })
}

// 创建小组
export function createGroup(data: CreateGroupRequestData) {
  return request<CreateGroupResponse>({
    url: "/groups/",
    method: "post",
    data
  })
}

// 添加课题到课程
export function addSubjectToCourse(courseId: string, data: {
  subject_ids: string
  subject_type: "PRIVATE" | "PUBLIC"
}) {
  return request<AddSubjectToCourseResponse>({
    url: `/courses/${courseId}/add_subject/`,
    method: "post",
    data
  })
}

// 获取课程课题列表
export function getCourseSubjectList(courseId: string, params: { page: number, page_size: number }) {
  return request<SubjectListResponse>({
    url: `/courses/${courseId}/subjects_list/`,
    method: "get",
    params
  })
}

// 删除课题
export function deleteSubjectFromCourse(courseId: string, subjectId: string) {
  return request<SubjectListResponse>({
    url: `/courses/${courseId}/delete_subject/`,
    method: "delete",
    data: {
      course_subject_id: subjectId
    }
  })
}