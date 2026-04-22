import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Charts } from './charts';

describe('Charts', () => {
  let component: Charts;
  let fixture: ComponentFixture<Charts>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Charts],
    }).compileComponents();

    fixture = TestBed.createComponent(Charts);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
