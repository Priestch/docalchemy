import axios from 'axios';

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 1000,
});

export {
  http,
}