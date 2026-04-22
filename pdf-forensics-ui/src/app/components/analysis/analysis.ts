import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-analysis',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './analysis.html',
  styleUrls: ['./analysis.css']
})
export class AnalysisComponent {
  @Input() result: any;
}