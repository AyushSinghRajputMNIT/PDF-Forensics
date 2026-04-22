import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SummaryCards } from './summary-cards';

describe('SummaryCards', () => {
  let component: SummaryCards;
  let fixture: ComponentFixture<SummaryCards>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SummaryCards],
    }).compileComponents();

    fixture = TestBed.createComponent(SummaryCards);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
