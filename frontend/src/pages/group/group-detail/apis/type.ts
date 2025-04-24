export interface GroupData {
  id: string
  name: string
  course: string
  students: Array<{
    user_id: string
    name: string
    role: string
    role_display: string
  }>
  creator: {
    user_id: string
    name: string
    role: string
    role_display: string
  }
  created_at: string
  updated_at: string
  max_students: number
  min_students: number
  group_subjects: Array<{
    id: string
    group: string
    course_subject: {
      id: string
      subject: {
        id: number
        creator: {
          user_id: string
          name: string
          role: string
          role_display: string
        }
        description_file_url: string | null
        title: string
        description: string
        description_file: string | null
        languages: string[]
        created_at: string
        version: number
        original_subject: number
      }
      subject_type: string
      created_at: string
      updated_at: string
    }
    created_at: string
    updated_at: string
  }>
}
