import type { CreateOrUpdateSubjectRequestData, SubjectData, SubjectDetailResponse, SubjectListResponse } from "./type"
import { request } from "@/http/axios"

export function getSubjectList(params: { page?: number, page_size?: number }) {
  return request<SubjectListResponse>({
    url: "/subjects/",
    method: "get",
    params
  })
}

export function getSubjectDetail(id: number) {
  return request<SubjectDetailResponse>({
    url: `/subjects/${id}/`,
    method: "get"
  })
}

export function createSubjectApi(data: FormData) {
  return request<SubjectDetailResponse>({
    url: "/subjects/",
    method: "post",
    data,
    headers: {
      "Content-Type": "multipart/form-data"
    }
  })
}

export function updateSubject(id: number, data: FormData) {
  return request<SubjectDetailResponse>({
    url: `/subjects/${id}/`,
    method: "put",
    data,
    headers: {
      "Content-Type": "multipart/form-data"
    }
  })
}

export function deleteSubject(id: number) {
  return request({
    url: `/subjects/${id}/`,
    method: "delete"
  })
}

export function reviewSubject(id: number, data: { status: string, review_comments: string }) {
  return request<SubjectDetailResponse>({
    url: `/subjects/${id}/review/`,
    method: "post",
    data
  })
}
