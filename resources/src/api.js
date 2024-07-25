import {http} from "./http.js";

async function getProjects() {
  return http.get('/projects').then((response) => {
    return response.data;
  })
}

export {
  getProjects,
}