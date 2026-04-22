import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-summary-cards',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './summary-cards.html',
  styleUrls: ['./summary-cards.css']
})
export class SummaryCardsComponent {
  @Input() result: any;
}