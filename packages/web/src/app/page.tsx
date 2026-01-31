"use client";

import { useState, useMemo } from 'react';
import { LoginButton } from "@/components/login-button";
import { UserProfileMenu } from "@/components/common/UserProfileMenu";
import { UploadSection } from "@/components/features/dashboard/UploadSection";
import { TaskGrid } from "@/components/features/dashboard/TaskGrid";
import { CalendarFilter } from "@/components/features/dashboard/CalendarFilter";
import { TagSidebar } from "@/components/features/dashboard/TagSidebar";
import { useAuthStore } from "@/stores/auth-store";
import { useTasks } from '@/hooks/useTasks';

export default function Home() {
  const { user, loading } = useAuthStore();
  const { tasks, isLoading, error } = useTasks(user?.uid ?? null);

  const [selectedDate, setSelectedDate] = useState<string>('');
  const [selectedTag, setSelectedTag] = useState<string>('');

  // Tasks filtered ONLY by Tag (for Calendar use)
  const tasksFilteredByTag = useMemo(() => {
    return selectedTag
      ? tasks.filter(t => t.tags?.includes(selectedTag))
      : tasks;
  }, [tasks, selectedTag]);

  // Tasks filtered ONLY by Date (for TagSidebar use)
  const tasksFilteredByDate = useMemo(() => {
    return selectedDate
      ? tasks.filter(t => new Date(t.createdAt).toISOString().split('T')[0] === selectedDate)
      : tasks;
  }, [tasks, selectedDate]);

  // Client-side filtering (Intersection)
  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      let matchesDate = true;
      let matchesTag = true;

      if (selectedDate) {
        const taskDate = new Date(task.createdAt).toISOString().split('T')[0];
        matchesDate = taskDate === selectedDate;
      }

      if (selectedTag) {
        matchesTag = task.tags?.includes(selectedTag) ?? false;
      }

      return matchesDate && matchesTag;
    });
  }, [tasks, selectedDate, selectedTag]);

  return (
    <div className="min-h-screen p-8 pb-20 sm:p-20 font-[family-name:var(--font-geist-sans)] bg-slate-50">
      <main className="max-w-screen-2xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8 max-w-4xl mx-auto xl:max-w-none">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Drawing Practice Agent</h1>
            <p className="text-slate-600 mt-1">デッサンをアップロードして、AIコーチングを受けましょう</p>
          </div>
          {user ? <UserProfileMenu /> : <LoginButton />}
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          </div>
        ) : user ? (
          <div className="flex flex-col xl:flex-row gap-8">
            {/* Left Column (70%) */}
            <div className="flex-1 xl:w-[70%] space-y-8 min-w-0">
              {/* Upload Section */}
              <section>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-slate-800">新規アップロード</h2>
                </div>
                <UploadSection />
              </section>

              {/* Task History */}
              <section>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-slate-800">
                    審査履歴
                    <span className="ml-2 text-sm font-normal text-slate-500">
                      {filteredTasks.length} / {tasks.length}
                    </span>
                  </h2>
                </div>
                <TaskGrid
                  key={`${selectedDate}-${selectedTag}`}
                  tasks={filteredTasks}
                  loading={isLoading}
                  error={error}
                />
              </section>
            </div>

            {/* Right Column (30%) */}
            <div className="xl:w-[30%] space-y-6 flex-shrink-0">
              <div className="sticky top-6 space-y-6">
                <CalendarFilter
                  tasks={tasksFilteredByTag}
                  selectedDate={selectedDate}
                  onSelectDate={setSelectedDate}
                />
                <TagSidebar
                  tasks={tasksFilteredByDate}
                  selectedTag={selectedTag}
                  onSelectTag={setSelectedTag}
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-md mx-auto text-center py-16 bg-white rounded-3xl border border-slate-200 shadow-sm mt-12">
            <h2 className="text-2xl font-bold text-slate-900 mb-4">ログインしてください</h2>
            <p className="text-slate-500 mb-8">デッサン審査を利用するにはGitHubアカウントでログインしてください</p>
            <LoginButton />
          </div>
        )}
      </main>
    </div>
  );
}
