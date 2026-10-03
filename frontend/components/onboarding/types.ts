import type { Assignment, AvailabilityDay, Course, Profile, Semester } from '@/lib/types';

export interface OnboardingData {
  profile: Profile;
  semester: Semester | null;
  courses: Course[];
  assignments: Assignment[];
  availability: AvailabilityDay[];
}
