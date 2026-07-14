'use client';

import { useState } from 'react';
import type { AnalyzeRequest } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { X, ArrowRight } from 'lucide-react';

interface StudentFormProps {
  onSubmit: (data: AnalyzeRequest) => Promise<void>;
  isLoading?: boolean;
}

export function StudentForm({ onSubmit, isLoading = false }: StudentFormProps) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<AnalyzeRequest>({
    name: '',
    major: '',
    current_gpa: 3.0,
    target_gpa: 3.5,
    courses: [],
    study_hours_per_week: 20,
    stress_level: 5,
    goals: '',
  });

  const [courseInput, setCourseInput] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const numValue = type === 'number' ? parseFloat(value) : value;

    setFormData(prev => ({
      ...prev,
      [name]: numValue,
    }));
  };

  const handleAddCourse = () => {
    if (courseInput.trim()) {
      setFormData(prev => ({
        ...prev,
        courses: [...prev.courses, courseInput.trim()],
      }));
      setCourseInput('');
    }
  };

  const handleRemoveCourse = (index: number) => {
    setFormData(prev => ({
      ...prev,
      courses: prev.courses.filter((_, i) => i !== index),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(formData);
  };

  const handleNextStep = () => {
    if (step < 3) setStep(step + 1);
  };

  const handlePrevStep = () => {
    if (step > 1) setStep(step - 1);
  };

  return (
    <Card className="w-full p-8 sm:p-10">
      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Step Indicator */}
        <div>
          <div className="mb-6">
            <p className="text-sm font-medium text-primary mb-2">Step {step} of 3</p>
            <h2 className="text-2xl font-bold text-foreground">
              {step === 1 && "Where are you currently?"}
              {step === 2 && "Tell us about your workload"}
              {step === 3 && "What are your goals?"}
            </h2>
          </div>
          <div className="flex gap-2">
            {[1, 2, 3].map(s => (
              <div
                key={s}
                className={`h-1.5 flex-1 rounded-full transition-all ${
                  s <= step ? 'bg-primary' : 'bg-border/30'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Step 1: Basic Info */}
        {step === 1 && (
          <>
            <div>
              <label className="block text-sm font-semibold text-foreground mb-2.5">
                Full Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Enter your name"
                required
                className="w-full rounded-xl border border-input bg-background px-4 py-3 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-foreground mb-2.5">
                Major *
              </label>
              <input
                type="text"
                name="major"
                value={formData.major}
                onChange={handleInputChange}
                placeholder="e.g., Computer Science"
                required
                className="w-full rounded-xl border border-input bg-background px-4 py-3 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-foreground mb-2.5">
                  Current GPA
                </label>
                <input
                  type="number"
                  name="current_gpa"
                  value={formData.current_gpa}
                  onChange={handleInputChange}
                  step="0.1"
                  min="0"
                  max="4"
                  className="w-full rounded-xl border border-input bg-background px-4 py-3 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-foreground mb-2.5">
                  Target GPA
                </label>
                <input
                  type="number"
                  name="target_gpa"
                  value={formData.target_gpa}
                  onChange={handleInputChange}
                  step="0.1"
                  min="0"
                  max="4"
                  className="w-full rounded-xl border border-input bg-background px-4 py-3 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                />
              </div>
            </div>
          </>
        )}

        {/* Step 2: Workload */}
        {step === 2 && (
          <>
            <div>
              <label className="block text-sm font-semibold text-foreground mb-3">
                Current Workload
              </label>
              <div className="space-y-2">
                {['Light', 'Moderate', 'Heavy'].map(workload => (
                  <label key={workload} className="flex items-center gap-3 p-4 rounded-xl border border-input cursor-pointer hover:bg-muted/30 transition-colors">
                    <input
                      type="radio"
                      name="workload"
                      value={workload.toLowerCase()}
                      onChange={() => setFormData(prev => ({
                        ...prev,
                        stress_level: workload === 'Light' ? 3 : workload === 'Moderate' ? 5 : 8
                      }))}
                      checked={(formData.stress_level <= 3 && workload === 'Light') || (formData.stress_level > 3 && formData.stress_level <= 6 && workload === 'Moderate') || (formData.stress_level > 6 && workload === 'Heavy')}
                      className="w-4 h-4 cursor-pointer"
                    />
                    <span className="text-sm font-medium text-foreground">{workload}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-foreground mb-2.5">
                Study Hours Per Week
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  name="study_hours_per_week"
                  min="0"
                  max="60"
                  step="5"
                  value={formData.study_hours_per_week}
                  onChange={handleInputChange}
                  className="flex-1"
                />
                <span className="text-lg font-bold text-primary w-16 text-right">
                  {formData.study_hours_per_week} hrs
                </span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-foreground mb-2.5">
                Courses (Add up to 6)
              </label>
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={courseInput}
                  onChange={e => setCourseInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddCourse())}
                  placeholder="e.g., CS 101 - Intro to Programming"
                  className="flex-1 rounded-xl border border-input bg-background px-4 py-3 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                />
                <Button type="button" onClick={handleAddCourse} variant="outline" className="rounded-lg">
                  Add
                </Button>
              </div>

              {formData.courses.length > 0 && (
                <div className="space-y-2">
                  {formData.courses.map((course, index) => (
                    <div key={index} className="flex items-center justify-between bg-muted/30 px-4 py-2 rounded-lg">
                      <span className="text-sm text-foreground">{course}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveCourse(index)}
                        className="text-foreground/50 hover:text-foreground transition-colors"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}

        {/* Step 3: Goals */}
        {step === 3 && (
          <div>
            <label className="block text-sm font-semibold text-foreground mb-2.5">
              What are your main goals for this recovery plan?
            </label>
            <textarea
              name="goals"
              value={formData.goals}
              onChange={handleInputChange}
              placeholder="e.g., Catch up on missed assignments, improve study habits, balance coursework with wellness..."
              rows={6}
              className="w-full rounded-xl border border-input bg-background px-4 py-3 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all resize-none"
            />
            <p className="text-xs text-foreground/50 mt-2">
              This helps our AI create a personalized recovery plan tailored to your needs.
            </p>
          </div>
        )}

        {/* Navigation */}
        <div className="flex gap-3 pt-4">
          {step > 1 && (
            <Button
              type="button"
              onClick={handlePrevStep}
              variant="outline"
              className="rounded-lg"
            >
              Back
            </Button>
          )}
          <div className="flex-1" />
          {step < 3 ? (
            <Button
              type="button"
              onClick={handleNextStep}
              className="rounded-lg gap-2"
            >
              Continue <ArrowRight className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              type="submit"
              disabled={isLoading}
              className="rounded-lg gap-2"
            >
              {isLoading ? 'Analyzing...' : 'Get My Recovery Plan'}
            </Button>
          )}
        </div>
      </form>
    </Card>
  );
}
