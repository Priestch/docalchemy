import axios from 'axios';

const baseURL = '/api/v1';

const http = axios.create({
  baseURL,
  timeout: 1000,
});

export {
  http,
  baseURL,
}