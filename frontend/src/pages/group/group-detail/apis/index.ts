import type { GroupCodeVersion, GroupCodeVersionListResponse, GroupCodeVersionResponse, GroupData } from "./type"
import { request } from "@/http/axios"

export function getGroupDetail(groupId: string) {
  return request<GroupData>({
    url: `/groups/${groupId}/`,
    method: "GET"
  })
}

export function selectSubject(groupId: string, subjectId: string) {
  return request({
    url: `/groups/${groupId}/select_subject/`,
    method: "POST",
    data: {
      course_subject_id: subjectId
    }
  })
}

export function unselectSubject(groupId: string) {
  return request({
    url: `/groups/${groupId}/unselect_subject/`,
    method: "DELETE"
  })
}

export function createGroupCodeVersion(groupId: string, data: FormData) {
  return request<GroupCodeVersion>({
    url: `/groups/${groupId}/versions/`,
    method: "POST",
    data,
    headers: {
      "Content-Type": "multipart/form-data"
    }
  })
}

export function listGroupCodeVersions(groupId: string) {
  return request<GroupCodeVersionListResponse>({
    url: `/groups/${groupId}/versions/`,
    method: "GET"
  })
}

export function getGroupCodeVersion(groupId: string, versionId: string) {
  return request<GroupCodeVersionResponse>({
    url: `/groups/${groupId}/versions/${versionId}/`,
    method: "GET"
  })
}

// 提交代码
export function submitCode(groupId: string, data: {
  code_version_id: string
  contributions: string[]
}) {
  return request({
    method: "post",
    url: `/groups/${groupId}/submit_code/`,
    data
  })
}
