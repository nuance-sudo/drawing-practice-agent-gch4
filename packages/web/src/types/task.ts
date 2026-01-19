export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type ReviewTask = {
  taskId: string;
  userId: string;
  status: TaskStatus;
  imageUrl: string;
  exampleImageUrl?: string;
  feedback?: Feedback;
  score?: number;
  tags?: string[];
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
    lineQuality: CategoryFeedback;
  };
};

export type CategoryFeedback = {
  score: number;
  comments: string[];
};
