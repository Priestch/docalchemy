import axios from 'redaxios';

const http = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/',
  timeout: 1000,
});

export {
  http
}