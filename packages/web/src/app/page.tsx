import { TaskList } from '@/components/features/dashboard/TaskList';
import { UploadSection } from '@/components/features/dashboard/UploadSection';

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-black text-slate-900 mb-4 tracking-tight">
            デッサンコーチング
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            あなたのデッサンをAIが分析し、具体的な改善点をフィードバックします。
          </p>
        </div>

        <div className="mb-16">
          <UploadSection />
        </div>

        <div>
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-slate-900">
              最近の履歴
            </h2>
          </div>
          <TaskList />
        </div>
      </div>
    </main>
  );
}
