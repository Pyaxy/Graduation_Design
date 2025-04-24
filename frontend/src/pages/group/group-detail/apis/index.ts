import type { GroupData } from "./type"
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
