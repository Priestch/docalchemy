import {http} from "./http.js";

async function getProjects() {
  return http.get('/projects').then((response) => {
    console.log(response.data);
  })
}

export {
  getProjects,
}