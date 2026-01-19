"use client";

import { LoginButton } from "@/components/login-button";
import { UploadSection } from "@/components/features/dashboard/UploadSection";
import { TaskList } from "@/components/features/dashboard/TaskList";
import { useAuthStore } from "@/stores/auth-store";

export default function Home() {
  const { user, loading } = useAuthStore();

  return (
    <div className="min-h-screen p-8 pb-20 sm:p-20 font-[family-name:var(--font-geist-sans)] bg-slate-50">
      <main className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-12">
          <div>
            <h1 className="text-4xl font-bold text-slate-900">Drawing Practice Agent</h1>
            <p className="text-lg text-slate-600 mt-2">デッサンをアップロードして、AIコーチングを受けましょう</p>
          </div>
          <LoginButton />
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          </div>
        ) : user ? (
          <div className="space-y-12">
            {/* Upload Section */}
            <section>
              <h2 className="text-xl font-bold text-slate-800 mb-6">新規アップロード</h2>
              <UploadSection />
            </section>

            {/* Task History */}
            <section>
              <h2 className="text-xl font-bold text-slate-800 mb-6">審査履歴</h2>
              <TaskList />
            </section>
          </div>
        ) : (
          <div className="text-center py-16 bg-white rounded-3xl border border-slate-200 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-900 mb-4">ログインしてください</h2>
            <p className="text-slate-500 mb-8">デッサン審査を利用するにはGitHubアカウントでログインしてください</p>
            <LoginButton />
          </div>
        )}
      </main>
    </div>
  );
}
