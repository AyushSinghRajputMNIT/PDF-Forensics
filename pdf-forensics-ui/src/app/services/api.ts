import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private API_URL = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  uploadPDF(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post(`${this.API_URL}/predict`, formData);
  }

  exportReport(data: any) {
    return this.http.post('http://127.0.0.1:8000/export-report', data, {
      responseType: 'blob',
    });
  }
}
