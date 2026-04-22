import { Component, Input, OnChanges, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration } from 'chart.js';

@Component({
  selector: 'app-charts',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './charts.html',
  styleUrls: ['./charts.css']
})
export class ChartsComponent implements OnChanges {

  constructor(private cdr: ChangeDetectorRef) {}

  @Input() result: any;

  // Chart datasets
  barData: ChartConfiguration<'bar'>['data'] | null = null;
  radarData: ChartConfiguration<'radar'>['data'] | null = null;
  doughnutData: ChartConfiguration<'doughnut'>['data'] | null = null;

  // Chart options (IMPORTANT FIX for label clipping)
  radarOptions: ChartConfiguration<'radar'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    layout: {
      padding: 30   // 🔥 prevents label cutoff
    },
    scales: {
      r: {
        pointLabels: {
          font: {
            size: 12
          },
          padding: 12  // 🔥 fixes "Image Tampering" clipping
        }
      }
    }
  };

  barOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    maintainAspectRatio: false
  };

  doughnutOptions: ChartConfiguration<'doughnut'>['options'] = {
    responsive: true,
    maintainAspectRatio: false
  };

  ngOnChanges(): void {
    if (!this.result) return;

    // -----------------------
    // BAR CHART (Model Compare)
    // -----------------------
    this.barData = {
      labels: ['RF', 'XGB'],
      datasets: [
        {
          data: [
            this.result.rf_probability,
            this.result.xgb_probability
          ],
          label: 'Model Output'
        }
      ]
    };

    // -----------------------
    // RADAR CHART (Tampering Types)
    // -----------------------
    this.radarData = {
      labels: this.result.tampering_types?.map((t: any) => t.type) || [],
      datasets: [
        {
          data: this.result.tampering_types?.map((t: any) => t.confidence) || [],
          label: 'Tampering Signals'
        }
      ]
    };

    // -----------------------
    // DOUGHNUT (Confidence)
    // -----------------------
    this.doughnutData = {
      labels: ['Confidence', 'Remaining'],
      datasets: [
        {
          data: [
            this.result.confidence,
            1 - this.result.confidence
          ]
        }
      ]
    };

    // Ensure UI refresh
    this.cdr.markForCheck();
  }
}