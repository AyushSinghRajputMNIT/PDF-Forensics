import { Component, EventEmitter, Output, Input } from '@angular/core';

@Component({
  selector: 'app-header',
  standalone: true,
  templateUrl: './header.html',
  styleUrls: ['./header.css']
})
export class HeaderComponent {

  @Output() fileUploaded = new EventEmitter<File>();

  selectedFile: File | null = null;

  @Input() loading: boolean = false;
  @Input() stage: string = 'IDLE';

  steps: string[] = [
    "Idle",
    "Reading PDF structure",
    "Extracting text & fonts",
    "Running OCR analysis",
    "Analyzing images",
    "Fusing model outputs"
  ];

  get currentStep(): string {
    return this.loading ? "Analyzing document..." : "System ready";
  }

  onFileChange(event: any) {
    const file = event.target.files[0];
    if (file) this.selectedFile = file;
  }

  submit() {
    if (this.selectedFile) {
      this.fileUploaded.emit(this.selectedFile);
    }
  }
}