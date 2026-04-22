import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChangeDetectorRef } from '@angular/core';
// import { HttpClientModule } from '@angular/common/http';

import { ApiService } from './services/api';

// Components
import { HeaderComponent } from './components/header/header';
import { SummaryCardsComponent } from './components/summary-cards/summary-cards';
import { ChartsComponent } from './components/charts/charts';
import { AnalysisComponent } from './components/analysis/analysis';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    // HttpClientModule,
    HeaderComponent,
    SummaryCardsComponent,
    ChartsComponent,
    AnalysisComponent
  ],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class AppComponent {

  result: any = null;
  loading: boolean = false;
  error: string | null = null;

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  // 🔥 Triggered from header component
  onFileUpload(file: File) {
    this.loading = true;
    this.error = null;
    this.result = null;

    this.api.uploadPDF(file).subscribe({
      next: (res: any) => {
        console.log("API RESPONSE:", res);  // keep this

        this.result = res;
        this.loading = false;

        this.cdr.detectChanges();   // 🔥 FORCE UI UPDATE
      },
      error: (err) => {
        console.error(err);
        this.error = 'Failed to analyze PDF';
        this.loading = false;

        this.cdr.detectChanges();   // 🔥 also here
      }
    });
  }
}