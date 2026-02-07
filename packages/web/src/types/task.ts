export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type ReviewTask = {
  taskId: string;
  userId: string;
  status: TaskStatus;
  imageUrl: string;
  annotatedImageUrl?: string;
  exampleImageUrl?: string;
  feedback?: Feedback;
  score?: number;
  tags?: string[];
  rankAtReview?: string;
  rankChanged?: boolean;
  errorMessage?: string;
  createdAt: string;
  updatedAt: string;
};

export type Feedback = {
  overallScore: number;
  strengths: string[];
  improvements: string[];
  details: {
    proportion: CategoryFeedback;
    shading: CategoryFeedback;
    texture: CategoryFeedback;
    lineQuality: CategoryFeedback;
    growth: GrowthFeedback;
  };
};

export type CategoryFeedback = {
  score: number;
  comments: string[];
};

export type GrowthFeedback = {
  score: number | null;
  comparisonSummary: string;
  improvedAreas: string[];
  consistentStrengths: string[];
  ongoingChallenges: string[];
};


export type TaskFilters = {
  startDate?: Date;
  endDate?: Date;
  status?: TaskStatus | 'all';
  tag?: string;
};
