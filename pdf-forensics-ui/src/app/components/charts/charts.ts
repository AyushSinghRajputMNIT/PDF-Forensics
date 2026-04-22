import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy } from '@angular/core';
import { BaseChartDirective } from 'ng2-charts';

@Component({
  selector: 'app-charts',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './charts.html',
  styleUrls: ['./charts.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ChartsComponent implements OnChanges {

  @Input() result: any;

  barData: any;
  radarData: any;
  doughnutData: any;

  ngOnChanges() {
    if (!this.result) return;

    // Model comparison
    this.barData = {
      labels: ['RF', 'XGB'],
      datasets: [{
        data: [
          this.result.rf_probability,
          this.result.xgb_probability
        ],
        label: 'Model Output'
      }]
    };

    // Tampering types
    this.radarData = {
      labels: this.result.tampering_types.map((t: any) => t.type),
      datasets: [{
        data: this.result.tampering_types.map((t: any) => t.confidence),
        label: 'Tampering Signals'
      }]
    };

    // Confidence
    this.doughnutData = {
      labels: ['Confidence', 'Remaining'],
      datasets: [{
        data: [
          this.result.confidence,
          1 - this.result.confidence
        ]
      }]
    };
  }
}