import {baseURL, http} from "./http.js";

async function getProjects() {
  return http.get('/projects').then((response) => {
    return response.data;
  })
}

function getProjectFileUrl(project_id) {
  return `${baseURL}/projects/${project_id}/file`
}

export {
  getProjects,
  getProjectFileUrl,
}