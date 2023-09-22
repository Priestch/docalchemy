import axios from 'redaxios';

const baseURL = '/api';

const http = axios.create({
  baseURL: baseURL,
})

function getDocumentUrl(name) {
  return `${baseURL}/documents/${name}/pdf`;
}

function getDocumentPredictions(name) {
  return http.get(`/documents/${name}/predictions`);
}

/**
 * @param {string} name
 * @param {number} page
 * @returns {Promise<Response<any>>}
 */
function getPagePredictions(name, page) {
  return http.get(`/documents/${name}/pages/${page}/predictions`);
}

export {
  getDocumentUrl,
  getDocumentPredictions,
  getPagePredictions
}