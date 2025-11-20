import axios from 'axios'

const API = axios.create({ baseURL: 'http://localhost:8000' })

// ================================
// FETCH FUNCTIONS
// ================================
export async function fetchCourses() { 
  return API.get('/courses/') 
}

export async function fetchTeachers() { 
  return API.get('/teachers/') 
}

export async function fetchBatches() { 
  return API.get('/batches/') 
}

export async function fetchTeacherTimetable(id) { 
  return API.get(`/teachers/${id}/timetable/`) 
}

export async function fetchBatchTimetable(id) { 
  return API.get(`/batches/${id}/timetable/`) 
}

export async function fetchBatchFreeSlots(id) { 
  return API.get(`/batches/${id}/free-slots/`) 
}

export async function fetchFullTimetable() {
  return API.get("/timetable/full/")
}

// ================================
// CREATE FUNCTIONS
// ================================
export async function createCourse(payload) { 
  return API.post('/courses/', payload) 
}

export async function createTeachers(payload) { 
  return API.post('/teachers/', payload) 
}

export async function createBatches(payload) { 
  return API.post('/batches/', payload) 
}

export async function createRooms(payload) { 
  return API.post('/rooms/', payload) 
}

export async function postGenerate() { 
  return API.post('/generate-timetable/') 
}

export async function postSeed(payload) { 
  return API.post('/admin/seed/', payload) 
}

export async function assignTeachers(courseId, payload) { 
  return API.post(`/courses/${courseId}/assign-teachers/`, payload) 
}

// ================================
// UPDATE FUNCTIONS (NEW)
// ================================
export async function updateCourse(courseId, payload) {
  return API.put(`/courses/${courseId}`, payload)
}

export async function updateTeacher(teacherId, payload) {
  return API.put(`/teachers/${teacherId}`, payload)
}

// ================================
// DELETE FUNCTIONS (NEW)
// ================================
export async function deleteCourse(courseId) {
  return API.delete(`/courses/${courseId}`)
}

export async function deleteTeacher(teacherId) {
  return API.delete(`/teachers/${teacherId}`)
}

// ================================
// DOWNLOAD PDF
// ================================
export async function downloadFullPDF() {
  return API.get("/timetable/full/pdf/", { responseType: "blob" })
}

export default API
